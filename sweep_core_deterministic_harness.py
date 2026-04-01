"""
Deterministic mini-simulation harness for sweep_core.StockSweep.

Goal:
  - Validate tick-level ladder breach counters for T1..T5 and ST1..ST5.
  - Validate drawdown tracking from cumulative total_pnl.
  - Validate multi-metric best-X selection wiring (best_x + breach summary).

Run:
  python sweep_core_deterministic_harness.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from sweep_core import IST, StockSweep


def _ts(hour: int, minute: int) -> datetime:
    # Keep it inside the trading window but outside entry blackout.
    # sweep_core entry blackout for equity is 09:15–09:35.
    return IST.localize(datetime(2026, 1, 1, hour, minute, 0, 0))


@dataclass
class CaseResult:
    name: str
    ok: bool
    details: str = ""


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise AssertionError(msg)


def test_buy_breach_drawdown_and_best_x() -> CaseResult:
    # Two BUY variations:
    #   v0 x=0.0001  => entry at 100.01, T1 at 100.02
    #   v1 x=0.0010  => entry at 100.10, should stay inactive
    x_vals = np.array([0.0001, 0.0010], dtype=np.float64)
    sw = StockSweep(symbol="TEST_BUY", prev_close=100.0, x_values_np=x_vals)

    # Tick 1: enter only v0 (price == buy_above for v0)
    p1 = float(sw.buy_above[0])
    sw.on_price(p1, _ts(10, 0))
    _assert(sw.trade_count[0] == 0, "BUY tick1 should not exit")
    _assert(int(sw.breach_ticks_T[:, 0].sum()) == 0, "No T-level breach on entry tick")

    # Tick 2: hit T1 for v0 (price == T1 for v0)
    # Small epsilon avoids float rounding edge-cases on comparisons.
    p2 = float(sw.t[0][0]) + 1e-9
    sw.on_price(p2, _ts(10, 1))
    _assert(int(sw.trade_count[0]) == 1, "BUY tick2 should exit exactly once for v0")

    # Breach counters:
    #   - T1 breached for exactly one tick (tick2)
    _assert(int(sw.breach_ticks_T[0, 0]) == 1, "T1 breach ticks for v0 must be 1")
    _assert(int(sw.first_breach_tick_T[0, 0]) == 2, "First breach tick for T1 must be tick #2")
    #   - Other T levels should not be breached
    _assert(int(sw.breach_ticks_T[1:, 0].sum()) == 0, "Only T1 should breach in this setup")
    #   - Inactive variation v1 should have zero breaches and zero trades
    _assert(int(sw.trade_count[1]) == 0, "v1 must remain inactive (no entries)")
    _assert(int(sw.breach_ticks_T[:, 1].sum()) == 0, "v1 must not breach any T level")

    # Drawdown:
    _assert(float(sw.max_drawdown[0]) > 0.0, "Drawdown must be positive after a negative net exit")

    # dump_state / best-X / breach summary wiring:
    ds = sw.dump_state()
    _assert(abs(float(ds["best_x"]) - float(x_vals[0])) < 1e-12, "best_x must select the only-trading variation")
    _assert(int(ds["best_breach_ticks_total"]) == 1, "best_breach_ticks_total must equal 1 (only T1 breached once)")
    return CaseResult(name="buy", ok=True)


def test_sell_breach_drawdown_and_best_x() -> CaseResult:
    # Two SELL variations:
    #   v0 x=0.0001  => sell entry at 99.99, ST1 at 99.98
    #   v1 x=0.0010  => sell entry at 99.90, should stay inactive
    x_vals = np.array([0.0001, 0.0010], dtype=np.float64)
    sw = StockSweep(symbol="TEST_SELL", prev_close=100.0, x_values_np=x_vals)

    # Tick 1: enter only v0 (price == sell_below for v0)
    p1 = float(sw.sell_below[0])
    sw.on_price(p1, _ts(10, 0))
    _assert(sw.trade_count[0] == 0, "SELL tick1 should not exit")
    _assert(int(sw.breach_ticks_ST[:, 0].sum()) == 0, "No ST-level breach on entry tick")

    # Tick 2: hit ST1 for v0 (price == ST1 for v0)
    p2 = float(sw.st[0][0]) - 1e-9
    sw.on_price(p2, _ts(10, 1))
    _assert(int(sw.trade_count[0]) == 1, "SELL tick2 should exit exactly once for v0")

    # Breach counters:
    _assert(int(sw.breach_ticks_ST[0, 0]) == 1, "ST1 breach ticks for v0 must be 1")
    _assert(int(sw.first_breach_tick_ST[0, 0]) == 2, "First breach tick for ST1 must be tick #2")
    _assert(int(sw.breach_ticks_ST[1:, 0].sum()) == 0, "Only ST1 should breach in this setup")

    # Inactive variation v1 should have zero breaches and zero trades
    _assert(int(sw.trade_count[1]) == 0, "v1 must remain inactive (no entries)")
    _assert(int(sw.breach_ticks_ST[:, 1].sum()) == 0, "v1 must not breach any ST level")

    # Drawdown:
    _assert(float(sw.max_drawdown[0]) > 0.0, "Drawdown must be positive after a negative net exit")

    ds = sw.dump_state()
    _assert(abs(float(ds["best_x"]) - float(x_vals[0])) < 1e-12, "best_x must select the only-trading variation")
    _assert(int(ds["best_breach_ticks_total"]) == 1, "best_breach_ticks_total must equal 1 (only ST1 breached once)")
    return CaseResult(name="sell", ok=True)


def main() -> None:
    results: list[CaseResult] = []
    for fn in (test_buy_breach_drawdown_and_best_x, test_sell_breach_drawdown_and_best_x):
        try:
            results.append(fn())
        except Exception as e:
            results.append(CaseResult(name=fn.__name__, ok=False, details=str(e)))

    failed = [r for r in results if not r.ok]
    if failed:
        print("FAILED:")
        for r in failed:
            print(f"- {r.name}: {r.details}")
        raise SystemExit(1)

    print("OK: deterministic harness passed.")


if __name__ == "__main__":
    main()

