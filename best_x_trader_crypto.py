"""
best_x_trader_crypto.py — Crypto Best-X Paper Trader
======================================================
Runs a paper-trading simulation for crypto (BTC/ETH/BNB/SOL/ADA)
using the globally best X multiplier produced by `x.py`.

Outputs:
  - trade_logs/crypto_bestx_trade_events_YYYYMMDD.jsonl

This file is separate from `crypto_engine.py` logs so the unified
dashboard's /crbestx page shows paper trades only.
"""

from __future__ import annotations

import json
import logging
import os
import time
import glob
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd
import pytz

from config import cfg
from broker.executor import build_broker
from risk_controls import TradeRiskController

log = logging.getLogger("best_x_trader_crypto")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BestX-CRYPTO] %(levelname)s — %(message)s",
)

IST = pytz.timezone("Asia/Kolkata")

LEVELS_DIR = "levels"
LIVE_PRICES_JSON = os.path.join(LEVELS_DIR, "live_prices.json")
OPT_RESULTS_DIR = "x_optimizer_results"
TRADE_DIR = "trade_logs"

BROKERAGE_FLAT_INR = 20.0  # matches crypto_engine trade logs
DEFAULT_USDT_TO_INR = 84.0

REANCHOR_HOURS = int(os.getenv("CRYPTO_REANCHOR_HOURS", "2"))

SYMBOLS = ["BTC", "ETH", "BNB", "SOL", "ADA"]


def _now_ist() -> datetime:
    return datetime.now(IST)


def _ts_str(now: datetime) -> str:
    return now.strftime("%Y-%m-%d %H:%M:%S IST+0530")


def _json_append(path: str, event: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _usdt_to_inr_from_crypto_levels() -> float:
    try:
        p = os.path.join(LEVELS_DIR, "crypto_initial_levels_latest.json")
        if not os.path.exists(p):
            return float(getattr(cfg, "USDT_TO_INR", 0.0) or DEFAULT_USDT_TO_INR)
        j = json.load(open(p, encoding="utf-8"))
        v = float(j.get("usdt_to_inr", 0.0) or 0.0)
        return v if v > 0 else DEFAULT_USDT_TO_INR
    except Exception:
        return float(getattr(cfg, "USDT_TO_INR", 0.0) or DEFAULT_USDT_TO_INR)


def _load_best_x_global() -> float:
    """
    Read globally best X multiplier from:
      - xopt_live_crypto_YYYYMMDD.csv
      - xopt_ranked_crypto_YYYYMMDD.csv (fallback)
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
        if 0.0001 <= x <= 0.05:
            return x
        return None

    # Prefer today's live output, then newest historical live, then ranked.
    candidates = []
    candidates.append(os.path.join(OPT_RESULTS_DIR, f"xopt_live_crypto_{ds}.csv"))
    candidates += sorted(
        glob.glob(os.path.join(OPT_RESULTS_DIR, "xopt_live_crypto_*.csv")),
        key=os.path.getmtime,
        reverse=True,
    )
    candidates.append(os.path.join(OPT_RESULTS_DIR, f"xopt_ranked_crypto_{ds}.csv"))
    candidates += sorted(
        glob.glob(os.path.join(OPT_RESULTS_DIR, "xopt_ranked_crypto_*.csv")),
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

    x = float(getattr(cfg, "CRYPTO_X_MULTIPLIER", 0.008) or 0.008)
    return x


def _load_crypto_anchors() -> Dict[str, float]:
    """
    Load initial anchor prices from crypto_initial_levels_latest.json.
    """
    p = os.path.join(LEVELS_DIR, "crypto_initial_levels_latest.json")
    if not os.path.exists(p):
        return {}
    j = json.load(open(p, encoding="utf-8")) or {}
    levels = j.get("levels", {}) or {}
    out: Dict[str, float] = {}
    for sym in SYMBOLS:
        lv = levels.get(sym)
        if isinstance(lv, dict):
            a = lv.get("anchor")
            if a is not None:
                out[sym] = float(a)
    return out


@dataclass
class CryptoPos:
    side: str  # BUY / SELL
    entry_px: float
    qty: float
    anchor_at_entry: float
    step: float  # constant half-width in price units (USDT)
    entry_x_mult: float
    retreat_peak: bool = False

    # Snapshot levels at entry (so targets/sl gates stay stable during the trade)
    buy_above: float = 0.0
    sell_below: float = 0.0
    buy_sl: float = 0.0
    sell_sl: float = 0.0
    t_targets: list = None
    st_targets: list = None
    t_exit_65: float = 0.0
    t_exit_25: float = 0.0
    s_exit_65: float = 0.0
    s_exit_25: float = 0.0


class BestXCryptoTrader:
    def __init__(self) -> None:
        self._state_day = _now_ist().strftime("%Y%m%d")
        self._out_path = os.path.join(TRADE_DIR, f"crypto_bestx_trade_events_{self._state_day}.jsonl")

        self._x_mult: float = _load_best_x_global()
        self._usdt_to_inr: float = _usdt_to_inr_from_crypto_levels()

        self._anchors: Dict[str, float] = {}
        self._step: Dict[str, float] = {}   # constant in price units (USDT)

        self._exited: Dict[str, bool] = {s: False for s in SYMBOLS}
        self._pos: Dict[str, Optional[CryptoPos]] = {s: None for s in SYMBOLS}

        self._next_reanchor: datetime = _now_ist() + timedelta(hours=REANCHOR_HOURS)

        self._budget_usdt = float(getattr(cfg, "CRYPTO_BUDGET_USDT", 1065.0) or 1065.0)
        if self._budget_usdt <= 0 and self._usdt_to_inr > 0:
            self._budget_usdt = float(getattr(cfg, "CRYPTO_BUDGET_INR", 100000.0) or 100000.0) / self._usdt_to_inr
        self._broker = build_broker()
        self._risk = TradeRiskController()

    def _crypto_qty(self, price_usdt: float) -> float:
        if price_usdt <= 0 or self._budget_usdt <= 0:
            return 0.0
        return float(self._budget_usdt / price_usdt)

    def _build_levels_for_symbol(self, sym: str, anchor: float) -> Dict[str, float]:
        # Keep step constant (price-units half-width) across re-anchors,
        # matching crypto_engine's apply_crypto_l_reanchor behavior.
        step = float(self._step.get(sym, 0.0) or (anchor * self._x_mult))
        buy_above = anchor + step
        sell_below = anchor - step
        buy_sl = anchor
        sell_sl = anchor
        t_targets = [buy_above + step * i for i in range(1, 6)]
        st_targets = [sell_below - step * i for i in range(1, 6)]
        retreat_65 = buy_above + 0.65 * step
        retreat_25 = buy_above + 0.25 * step
        retreat_s_65 = sell_below - 0.65 * step
        retreat_s_25 = sell_below - 0.25 * step
        return {
            "anchor": anchor,
            "step": step,
            "buy_above": buy_above,
            "sell_below": sell_below,
            "buy_sl": buy_sl,
            "sell_sl": sell_sl,
            "t_targets": t_targets,
            "st_targets": st_targets,
            "retreat_65": retreat_65,
            "retreat_25": retreat_25,
            "retreat_s_65": retreat_s_65,
            "retreat_s_25": retreat_s_25,
        }

    def _rebuild_day_state(self) -> None:
        anchors = _load_crypto_anchors()
        if not anchors:
            log.warning("No crypto anchors found — waiting")
            return
        self._anchors = {}
        self._step = {}
        self._exited = {s: False for s in SYMBOLS}
        self._pos = {s: None for s in SYMBOLS}
        for sym, a in anchors.items():
            if sym in self._step:
                pass
            if a and a > 0:
                self._anchors[sym] = float(a)
                self._step[sym] = float(a * self._x_mult)
        log.info("Rebuilt crypto states: x=%.6f anchors=%d", self._x_mult, len(self._anchors))

    def _load_prices(self) -> Dict[str, float]:
        try:
            with open(LIVE_PRICES_JSON, encoding="utf-8") as f:
                j = json.load(f) or {}
            prices = j.get("crypto_prices") or {}
            out: Dict[str, float] = {}
            for k, v in prices.items():
                try:
                    out[str(k).upper()] = float(v)
                except Exception:
                    continue
            return out
        except Exception:
            return {}

    def _append_entry(self, sym: str, side: str, entry_px: float, qty: float, now: datetime, x_mult_effective: float) -> None:
        broker_order_id = None
        broker_backend = None
        try:
            o = self._broker.place_entry(asset_class="crypto", symbol=sym, side=side, qty=qty, price_hint=entry_px)
            broker_order_id = o.order_id
            broker_backend = o.backend
        except Exception:
            pass
        _json_append(
            self._out_path,
            {
                "ts": _ts_str(now),
                "symbol": sym,
                "side": side,
                "entry_px": float(entry_px),
                "exit_px": None,
                "qty": float(qty),
                "gross_pnl_usdt": None,
                "gross_pnl_inr": None,
                "brokerage_inr": None,
                "net_pnl_inr": None,
                "reason": "ENTRY",
                "x_val": float(x_mult_effective),
                "asset_class": "crypto",
                "currency": "USDT",
                "broker_backend": broker_backend,
                "broker_order_id": broker_order_id,
            },
        )

    def _append_exit(
        self,
        sym: str,
        side: str,
        entry_px: float,
        exit_px: float,
        qty: float,
        reason: str,
        now: datetime,
        x_mult_effective: float,
    ) -> None:
        gross_usdt = (exit_px - entry_px) * qty if side == "BUY" else (entry_px - exit_px) * qty
        gross_inr = gross_usdt * self._usdt_to_inr
        net_inr = gross_inr - BROKERAGE_FLAT_INR
        self._risk.register_exit(sym, float(net_inr), now)
        broker_exit_id = None
        broker_backend = None
        try:
            o = self._broker.place_exit(asset_class="crypto", symbol=sym, side=side, qty=qty, price_hint=exit_px, reason=reason)
            broker_exit_id = o.order_id
            broker_backend = o.backend
        except Exception:
            pass

        _json_append(
            self._out_path,
            {
                "ts": _ts_str(now),
                "symbol": sym,
                "side": side,
                "entry_px": float(entry_px),
                "exit_px": float(exit_px),
                "qty": float(qty),
                "gross_pnl_usdt": round(gross_usdt, 6),
                "gross_pnl_inr": round(gross_inr, 2),
                "brokerage_inr": BROKERAGE_FLAT_INR,
                "net_pnl_inr": round(net_inr, 2),
                "reason": reason,
                "x_val": float(x_mult_effective),
                "asset_class": "crypto",
                "currency": "USDT",
                "broker_backend": broker_backend,
                "broker_exit_order_id": broker_exit_id,
            },
        )

    def _enter_trade(self, sym: str, side: str, price: float, now: datetime) -> None:
        if not self._risk.can_enter(sym, now):
            return
        anchor = self._anchors.get(sym, 0.0)
        if anchor <= 0:
            return
        levels = self._build_levels_for_symbol(sym, anchor)
        step = float(levels["step"])
        if step <= 0:
            return

        qty = self._crypto_qty(price)
        if qty <= 0:
            return

        x_mult_effective = step / anchor if anchor else 0.0

        pos = CryptoPos(
            side=side,
            entry_px=float(price),
            qty=float(qty),
            anchor_at_entry=float(anchor),
            step=step,
            entry_x_mult=float(x_mult_effective),
            retreat_peak=False,
            buy_above=float(levels["buy_above"]),
            sell_below=float(levels["sell_below"]),
            buy_sl=float(levels["buy_sl"]),
            sell_sl=float(levels["sell_sl"]),
            t_targets=levels["t_targets"],
            st_targets=levels["st_targets"],
            t_exit_65=float(levels["retreat_65"]),
            t_exit_25=float(levels["retreat_25"]),
            s_exit_65=float(levels["retreat_s_65"]),
            s_exit_25=float(levels["retreat_s_25"]),
        )
        self._pos[sym] = pos

        self._append_entry(sym, side, price, qty, now, x_mult_effective)

    def _exit_reanchor_target_or_sl(self, sym: str, exit_px: float) -> None:
        # Engine-like L re-anchor: keep step constant (price units), rebuild using new anchor.
        self._anchors[sym] = float(exit_px)
        self._exited[sym] = False
        self._pos[sym] = None

    def _process_symbol(self, sym: str, price: float, now: datetime) -> None:
        pos = self._pos.get(sym)
        if pos is not None:
            side = pos.side
            entry_px = pos.entry_px
            qty = pos.qty

            # Targets (first, to match gate ordering)
            if side == "BUY":
                for i, tgt in enumerate(pos.t_targets, 1):
                    if tgt > entry_px and price >= tgt:
                        self._append_exit(sym, side, entry_px, float(tgt), qty, f"T{i}_HIT", now, pos.step / self._anchors.get(sym, pos.anchor_at_entry))
                        self._exit_reanchor_target_or_sl(sym, float(tgt))
                        return
                # Stop loss
                if pos.buy_sl > 0 and price <= pos.buy_sl:
                    anchor_before = self._anchors.get(sym, pos.anchor_at_entry)
                    self._append_exit(sym, side, entry_px, price, qty, "SL_HIT", now, pos.step / anchor_before if anchor_before else pos.entry_x_mult)
                    # SL_HIT re-anchor to anchor (buy_sl == anchor).
                    self._exit_reanchor_target_or_sl(sym, float(anchor_before))
                    return
                # Retreat
                if (not pos.retreat_peak) and price >= pos.t_exit_65:
                    pos.retreat_peak = True
                if pos.retreat_peak and price <= pos.t_exit_25:
                    anchor_before = self._anchors.get(sym, pos.anchor_at_entry)
                    self._append_exit(sym, side, entry_px, price, qty, "RETREAT", now, pos.step / anchor_before if anchor_before else pos.entry_x_mult)
                    self._pos[sym] = None
                    self._exited[sym] = True
                    return

            else:  # SELL
                for i, tgt in enumerate(pos.st_targets, 1):
                    if tgt < entry_px and price <= tgt:
                        self._append_exit(sym, side, entry_px, float(tgt), qty, f"ST{i}_HIT", now, pos.step / self._anchors.get(sym, pos.anchor_at_entry))
                        self._exit_reanchor_target_or_sl(sym, float(tgt))
                        return
                if pos.sell_sl > 0 and price >= pos.sell_sl:
                    anchor_before = self._anchors.get(sym, pos.anchor_at_entry)
                    self._append_exit(sym, side, entry_px, price, qty, "SL_HIT", now, pos.step / anchor_before if anchor_before else pos.entry_x_mult)
                    self._exit_reanchor_target_or_sl(sym, float(anchor_before))
                    return
                if (not pos.retreat_peak) and price <= pos.s_exit_65:
                    pos.retreat_peak = True
                if pos.retreat_peak and price >= pos.s_exit_25:
                    anchor_before = self._anchors.get(sym, pos.anchor_at_entry)
                    self._append_exit(sym, side, entry_px, price, qty, "RETREAT", now, pos.step / anchor_before if anchor_before else pos.entry_x_mult)
                    self._pos[sym] = None
                    self._exited[sym] = True
                    return

        else:
            # Flat: check scheduled re-entry rules
            if self._exited.get(sym, False):
                return
            anchor = self._anchors.get(sym, 0.0)
            if anchor <= 0:
                return
            levels = self._build_levels_for_symbol(sym, anchor)
            buy_above = float(levels["buy_above"])
            sell_below = float(levels["sell_below"])
            if price >= buy_above:
                self._enter_trade(sym, "BUY", price, now)
            elif price <= sell_below:
                self._enter_trade(sym, "SELL", price, now)

    def _maybe_reanchor(self, now: datetime, prices: Dict[str, float]) -> None:
        if now < self._next_reanchor:
            return
        # Advance next reanchor window
        while self._next_reanchor <= now:
            self._next_reanchor = self._next_reanchor + timedelta(hours=REANCHOR_HOURS)

        # Re-anchor only flat symbols (engine-like: never force-close opens)
        for sym in SYMBOLS:
            if self._pos.get(sym) is not None:
                continue
            px = prices.get(sym)
            if px and px > 0:
                self._anchors[sym] = float(px)
                self._exited[sym] = False

    def run_forever(self) -> None:
        os.makedirs(TRADE_DIR, exist_ok=True)

        self._rebuild_day_state()
        log.info("Crypto BestX paper trader running: x=%.6f", self._x_mult)
        log.info("Crypto risk controls active: %s", self._risk.snapshot(_now_ist()))

        last_x_refresh = time.monotonic()
        x_refresh_s = 30.0
        while True:
            now = _now_ist()
            # Day rollover -> switch output file but keep state simplistic
            ds = now.strftime("%Y%m%d")
            if ds != self._state_day:
                self._state_day = ds
                self._out_path = os.path.join(TRADE_DIR, f"crypto_bestx_trade_events_{ds}.jsonl")
                self._rebuild_day_state()

            prices = self._load_prices()
            if not prices:
                time.sleep(2.0)
                continue

            # Reload best X globally every ~30s.
            if time.monotonic() - last_x_refresh > x_refresh_s:
                new_x = _load_best_x_global()
                if abs(float(new_x) - float(self._x_mult)) > 0.00005:
                    self._x_mult = float(new_x)
                    self._rebuild_day_state()
                last_x_refresh = time.monotonic()

            # Scheduled re-anchor
            self._maybe_reanchor(now, prices)

            # Process symbol ticks
            for sym in SYMBOLS:
                px = prices.get(sym)
                if px and px > 0:
                    self._process_symbol(sym, float(px), now)

            time.sleep(2.0)


def main() -> None:
    try:
        BestXCryptoTrader().run_forever()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()

