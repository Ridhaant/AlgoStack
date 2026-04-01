from __future__ import annotations

import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, Dict, Tuple

log = logging.getLogger(__name__)


@dataclass
class SymbolRiskState:
    trades_today: int = 0
    consecutive_losses: int = 0
    cooldown_until: datetime | None = None


class TradeRiskController:
    """
    Shared, deterministic risk guardrails for all Best-X traders.
    """

    # Hardcoded defaults for autohealer-managed runtime.
    MAX_DAILY_DRAWDOWN_INR = 7_500.0
    MAX_TRADES_PER_SYMBOL_PER_DAY = 12
    CONSECUTIVE_LOSS_COOLDOWN_AFTER = 3
    COOLDOWN_MINUTES = 20

    def __init__(self) -> None:
        self._day = ""
        self._day_net = 0.0
        self._global_halt = False
        self._sym: Dict[str, SymbolRiskState] = {}

    def _rollover_if_needed(self, now: datetime) -> None:
        ds = now.strftime("%Y%m%d")
        if ds == self._day:
            return
        self._day = ds
        self._day_net = 0.0
        self._global_halt = False
        self._sym = {}

    def can_enter(self, symbol: str, now: datetime) -> bool:
        self._rollover_if_needed(now)
        if self._global_halt:
            return False
        s = self._sym.setdefault(str(symbol).upper(), SymbolRiskState())
        if s.trades_today >= self.MAX_TRADES_PER_SYMBOL_PER_DAY:
            return False
        if s.cooldown_until and now < s.cooldown_until:
            return False
        return True

    def register_exit(self, symbol: str, net_pnl_inr: float, now: datetime) -> None:
        self._rollover_if_needed(now)
        s = self._sym.setdefault(str(symbol).upper(), SymbolRiskState())
        s.trades_today += 1
        pnl = float(net_pnl_inr or 0.0)
        self._day_net += pnl
        if pnl < 0:
            s.consecutive_losses += 1
            if s.consecutive_losses >= self.CONSECUTIVE_LOSS_COOLDOWN_AFTER:
                s.cooldown_until = now + timedelta(minutes=self.COOLDOWN_MINUTES)
                s.consecutive_losses = 0
        else:
            s.consecutive_losses = 0
            s.cooldown_until = None
        if self._day_net <= -abs(self.MAX_DAILY_DRAWDOWN_INR):
            self._global_halt = True

    def snapshot(self, now: datetime) -> dict:
        self._rollover_if_needed(now)
        blocked = [k for k, v in self._sym.items() if v.cooldown_until and now < v.cooldown_until]
        return {
            "day_net_inr": round(self._day_net, 2),
            "global_halt": bool(self._global_halt),
            "cooldown_symbols": blocked[:50],
        }


# ── Pre-execution gates (broker executor / exchange rate limits) ────────────


def portfolio_notional_inr() -> float:
    """Rough portfolio size for per-symbol % caps (override via env or ``config``)."""
    try:
        from config import cfg

        v = float(getattr(cfg, "ALGOSTACK_EST_PORTFOLIO_INR", 0.0) or 0.0)
        if v > 0.0:
            return v
    except Exception as e:
        log.debug("config portfolio fallback: %s", e)
    try:
        return float(os.getenv("ALGOSTACK_EST_PORTFOLIO_INR", "3000000").strip() or 3_000_000.0)
    except Exception:
        return 3_000_000.0


def max_position_pct() -> float:
    try:
        from config import cfg

        return float(getattr(cfg, "MAX_POSITION_PCT", 0.05))
    except Exception:
        try:
            return float(os.getenv("MAX_POSITION_PCT", "0.05"))
        except Exception:
            return 0.05


def max_orders_per_second() -> int:
    try:
        from config import cfg

        return int(getattr(cfg, "MAX_ORDERS_PER_SECOND", 10))
    except Exception:
        try:
            return int(os.getenv("MAX_ORDERS_PER_SECOND", "10"))
        except Exception:
            return 10


def check_symbol_position_pct(
    *,
    current_open_inr: float,
    proposed_notion_inr: float,
    portfolio_inr: float,
    max_pct: float | None = None,
) -> Tuple[bool, str]:
    """
    Block new entry if symbol open + proposed would exceed ``max_pct`` of portfolio.

    Args:
        current_open_inr: Already-open notional for this symbol (same currency basis as proposed).
        proposed_notion_inr: Additional notional for this order.
        portfolio_inr: Portfolio denominator for the percentage cap.
        max_pct: Override (default: config / env).

    Returns:
        (allowed, empty message) or (False, reason).
    """
    pct = max_position_pct() if max_pct is None else float(max_pct)
    cap = float(portfolio_inr) * float(pct)
    nxt = float(current_open_inr) + float(proposed_notion_inr)
    if nxt > cap + 1e-6:
        return False, (
            f"symbol exposure {nxt:.0f} INR would exceed {pct:.0%} of portfolio "
            f"(cap {cap:.0f} INR)"
        )
    return True, ""


class OrderRateLimiter:
    """Sliding 1s window — exchange-style burst guard (default 10 orders/s)."""

    def __init__(self, max_per_second: int | None = None) -> None:
        self._max = max_orders_per_second() if max_per_second is None else int(max_per_second)
        self._timestamps: Deque[float] = deque()

    def allow(self) -> bool:
        now = time.monotonic()
        cutoff = now - 1.0
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
        if len(self._timestamps) >= self._max:
            return False
        self._timestamps.append(now)
        return True

