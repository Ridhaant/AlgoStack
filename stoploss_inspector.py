"""
stoploss_inspector.py
======================
Live Stoploss-Hit Analyzer for AlgoStack (Equity + MCX + Crypto).

What it does:
- Reads/trails today's JSONL trade logs:
  - trade_logs/trade_events_YYYYMMDD.jsonl             (equity)
  - trade_logs/commodity_trade_events_YYYYMMDD.jsonl (commodities)
  - trade_logs/crypto_trade_events_YYYYMMDD.jsonl    (crypto)
- Reconstructs a "current open position" per asset/symbol (best-effort).
- For every stoploss exit:
  - Computes entry->SL time delta
  - Computes SL severity (distance)
  - Detects anomalies (SL without open entry, impossible direction)
- Buckets SL hits into root-cause groups and emits:
  - Console summary (last N stoploss hits + bucket counts)
  - JSON report: algostack_logs/reports/stoploss_insights_YYYYMMDD.json
- Optional live-fix mode:
  - When it detects "impossible target-hit negative gross" anomalies
    (common past failure mode), it can prompt to sanitize today's
    commodity/crypto JSONL files and/or delete stale scanner state so
    engines rebuild.

Safety:
- No trading actions.
- File sanitization is idempotent and guarded by a "already fixed" marker
  in the reason field (e.g. FIX_SWAP_...).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple

import pytz

from config import cfg

try:
    from log_manager import LogManager
except Exception:
    LogManager = None  # type: ignore


IST = pytz.timezone("Asia/Kolkata")


EQUITY_SL_EVENTS = {"BUY_SL", "SELL_SL"}
EQUITY_ENTRY_EVENTS = {"BUY_ENTRY", "SELL_ENTRY"}

_RE_TS_ISO = re.compile(r".*T.*")
_RE_DATE_TIME_IST_OFF = re.compile(r"^(?P<base>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) IST(?P<off>[+-]\d{4})$")

# Commodity/Crypto reasons:
# - ENTRY
# - SL_HIT
# - T1_HIT..T5_HIT, ST1_HIT..ST5_HIT
# - RETREAT
# - EOD_2330 (commodity), EOD_SQUAREOFF_REANCHOR (crypto) etc.
_RE_TARGET_HIT = re.compile(r"^(T[1-5]_HIT|ST[1-5]_HIT)$")


FAST_SL_AFTER_ENTRY_SEC = float(os.getenv("SLINSPECT_FAST_SEC", "15"))
BROKERAGE_DOMINANCE_RATIO = float(os.getenv("SLINSPECT_BROKER_DOM_RATIO", "0.75"))
MIN_DIST_PCT = float(os.getenv("SLINSPECT_MIN_DIST_PCT", "0.001"))


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _parse_ts_to_ist(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    s = str(ts).strip()
    if not s:
        return None

    try:
        if _RE_TS_ISO.match(s):
            # Equity uses ISO with tz offset.
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = IST.localize(dt)
            else:
                dt = dt.astimezone(IST)
            return dt
    except Exception:
        pass

    # Commodity/Crypto use: "2026-03-30 09:36:00 IST+0530"
    m = _RE_DATE_TIME_IST_OFF.match(s)
    if m:
        base = m.group("base")
        try:
            dt = datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
            return IST.localize(dt)
        except Exception:
            return None

    # Fallback: try common patterns.
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            dt = datetime.strptime(s[: len(fmt)], fmt)
            return IST.localize(dt)
        except Exception:
            continue
    return None


def _now_ist_ts() -> str:
    return datetime.now(IST).isoformat()


def _read_jsonl_lines(path: str, start_offset: int = 0) -> Tuple[List[dict], int]:
    """
    Read JSONL lines from a file starting at byte offset.
    Returns parsed dicts and new offset.
    """
    if not os.path.exists(path):
        return [], start_offset
    try:
        with open(path, "r", encoding="utf-8") as fh:
            fh.seek(start_offset)
            out: List[dict] = []
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    # Keep going; ignore corrupt/partial lines.
                    continue
            return out, fh.tell()
    except Exception:
        # Best-effort: no hard fail for a monitoring tool.
        return [], start_offset


def _write_json_atomic(path: str, payload: dict) -> None:
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def _report_path(date_str: str) -> str:
    if LogManager is not None:
        return LogManager.path("reports", f"stoploss_insights_{date_str}.json")
    return os.path.join("algostack_logs", "reports", f"stoploss_insights_{date_str}.json")


def sl_px_guess(_asset_class: str, entry_px: float, exit_px: float) -> float:
    """Best-effort fallback when log row is missing exit_px."""
    if exit_px and exit_px > 0:
        return float(exit_px)
    return float(entry_px or 0.0)


@dataclass
class OpenPos:
    asset_class: str
    symbol: str
    side: str
    entry_ts: Optional[datetime]
    entry_px: float
    qty: float
    meta: dict


def _expected_target_direction(side: str, entry_px: float, exit_px: float) -> bool:
    if side == "BUY":
        return exit_px > entry_px
    # SELL
    return exit_px < entry_px


def _commodity_or_crypto_target_anomaly(rec: dict) -> Optional[str]:
    """
    Detect "target hit but negative gross" that should be impossible:
    - reason is a target hit (T1..T5, ST1..ST5)
    - side is BUY and exit_px <= entry_px OR side is SELL and exit_px >= entry_px
    Returns anomaly key string if detected.
    """
    reason_raw = str(rec.get("reason", "") or "").strip().upper()
    if not reason_raw:
        return None

    # Engines may tag corrected rows as FIX_SWAP_* or ANOMALY_*.
    # Treat ANOMALY_* as a hard anomaly; treat FIX_SWAP_* as "was bad but fixed".
    tagged = None
    reason = reason_raw
    for pfx in ("ANOMALY_", "FIX_SWAP_"):
        if reason.startswith(pfx):
            tagged = pfx.rstrip("_")
            reason = reason[len(pfx) :]
            break

    # If it's tagged as ANOMALY, we always surface it (even if it no longer matches *_HIT).
    if tagged == "ANOMALY":
        gross_inr = rec.get("gross_pnl_inr", rec.get("gross_pnl"))
        gross = _safe_float(gross_inr)
        return f"ENGINE_TAGGED_ANOMALY::{reason_raw}::{gross:+.2f}"

    if not _RE_TARGET_HIT.match(reason):
        return None

    side = str(rec.get("side", "") or "").strip().upper()
    if side not in {"BUY", "SELL"}:
        return None

    entry_px = _safe_float(rec.get("entry_px"))
    exit_px = _safe_float(rec.get("exit_px"))
    if entry_px <= 0 or exit_px <= 0:
        return None

    expected_good = _expected_target_direction(side, entry_px, exit_px)
    if expected_good:
        return None

    gross_inr = rec.get("gross_pnl_inr", rec.get("gross_pnl"))
    gross = _safe_float(gross_inr)
    # Even if gross could be negative because of data issues, we still want to flag.
    # If engine already fixed it via swap tagging, downgrade severity but still track.
    if tagged == "FIX_SWAP":
        return f"FIXED_SWAP_TARGET_EXIT::{reason_raw}::{gross:+.2f}"
    return f"IMPOSSIBLE_TARGET_NEGATIVE_GROSS::{reason_raw}::{gross:+.2f}"


class StoplossInspector:
    def __init__(self, date_str: str, live_fix: bool = True) -> None:
        self.date_str = date_str
        self.live_fix = live_fix

        self.sl_buckets: Dict[str, int] = defaultdict(int)
        self.sl_recent: Deque[dict] = deque(maxlen=30)

        self.anomalies: Dict[str, int] = defaultdict(int)
        self.anom_recent: Deque[dict] = deque(maxlen=50)

        # open positions reconstructed from logs
        self.open_equity: Dict[str, OpenPos] = {}
        self.open_comm: Dict[str, OpenPos] = {}
        self.open_crypto: Dict[str, OpenPos] = {}

        # file offsets for tailing
        self.offsets: Dict[str, int] = {}

        # live-fix latch
        self._fixed_today = False

    def _handle_equity_event(self, rec: dict) -> None:
        sym = str(rec.get("symbol", "") or "").strip().upper()
        if not sym:
            return
        et = str(rec.get("event_type", "") or "").strip().upper()
        side = str(rec.get("side", "") or "").strip().upper()
        price = _safe_float(rec.get("price"))
        qty = _safe_float(rec.get("qty"), 0.0)
        entry_px = _safe_float(rec.get("entry_price"), price)
        gross = _safe_float(rec.get("gross", rec.get("gross_pnl", 0.0)))
        net = _safe_float(rec.get("net", rec.get("net_pnl", 0.0)))
        ts = _parse_ts_to_ist(rec.get("timestamp"))

        if et in EQUITY_ENTRY_EVENTS:
            # If there's already an open pos, mark anomaly and overwrite best-effort.
            if sym in self.open_equity:
                self.anomalies["EQUITY_OVERWRITE_OPEN_ENTRY"] += 1
                self.anom_recent.append(
                    {"asset": "equity", "symbol": sym, "type": "OVERWRITE", "ts": ts.isoformat() if ts else None}
                )
            self.open_equity[sym] = OpenPos(
                asset_class="equity",
                symbol=sym,
                side=side,
                entry_ts=ts,
                entry_px=entry_px,
                qty=qty,
                meta={"event_type": et},
            )
            return

        # Exit handling
        if et in EQUITY_SL_EVENTS:
            self._classify_equity_sl(
                sym=sym,
                side=side,
                sl_ts=ts,
                sl_px=price,
                entry_px=entry_px,
                qty=qty,
                gross=gross,
                net=net,
            )
            # Close open position if present.
            self.open_equity.pop(sym, None)
            return

        # Close open pos on any known exit types:
        # Targets, retreats, EOD, manual.
        if et.startswith("T") or et.startswith("ST") or "RETREAT" in et or et.startswith("EOD") or et.startswith("MANUAL"):
            self.open_equity.pop(sym, None)
            return

    def _classify_equity_sl(
        self,
        sym: str,
        side: str,
        sl_ts: Optional[datetime],
        sl_px: float,
        entry_px: float,
        qty: float,
        gross: float,
        net: float,
    ) -> None:
        op = self.open_equity.get(sym)
        # Use reconstructed entry_px if available; otherwise fall back to log's entry_price.
        true_entry_px = entry_px if entry_px > 0 else (op.entry_px if op else 0.0)
        entry_ts = sl_ts
        if op and op.entry_ts:
            entry_ts = op.entry_ts

        # If no entry existed, this is a data anomaly.
        if not op:
            self.anomalies["EQUITY_SL_WITH_NO_OPEN_ENTRY"] += 1
            self.anom_recent.append({"asset": "equity", "symbol": sym, "type": "NO_OPEN_ENTRY", "sl_px": sl_px})
            self.sl_buckets["SL_WITH_NO_OPEN_ENTRY"] += 1
            rec = {
                "asset": "equity",
                "symbol": sym,
                "side": side,
                "sl_ts": sl_ts.isoformat() if sl_ts else None,
                "entry_ts": None,
                "entry_px": true_entry_px,
                "sl_px": sl_px,
                "qty": qty,
                "gross": gross,
                "net": net,
                "bucket": "SL_WITH_NO_OPEN_ENTRY",
            }
            self.sl_recent.append(rec)
            return

        dt_sec = None
        if op.entry_ts and sl_ts:
            dt_sec = (sl_ts - op.entry_ts).total_seconds()

        brokerage = abs(gross - net) if abs(gross - net) > 1e-9 else 0.0
        dist_pct = abs(sl_px - op.entry_px) / op.entry_px * 100.0 if op.entry_px else 0.0

        # Direction checks: for BUY_SL, gross should be negative (exit below entry); for SELL_SL, gross negative (exit above entry).
        # We can only validate net/gross sign with the log itself.
        if gross > 1e-6 or net > 1e-6:
            self.anomalies["EQUITY_SL_IMPOSSIBLE_POSITIVE_GROSS"] += 1
            self.anom_recent.append({"asset": "equity", "symbol": sym, "type": "IMPOSSIBLE_SL_POSITIVE", "gross": gross, "net": net})
            bucket = "IMPOSSIBLE_SL_DIRECTION"
        elif dt_sec is not None and dt_sec <= FAST_SL_AFTER_ENTRY_SEC:
            bucket = "FAST_SL_AFTER_ENTRY"
        elif brokerage > 0 and abs(gross) > 0 and abs(gross) <= brokerage * BROKERAGE_DOMINANCE_RATIO:
            bucket = "BROKERAGE_DOMINATED_SL"
        elif dist_pct >= MIN_DIST_PCT and dt_sec is not None and dt_sec <= 90:
            bucket = "SL_IN_SHORT_WINDOW"
        else:
            bucket = "SL_STANDARD"

        self.sl_buckets[bucket] += 1
        self.sl_recent.append(
            {
                "asset": "equity",
                "symbol": sym,
                "side": side,
                "sl_ts": sl_ts.isoformat() if sl_ts else None,
                "entry_ts": op.entry_ts.isoformat() if op.entry_ts else None,
                "entry_px": op.entry_px,
                "sl_px": sl_px,
                "dt_sec": dt_sec,
                "dist_pct": dist_pct,
                "qty": qty,
                "gross": gross,
                "net": net,
                "brokerage_derived": brokerage,
                "bucket": bucket,
            }
        )

    def _handle_comm_or_crypto_event(self, rec: dict, asset_class: str) -> None:
        sym = str(rec.get("symbol", "") or "").strip().upper()
        if not sym:
            return
        reason = str(rec.get("reason", "") or "").strip().upper()
        side = str(rec.get("side", "") or "").strip().upper()
        ts = _parse_ts_to_ist(rec.get("ts") or rec.get("timestamp"))
        entry_px = _safe_float(rec.get("entry_px"))
        exit_px = _safe_float(rec.get("exit_px"))
        qty = _safe_float(rec.get("qty"), 0.0)
        gross = _safe_float(rec.get("gross_pnl_inr", rec.get("gross_pnl")))
        net = _safe_float(rec.get("net_pnl_inr", rec.get("net_pnl")))

        open_map = self.open_comm if asset_class == "commodity" else self.open_crypto

        if reason == "ENTRY":
            if sym in open_map:
                self.anomalies[f"{asset_class.upper()}_OVERWRITE_OPEN_ENTRY"] += 1
                self.anom_recent.append({"asset": asset_class, "symbol": sym, "type": "OVERWRITE", "ts": ts.isoformat() if ts else None})
            open_map[sym] = OpenPos(
                asset_class=asset_class,
                symbol=sym,
                side=side,
                entry_ts=ts,
                entry_px=entry_px,
                qty=qty,
                meta={"reason": "ENTRY"},
            )
            return

        # Target anomalies (regression guard): "T1_HIT but negative gross should be impossible"
        tgt_anom = _commodity_or_crypto_target_anomaly(rec)
        if tgt_anom:
            self.anomalies[tgt_anom] += 1
            self.anom_recent.append({"asset": asset_class, "symbol": sym, "type": "IMPOSSIBLE_TARGET_NEG_GROSS", "reason": reason, "gross": gross, "net": net})

        if reason == "SL_HIT":
            op = open_map.get(sym)
            if not op:
                self.anomalies[f"{asset_class.upper()}_SL_WITH_NO_OPEN_ENTRY"] += 1
                bucket = "SL_WITH_NO_OPEN_ENTRY"
                self.sl_buckets[bucket] += 1
                self.sl_recent.append(
                    {
                        "asset": asset_class,
                        "symbol": sym,
                        "side": side,
                        "entry_ts": None,
                        "entry_px": entry_px,
                        "sl_ts": ts.isoformat() if ts else None,
                        "sl_px": exit_px if exit_px > 0 else sl_px_guess(asset_class, entry_px, exit_px),
                        "dt_sec": None,
                        "gross": gross,
                        "net": net,
                        "bucket": bucket,
                    }
                )
                return

            dt_sec = None
            if op.entry_ts and ts:
                dt_sec = (ts - op.entry_ts).total_seconds()
            dist_pct = abs(exit_px - op.entry_px) / op.entry_px * 100.0 if op.entry_px else 0.0
            brokerage = abs(gross - net) if abs(gross - net) > 1e-9 else 0.0

            # direction anomaly for SL: gross should be negative for SL in general
            if gross > 1e-6 or net > 1e-6:
                self.anomalies[f"{asset_class.upper()}_SL_IMPOSSIBLE_POSITIVE_GROSS"] += 1
                bucket = "IMPOSSIBLE_SL_DIRECTION"
            elif dt_sec is not None and dt_sec <= FAST_SL_AFTER_ENTRY_SEC:
                bucket = "FAST_SL_AFTER_ENTRY"
            elif brokerage > 0 and abs(gross) > 0 and abs(gross) <= brokerage * BROKERAGE_DOMINANCE_RATIO:
                bucket = "BROKERAGE_DOMINATED_SL"
            elif dist_pct >= MIN_DIST_PCT and dt_sec is not None and dt_sec <= 90:
                bucket = "SL_IN_SHORT_WINDOW"
            else:
                bucket = "SL_STANDARD"

            self.sl_buckets[bucket] += 1
            self.sl_recent.append(
                {
                    "asset": asset_class,
                    "symbol": sym,
                    "side": side,
                    "entry_ts": op.entry_ts.isoformat() if op.entry_ts else None,
                    "entry_px": op.entry_px,
                    "sl_ts": ts.isoformat() if ts else None,
                    "sl_px": exit_px,
                    "dt_sec": dt_sec,
                    "dist_pct": dist_pct,
                    "qty": qty,
                    "gross": gross,
                    "net": net,
                    "brokerage_derived": brokerage,
                    "bucket": bucket,
                    "reason": reason,
                }
            )

            open_map.pop(sym, None)
            return

        # Close open position on any non-entry exit reasons.
        if exit_px > 0 and reason != "ENTRY":
            open_map.pop(sym, None)

    def _maybe_prompt_live_fixes(self, report_payload: dict) -> None:
        """
        Live-fix mode: when we detect regression anomalies, ask permission.
        We only do "safe" file fixes (sanitize JSONL + optionally delete stale state).
        """
        if not self.live_fix or self._fixed_today:
            return

        impossible_targets = [
            k for k in self.anomalies.keys() if "IMPOSSIBLE_TARGET_NEGATIVE_GROSS" in k
        ]
        if not impossible_targets:
            return

        total = sum(self.anomalies[k] for k in impossible_targets)
        if total <= 0:
            return

        print("\n[SLINSPECT] Detected impossible target-hit negative gross anomalies:")
        for k in sorted(impossible_targets)[:5]:
            print(f"  - {k}: {self.anomalies[k]}")
        print(f"Total anomalies (today): {total}")

        ans = input("[SLINSPECT] Run safe sanitization for commodity+crypto JSONL now? (y/n): ").strip().lower()
        if ans != "y":
            print("[SLINSPECT] Live fix declined.")
            return

        fixed_any = False
        try:
            fixed_any |= sanitize_impossible_targets_in_commodity(self.date_str)
        except Exception as e:
            print(f"[SLINSPECT] Commodity sanitization failed: {e}")
        try:
            fixed_any |= sanitize_impossible_targets_in_crypto(self.date_str)
        except Exception as e:
            print(f"[SLINSPECT] Crypto sanitization failed: {e}")

        if fixed_any:
            print("[SLINSPECT] Sanitization complete (idempotent).")
            self._fixed_today = True
            report_payload["live_fix"] = {"sanitized": True, "ts": _now_ist_ts()}
        else:
            print("[SLINSPECT] Nothing fixed (already clean or insufficient data).")

        # Optional stale scanner rebuild prompt (lightweight).
        ans2 = input("[SLINSPECT] Also delete stale S1/S3 scanner live_state.json to force rebuild? (y/n): ").strip().lower()
        if ans2 == "y":
            deleted = delete_stale_scanner_live_state(self.date_str)
            print(f"[SLINSPECT] Deleted {deleted} stale live_state.json files.")

    def consume_equity_lines(self, lines: Iterable[dict]) -> None:
        for rec in lines:
            self._handle_equity_event(rec)

    def consume_commodity_lines(self, lines: Iterable[dict]) -> None:
        for rec in lines:
            self._handle_comm_or_crypto_event(rec, asset_class="commodity")

    def consume_crypto_lines(self, lines: Iterable[dict]) -> None:
        for rec in lines:
            self._handle_comm_or_crypto_event(rec, asset_class="crypto")

    def snapshot_report(self) -> Dict[str, Any]:
        total_sl = sum(self.sl_buckets.values())
        return {
            "date": self.date_str,
            "generated_at": _now_ist_ts(),
            "sl_bucket_counts": dict(self.sl_buckets),
            "sl_total": total_sl,
            "recent_sl_hits": list(self.sl_recent),
            "anomalies_counts": dict(self.anomalies),
            "recent_anomalies": list(self.anom_recent)[-20:],
            "recommendations": recommendations_from_buckets(self.sl_buckets, self.anomalies),
        }

    def print_console(self) -> None:
        # Keep console compact: show bucket counts + last few SL hits.
        print("\n===== Stoploss Inspector (live) =====")
        print(f"Date: {self.date_str}  Timestamp: {_now_ist_ts()}")
        if not self.sl_buckets:
            print("No SL hits classified yet.")
        else:
            print("SL buckets:")
            for k, v in sorted(self.sl_buckets.items(), key=lambda kv: kv[1], reverse=True):
                print(f"  - {k}: {v}")

        if self.sl_recent:
            print("\nLast SL hits:")
            for r in list(self.sl_recent)[-8:]:
                sym = r.get("symbol")
                asset = r.get("asset")
                bucket = r.get("bucket")
                dt = r.get("dt_sec")
                dist = r.get("dist_pct")
                sl_px = r.get("sl_px")
                print(f"  - {asset}:{sym} bucket={bucket} dt={dt} dist_pct={dist} sl_px={sl_px}")


def sl_px_guess(asset_class: str, entry_px: float, exit_px: float) -> float:
    # Small helper for cases where log is missing exit_px.
    if exit_px and exit_px > 0:
        return exit_px
    return entry_px


def recommendations_from_buckets(
    sl_buckets: Dict[str, int],
    anomalies: Dict[str, int],
) -> List[dict]:
    recs: List[dict] = []
    if not sl_buckets:
        return recs

    def _add(key: str, why: str, fixes: List[str]) -> None:
        recs.append({"bucket": key, "why": why, "recommendations": fixes})

    if sl_buckets.get("FAST_SL_AFTER_ENTRY", 0) > 0:
        _add(
            "FAST_SL_AFTER_ENTRY",
            "Stoploss triggers very quickly after a fresh entry (likely gap/stale levels or tick jumps).",
            [
                "Add a short entry confirmation window: require 1-2 consecutive ticks beyond SL buffer before arming SL evaluation.",
                "Increase effective SL distance for symbols with repeated fast SL (symbol-specific min SL distance).",
                "Temporarily widen buy_above/sell_below on re-anchoring to reduce gap risk.",
            ],
        )
    if sl_buckets.get("BROKERAGE_DOMINATED_SL", 0) > 0:
        _add(
            "BROKERAGE_DOMINATED_SL",
            "Many stoplosses are small losses where brokerage dominates, making net negative even if gross is near zero.",
            [
                "Widen targets / reduce trade churn (avoid re-entry too aggressively after exit).",
                "Add a profitability floor: if expected gross distance < X, skip SL/entry for that symbol+state.",
                "Add a minimum duration filter: ignore SL exits that happen before a minimum time threshold.",
            ],
        )
    if sl_buckets.get("IMPOSSIBLE_SL_DIRECTION", 0) > 0:
        _add(
            "IMPOSSIBLE_SL_DIRECTION",
            "Stoploss exit shows an impossible profit direction, indicating a log mismatch or wrong ladder comparison.",
            [
                "Verify entry/exit swap guards exist in the relevant engine (equity: BUY_SL/SELL_SL, commodity: SL_HIT).",
                "Add regression unit checks: ensure gross sign matches direction for each exit type.",
            ],
        )
    if any("IMPOSSIBLE_TARGET_NEGATIVE_GROSS" in k for k in anomalies.keys()):
        recs.append(
            {
                "bucket": "IMPOSSIBLE_TARGET_NEGATIVE_GROSS",
                "why": "A regression where a target-hit row implies negative gross profit (direction mismatch).",
                "recommendations": [
                    "Keep the entry-relative guards around target evaluation (mirrors crypto_engine's implementation).",
                    "Add idempotent sanitization to repair past rows and mark them FIX_SWAP_* so the dashboard never shows impossible totals.",
                ],
            }
        )
    # Always include a generic improvement.
    recs.append(
        {
            "bucket": "GENERIC",
            "why": "Cross-checks suggest stoploss exits are sensitive to level anchoring + tick timing.",
            "recommendations": [
                "Add symbol-specific tuning for re-anchor thresholds and stoploss buffers based on observed dt_sec distribution.",
                "Track: entry->first_target_hit_time and entry->sl_time; use it to detect where ladder logic diverges.",
            ],
        }
    )
    return recs


def _scan_and_fix_jsonl(
    path: str,
    fix_fn,
) -> bool:
    if not os.path.exists(path):
        return False
    changed = False
    tmp_path = path + ".tmp"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "r", encoding="utf-8") as src, open(tmp_path, "w", encoding="utf-8") as dst:
        for raw in src:
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                dst.write(raw)
                continue
            new_rec, ok = fix_fn(rec)
            if ok:
                changed = True
            dst.write(json.dumps(new_rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    if changed:
        os.replace(tmp_path, path)
    else:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
    return changed


def sanitize_impossible_targets_in_commodity(date_str: str) -> bool:
    """
    Sanitize commodity JSONL for "target-hit but direction mismatch" anomalies.
    Detects cases where reason is T*_HIT/ST*_HIT but exit_px does not match expected direction.
    If found, swaps entry_px/exit_px and recomputes gross_pnl/net_pnl using cfg.USDT_TO_INR and BROKERAGE=20.
    Returns True if any change applied.
    """
    path = os.path.join("trade_logs", f"commodity_trade_events_{date_str}.jsonl")
    if not os.path.exists(path):
        return False

    usdt_to_inr = float(getattr(cfg, "USDT_TO_INR", 84.0) or 84.0)
    brokerage = 20.0

    def _fix(rec: dict) -> Tuple[dict, bool]:
        reason = str(rec.get("reason", "") or "").strip().upper()
        if reason.startswith("FIX_SWAP_"):
            return rec, False

        if not _RE_TARGET_HIT.match(reason):
            return rec, False

        side = str(rec.get("side", "") or "").strip().upper()
        if side not in {"BUY", "SELL"}:
            return rec, False

        entry_px = _safe_float(rec.get("entry_px"))
        exit_px = _safe_float(rec.get("exit_px"))
        qty = _safe_float(rec.get("qty"), 0.0)
        if entry_px <= 0 or exit_px <= 0 or qty <= 0:
            return rec, False

        expected_good = _expected_target_direction(side, entry_px, exit_px)
        if expected_good:
            return rec, False

        # Swap and recompute.
        swapped_good = _expected_target_direction(side, exit_px, entry_px)
        if not swapped_good:
            # Can't safely fix; leave as-is but mark anomaly.
            return rec, False

        new_entry = exit_px
        new_exit = entry_px

        if side == "BUY":
            gross_usdt = (new_exit - new_entry) * qty
        else:
            gross_usdt = (new_entry - new_exit) * qty

        gross_inr = gross_usdt * usdt_to_inr
        net_inr = gross_inr - brokerage

        rec["entry_px"] = round(new_entry, 8)
        rec["exit_px"] = round(new_exit, 8)
        rec["gross_pnl"] = round(gross_inr, 2)
        rec["net_pnl"] = round(net_inr, 2)
        rec["reason"] = f"FIX_SWAP_{reason}"
        return rec, True

    return _scan_and_fix_jsonl(path, _fix)


def sanitize_impossible_targets_in_crypto(date_str: str) -> bool:
    """
    Crypto engine already has a trade-log sanitizer, but we keep this safe
    repair here as well to guarantee the dashboard never shows impossible
    totals.
    """
    path = os.path.join("trade_logs", f"crypto_trade_events_{date_str}.jsonl")
    if not os.path.exists(path):
        return False

    usdt_to_inr = float(getattr(cfg, "USDT_TO_INR", 84.0) or 84.0)
    brokerage_inr = 20.0

    def _fix(rec: dict) -> Tuple[dict, bool]:
        reason = str(rec.get("reason", "") or "").strip().upper()
        if reason.startswith("FIX_SWAP_") or reason.startswith("ANOMALY_"):
            return rec, False

        if not _RE_TARGET_HIT.match(reason):
            return rec, False

        side = str(rec.get("side", "") or "").strip().upper()
        if side not in {"BUY", "SELL"}:
            return rec, False

        entry_px = _safe_float(rec.get("entry_px"))
        exit_px = _safe_float(rec.get("exit_px"))
        qty = _safe_float(rec.get("qty"), 0.0)
        if entry_px <= 0 or exit_px <= 0 or qty <= 0:
            return rec, False

        expected_good = _expected_target_direction(side, entry_px, exit_px)
        if expected_good:
            return rec, False

        swapped_good = _expected_target_direction(side, exit_px, entry_px)
        if not swapped_good:
            return rec, False

        new_entry = exit_px
        new_exit = entry_px

        # Recompute gross in USDT then INR.
        if side == "BUY":
            gross_usdt = (new_exit - new_entry) * qty
        else:
            gross_usdt = (new_entry - new_exit) * qty
        gross_inr = gross_usdt * usdt_to_inr
        net_inr = gross_inr - brokerage_inr

        rec["entry_px"] = round(new_entry, 8)
        rec["exit_px"] = round(new_exit, 8)
        rec["gross_pnl_usdt"] = round(gross_usdt, 6)
        rec["gross_pnl_inr"] = round(gross_inr, 2)
        rec["net_pnl_inr"] = round(net_inr, 2)
        rec["brokerage_inr"] = brokerage_inr
        rec["reason"] = f"FIX_SWAP_{reason}"
        return rec, True

    return _scan_and_fix_jsonl(path, _fix)


def delete_stale_scanner_live_state(date_str: str) -> int:
    """
    Deletes scanner live_state.json for S1 and S3 for the given date folder,
    which forces the running scanner process to rebuild on its next dump cycle.
    """
    paths = [
        os.path.join("sweep_results", "scanner1_narrow_x0080_x0090", date_str, "live_state.json"),
        os.path.join("sweep_results", "scanner3_widedual_x0010_x0320", date_str, "live_state.json"),
    ]
    deleted = 0
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
                deleted += 1
        except Exception:
            continue
    return deleted


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AlgoStack Stoploss Inspector (equity + MCX + crypto)")
    p.add_argument("--date", default=datetime.now(IST).strftime("%Y%m%d"), help="Trading date YYYYMMDD")
    p.add_argument("--tail-interval", type=float, default=float(os.getenv("SLINSPECT_TAIL_S", "2.0")), help="Polling interval seconds")
    p.add_argument("--flush-interval", type=float, default=float(os.getenv("SLINSPECT_FLUSH_S", "10.0")), help="Report flush interval seconds")
    p.add_argument("--live-fix", type=str, default=os.getenv("SLINSPECT_LIVE_FIX", "1"), help="1 to enable live-fix prompts; 0 disables prompts")
    return p


def _init_offsets_if_needed(path: str) -> int:
    # Start by hydrating from file start, so offsets should start at end after hydration.
    if not os.path.exists(path):
        return 0
    try:
        return os.path.getsize(path)
    except Exception:
        return 0


def main() -> None:
    ap = _build_argparser()
    args = ap.parse_args()

    date_str = str(args.date).strip()
    live_fix = str(args.live_fix).strip() not in {"0", "false", "False", "no", "NO"}

    inspector = StoplossInspector(date_str=date_str, live_fix=live_fix)

    equity_path = os.path.join("trade_logs", f"trade_events_{date_str}.jsonl")
    comm_path = os.path.join("trade_logs", f"commodity_trade_events_{date_str}.jsonl")
    crypto_path = os.path.join("trade_logs", f"crypto_trade_events_{date_str}.jsonl")

    sources = [
        ("equity", equity_path),
        ("commodity", comm_path),
        ("crypto", crypto_path),
    ]

    # 1) Hydrate from existing content.
    for asset, path in sources:
        if not os.path.exists(path):
            continue
        lines: List[dict] = []
        try:
            # Read whole file once (bounded by "today only").
            with open(path, "r", encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        lines.append(json.loads(raw))
                    except Exception:
                        continue
        except Exception:
            lines = []

        if asset == "equity":
            inspector.consume_equity_lines(lines)
        elif asset == "commodity":
            inspector.consume_commodity_lines(lines)
        else:
            inspector.consume_crypto_lines(lines)

        # After hydration, set offsets to EOF.
        inspector.offsets[path] = os.path.getsize(path)

    last_flush = time.monotonic()
    last_print = 0.0
    while True:
        now_m = time.monotonic()

        # Tail each file by size/offset.
        for asset, path in sources:
            if not os.path.exists(path):
                continue
            off = inspector.offsets.get(path, 0)
            try:
                size = os.path.getsize(path)
            except Exception:
                continue
            if size <= off:
                continue
            new_recs, new_off = _read_jsonl_lines(path, start_offset=off)
            inspector.offsets[path] = new_off
            if asset == "equity":
                inspector.consume_equity_lines(new_recs)
            elif asset == "commodity":
                inspector.consume_commodity_lines(new_recs)
            else:
                inspector.consume_crypto_lines(new_recs)

        # Flush reports periodically.
        if now_m - last_flush >= float(args.flush_interval):
            payload = inspector.snapshot_report()
            payload_path = _report_path(date_str)
            _write_json_atomic(payload_path, payload)
            # Live-fix prompt (optional).
            inspector._maybe_prompt_live_fixes(payload)
            _write_json_atomic(payload_path, inspector.snapshot_report())

            last_flush = now_m

        # Print console every few cycles (not too often).
        if now_m - last_print >= 8.0:
            inspector.print_console()
            last_print = now_m

        time.sleep(float(args.tail_interval))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SLINSPECT] Stopped by user.")
        sys.exit(0)

