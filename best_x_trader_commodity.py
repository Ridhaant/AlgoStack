"""
best_x_trader_commodity.py — Commodity Best-X Paper Trader
===============================================================
Runs a paper-trading simulation for MCX commodities (GOLD/SILVER/CRUDE/
NATURALGAS/COPPER) using the globally best X multiplier produced by
`x.py`.

Outputs:
  - trade_logs/commodity_bestx_trade_events_YYYYMMDD.jsonl

This is intentionally separate from `commodity_engine.py` logs so the
dashboard /cbestx page reflects paper-trades only.
"""

from __future__ import annotations

import json
import logging
import os
import time
import glob
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
import pytz

from config import cfg
from broker.executor import build_broker
from risk_controls import TradeRiskController

log = logging.getLogger("best_x_trader_commodity")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BestX-COMM] %(levelname)s — %(message)s",
)

IST = pytz.timezone("Asia/Kolkata")

LEVELS_DIR = "levels"
LIVE_PRICES_JSON = os.path.join(LEVELS_DIR, "live_prices.json")
OPT_RESULTS_DIR = "x_optimizer_results"
TRADE_DIR = "trade_logs"

BROKERAGE_FLAT_INR = 20.0  # matches commodity_engine + existing trade logs

SYMBOLS = ["GOLD", "SILVER", "CRUDE", "NATURALGAS", "COPPER"]


def _now_ist() -> datetime:
    return datetime.now(IST)


def _ts_str(now: datetime) -> str:
    # Mirror existing engines' literal suffix.
    return now.strftime("%Y-%m-%d %H:%M:%S IST+0530")


def _json_append(path: str, event: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _usdt_to_inr() -> float:
    try:
        v = float(getattr(cfg, "USDT_TO_INR", 0.0) or 0.0)
        return v if v > 0 else 84.0
    except Exception:
        return 84.0


def _load_best_x_global() -> float:
    """
    Read globally best X multiplier from:
      - xopt_live_commodity_YYYYMMDD.csv (preferred)
      - xopt_ranked_commodity_YYYYMMDD.csv (fallback)
    """
    ds = _now_ist().strftime("%Y%m%d")

    def _pick(df: pd.DataFrame) -> Optional[float]:
        if df is None or df.empty or "x_value" not in df.columns:
            return None
        d = df.copy()
        d["x_value"] = pd.to_numeric(d["x_value"], errors="coerce")
        d = d.dropna(subset=["x_value"])
        if d.empty:
            return None
        if "score" in d.columns:
            d["score"] = pd.to_numeric(d["score"], errors="coerce").fillna(-1e18)
            d = d.sort_values("score", ascending=False)
        elif "total_pnl" in d.columns:
            d["total_pnl"] = pd.to_numeric(d["total_pnl"], errors="coerce").fillna(-1e18)
            d = d.sort_values("total_pnl", ascending=False)
        x = float(d.iloc[0]["x_value"])
        # Best-X guardrails: stay in realistic multiplier bands.
        if 0.0001 <= x <= 0.05:
            return x
        return None

    # Prefer today's live output, then newest historical live, then ranked.
    candidates = []
    candidates.append(os.path.join(OPT_RESULTS_DIR, f"xopt_live_commodity_{ds}.csv"))
    candidates += sorted(
        glob.glob(os.path.join(OPT_RESULTS_DIR, "xopt_live_commodity_*.csv")),
        key=os.path.getmtime,
        reverse=True,
    )
    candidates.append(os.path.join(OPT_RESULTS_DIR, f"xopt_ranked_commodity_{ds}.csv"))
    candidates += sorted(
        glob.glob(os.path.join(OPT_RESULTS_DIR, "xopt_ranked_commodity_*.csv")),
        key=os.path.getmtime,
        reverse=True,
    )
    seen = set()
    for p in candidates:
        if not p or p in seen or not os.path.exists(p):
            continue
        seen.add(p)
        try:
            x = _pick(pd.read_csv(p))
            if x is not None:
                return x
        except Exception:
            continue

    # Fallback: average configured commodity multipliers (stable default).
    xs = list(getattr(cfg, "COMM_X", {}).values() or [])
    if xs:
        return float(sum(xs) / len(xs))
    return 0.008


def _load_commodity_prev_closes(ds: str) -> Dict[str, float]:
    """
    Read anchor/prev_close from:
      - levels/commodity_initial_levels_YYYYMMDD.json
      - levels/commodity_initial_levels_latest.json (fallback)
    """
    paths = [
        os.path.join(LEVELS_DIR, f"commodity_initial_levels_{ds}.json"),
        os.path.join(LEVELS_DIR, "commodity_initial_levels_latest.json"),
    ]
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                j = json.load(f) or {}
            lv = j.get("levels", {}) or {}
            out: Dict[str, float] = {}
            for s in SYMBOLS:
                if s in lv and isinstance(lv[s], dict):
                    pc = lv[s].get("prev_close")
                    if pc is not None:
                        out[s] = float(pc)
            if out:
                return out
        except Exception:
            pass
    return {}


@dataclass
class Position:
    side: str  # BUY / SELL
    entry_px: float
    qty: float
    entry_x_mult: float  # x_mult before any re-anchor on exit
    # Snapshot of levels at entry (engine-like behavior)
    buy_above: float
    sell_below: float
    buy_sl: float
    sell_sl: float
    step: float  # half-width constant in price units
    t_targets: list
    st_targets: list
    retreat_peak: bool = False


class BestXCommodityTrader:
    def __init__(self) -> None:
        self._stop = False
        self._lock = None  # single-threaded; left for future safety

        self._best_x: float = 0.0
        self._best_x_age_s: float = 9999.0

        self._state_day: str = ""
        self._eod_done: bool = False

        # per-symbol: current anchor and constant step until exit re-anchors
        self._anchors: Dict[str, float] = {}  # prev_close (price units, USDT)
        self._step: Dict[str, float] = {}     # half-width constant in price units
        self._exited: Dict[str, bool] = {s: False for s in SYMBOLS}
        self._pos: Dict[str, Optional[Position]] = {s: None for s in SYMBOLS}

        self._out_path: str = ""
        self._broker = build_broker()
        self._risk = TradeRiskController()

    def _comm_qty(self, price_usdt: float) -> float:
        """Dynamic size (~₹1L notional) to reduce brokerage-dominated exits."""
        try:
            p = float(price_usdt)
        except Exception:
            return 0.0
        if p <= 0:
            return 0.0
        fx = _usdt_to_inr()
        if fx <= 0:
            return 0.0
        capital_usdt = 100_000.0 / float(fx)
        q = int(capital_usdt // p)
        return float(max(1, q))

    def _build_initial_state(self) -> None:
        ds = self._state_day
        pcs = _load_commodity_prev_closes(ds)
        if not pcs:
            log.warning("No commodity prev_closes loaded for %s — waiting", ds)
            return

        self._anchors = {}
        self._step = {}
        for s in SYMBOLS:
            pc = pcs.get(s, 0.0)
            if pc and pc > 0:
                self._anchors[s] = float(pc)
                self._step[s] = float(pc) * float(self._best_x)
                self._exited[s] = False
                self._pos[s] = None

        log.info(
            "Rebuilt commodity states: best_x=%.6f (%d/%d symbols)",
            self._best_x,
            sum(1 for s in SYMBOLS if self._pos.get(s) is None and self._anchors.get(s)),
            len(SYMBOLS),
        )

    def _reanchor_symbol(self, sym: str, new_anchor: float) -> None:
        """
        Engine-like L re-anchor:
          - keep step constant (x_override = step)
          - recompute levels around the new anchor
        """
        if new_anchor <= 0:
            return
        self._anchors[sym] = float(new_anchor)
        self._exited[sym] = False
        self._pos[sym] = None

    def _entry_levels(self, sym: str) -> Optional[Position]:
        anchor = self._anchors.get(sym, 0.0)
        step = self._step.get(sym, 0.0)
        if anchor <= 0 or step <= 0:
            return None

        buy_above = anchor + step
        sell_below = anchor - step
        buy_sl = anchor
        sell_sl = anchor
        x_mult_current = step / anchor if anchor else 0.0

        # Targets / SL snapshot at entry.
        t_targets = [buy_above + step * i for i in range(1, 6)]
        st_targets = [sell_below - step * i for i in range(1, 6)]

        return Position(
            side="BUY",
            entry_px=0.0,
            qty=1.0,
            entry_x_mult=x_mult_current,
            buy_above=buy_above,
            sell_below=sell_below,
            buy_sl=buy_sl,
            sell_sl=sell_sl,
            step=step,
            t_targets=t_targets,
            st_targets=st_targets,
            retreat_peak=False,
        )

    def _open_trade(self, sym: str, side: str, price: float, now: datetime) -> None:
        if not self._risk.can_enter(sym, now):
            return
        p = self._entry_levels(sym)
        if not p:
            return
        p.side = side
        p.entry_px = float(price)
        p.qty = self._comm_qty(price)
        if p.qty <= 0:
            return
        p.entry_x_mult = p.step / (p.buy_sl if p.buy_sl else 1.0) if side == "BUY" else p.step / (p.sell_sl if p.sell_sl else 1.0)
        # Reset retreat gate
        p.retreat_peak = False
        self._pos[sym] = p

        # ENTRY: only reason/entry fields; net/gross remain null until exit.
        self._append_event(
            {
                "ts": _ts_str(now),
                "symbol": sym,
                "side": side,
                "entry_px": float(price),
                "exit_px": None,
                "qty": p.qty,
                "gross_pnl": None,
                "net_pnl": None,
                "reason": "ENTRY",
                "x_val": float(p.entry_x_mult),
                "asset_class": "commodity",
            }
        )
        try:
            o = self._broker.place_entry(asset_class="commodity", symbol=sym, side=side, qty=p.qty, price_hint=price)
            self._append_event(
                {
                    "ts": _ts_str(now),
                    "symbol": sym,
                    "side": side,
                    "entry_px": float(price),
                    "exit_px": None,
                    "qty": p.qty,
                    "gross_pnl": None,
                    "net_pnl": None,
                    "reason": "BROKER_ENTRY_ACK",
                    "x_val": float(p.entry_x_mult),
                    "asset_class": "commodity",
                    "broker_backend": o.backend,
                    "broker_order_id": o.order_id,
                }
            )
        except Exception:
            pass

    def _append_event(self, event: dict) -> None:
        if not self._out_path:
            return
        _json_append(self._out_path, event)

    def _exit_trade(
        self,
        sym: str,
        side: str,
        pos: Position,
        exit_px: float,
        reason: str,
        now: datetime,
    ) -> None:
        anchor_before = self._anchors.get(sym, 0.0)
        step = pos.step
        qty = pos.qty
        entry_px = pos.entry_px

        usdt_to_inr = _usdt_to_inr()

        # Gross P&L in USDT (then INR), matched to commodity_engine formulas.
        if reason == "RETREAT":
            gross_usdt = step * 0.25 * qty
        else:
            if side == "BUY":
                gross_usdt = (exit_px - entry_px) * qty
            else:
                gross_usdt = (entry_px - exit_px) * qty

        gross_inr = gross_usdt * usdt_to_inr
        net_inr = gross_inr - BROKERAGE_FLAT_INR
        self._risk.register_exit(sym, float(net_inr), now)

        # x_val logged as x_mult BEFORE re-anchor (engine behavior).
        x_mult_before = (step / anchor_before) if anchor_before and anchor_before > 0 else pos.entry_x_mult

        self._append_event(
            {
                "ts": _ts_str(now),
                "symbol": sym,
                "side": side,
                "entry_px": float(entry_px),
                "exit_px": float(exit_px),
                "qty": qty,
                "gross_pnl": round(gross_inr, 2),
                "net_pnl": round(net_inr, 2),
                "reason": reason,
                "x_val": float(x_mult_before),
                "asset_class": "commodity",
                "brokerage": BROKERAGE_FLAT_INR,
            }
        )
        try:
            o = self._broker.place_exit(asset_class="commodity", symbol=sym, side=side, qty=qty, price_hint=exit_px, reason=reason)
            self._append_event(
                {
                    "ts": _ts_str(now),
                    "symbol": sym,
                    "side": side,
                    "entry_px": float(entry_px),
                    "exit_px": float(exit_px),
                    "qty": qty,
                    "gross_pnl": None,
                    "net_pnl": None,
                    "reason": "BROKER_EXIT_ACK",
                    "x_val": float(x_mult_before),
                    "asset_class": "commodity",
                    "broker_backend": o.backend,
                    "broker_exit_order_id": o.order_id,
                }
            )
        except Exception:
            pass

        # Post-exit state updates:
        if reason.startswith("T") or reason.startswith("ST"):
            # Target exits: re-anchor at exit_px and allow re-entry.
            self._reanchor_symbol(sym, float(exit_px))
        elif reason == "SL_HIT":
            # SL_HIT: re-anchor to the stop-loss anchor (buy_sl/sell_sl == anchor_before).
            self._reanchor_symbol(sym, float(anchor_before))
        elif reason.startswith("EOD"):
            # EOD square-off: lock until next rebuild/day rollover.
            self._exited[sym] = True
            self._pos[sym] = None
        elif reason == "RETREAT":
            # Retreat exits: lock until next rebuild (engine sets exited=True).
            self._exited[sym] = True
            self._pos[sym] = None

    def _maybe_tick(self, now: datetime) -> None:
        """
        Process one polling tick:
          - load live commodity prices
          - open entries when thresholds breach
          - close positions on targets / SL / retreat / EOD
        """
        # Load live prices
        try:
            with open(LIVE_PRICES_JSON, encoding="utf-8") as f:
                j = json.load(f) or {}
            prices = j.get("commodity_prices") or {}
        except Exception:
            prices = {}

        if not prices:
            return

        # EOD close (MCX session ends): mirror commodity_engine's early 23:xx behavior.
        if now.hour == 23 and not self._eod_done:
            for sym in SYMBOLS:
                pos = self._pos.get(sym)
                if not pos:
                    continue
                px = float(prices.get(sym, pos.entry_px) or 0.0)
                if px <= 0:
                    continue
                self._exit_trade(sym, pos.side, pos, px, "EOD_2330", now)
                self._exited[sym] = True
            self._eod_done = True
            return

        t_min = now.hour * 60 + now.minute
        # Match engine's entry blackout window (entries blocked roughly 09:00–09:35).
        entry_allowed = (t_min >= 9 * 60 + 36) and (t_min <= 23 * 60)

        for sym in SYMBOLS:
            px = prices.get(sym)
            if px is None:
                continue
            price = float(px)
            if price <= 0:
                continue

            pos = self._pos.get(sym)
            anchor = self._anchors.get(sym, 0.0)
            step = self._step.get(sym, 0.0)
            if not pos and (anchor <= 0 or step <= 0):
                continue

            if pos:
                side = pos.side
                # BUY side exits
                if side == "BUY":
                    # Targets T1-T5
                    for i, tgt in enumerate(pos.t_targets, 1):
                        if tgt > pos.entry_px and price >= tgt:
                            self._exit_trade(sym, side, pos, float(tgt), f"T{i}_HIT", now)
                            break
                    else:
                        # SL_HIT: buy_sl == anchor_before
                        if price <= pos.buy_sl and pos.buy_sl > 0:
                            self._exit_trade(sym, side, pos, price, "SL_HIT", now)
                        else:
                            # Retreat gates
                            t_peak = pos.buy_above + 0.65 * step
                            t_exit = pos.buy_above + 0.25 * step
                            if (not pos.retreat_peak) and price >= t_peak:
                                pos.retreat_peak = True
                            if pos.retreat_peak and price <= t_exit:
                                # Engine uses theoretical gross = step*0.25*qty.
                                self._exit_trade(sym, side, pos, price, "RETREAT", now)

                # SELL side exits
                else:
                    for i, tgt in enumerate(pos.st_targets, 1):
                        if tgt < pos.entry_px and price <= tgt:
                            self._exit_trade(sym, side, pos, float(tgt), f"ST{i}_HIT", now)
                            break
                    else:
                        if price >= pos.sell_sl and pos.sell_sl > 0:
                            self._exit_trade(sym, side, pos, price, "SL_HIT", now)
                        else:
                            t_peak = pos.sell_below - 0.65 * step
                            t_exit = pos.sell_below - 0.25 * step
                            if (not pos.retreat_peak) and price <= t_peak:
                                pos.retreat_peak = True
                            if pos.retreat_peak and price >= t_exit:
                                self._exit_trade(sym, side, pos, price, "RETREAT", now)

            else:
                # Flat symbol — open new entries only if not locked by retreat.
                if self._exited.get(sym, False):
                    continue
                if not entry_allowed:
                    continue

                # Compute entry thresholds from current anchor/step.
                buy_above = anchor + step
                sell_below = anchor - step

                if price >= buy_above:
                    self._open_trade(sym, "BUY", price, now)
                elif price <= sell_below:
                    self._open_trade(sym, "SELL", price, now)

    def run_forever(self) -> None:
        os.makedirs(TRADE_DIR, exist_ok=True)
        self._state_day = _now_ist().strftime("%Y%m%d")
        self._out_path = os.path.join(TRADE_DIR, f"commodity_bestx_trade_events_{self._state_day}.jsonl")

        last_x_refresh = 0.0
        last_state_build = 0.0
        rebuild_threshold = 0.00005

        # Initial best-x load
        self._best_x = _load_best_x_global()
        last_x_refresh = time.monotonic()
        last_state_build = time.monotonic()
        self._build_initial_state()

        log.info("Commodity BestX paper trader running: best_x=%.6f", self._best_x)
        log.info("Commodity risk controls active: %s", self._risk.snapshot(_now_ist()))

        eod_checked_day = False

        while True:
            now = _now_ist()
            ds = now.strftime("%Y%m%d")
            if ds != self._state_day:
                # Day rollover: rebuild from scratch and switch output file.
                self._state_day = ds
                self._eod_done = False
                self._out_path = os.path.join(TRADE_DIR, f"commodity_bestx_trade_events_{ds}.jsonl")
                self._best_x = _load_best_x_global()
                self._build_initial_state()
                log.info("New day rebuild: best_x=%.6f", self._best_x)

            # Reload best X every ~30s
            if time.monotonic() - last_x_refresh > 30:
                new_x = _load_best_x_global()
                if abs(float(new_x) - float(self._best_x)) > rebuild_threshold:
                    self._best_x = float(new_x)
                    self._build_initial_state()
                last_x_refresh = time.monotonic()

            if not self._eod_done:
                self._maybe_tick(now)

            time.sleep(1.5)


def main() -> None:
    try:
        BestXCommodityTrader().run_forever()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()

