# ═══════════════════════════════════════════════════════════════════════
# © 2026 Ridhaant Ajoy Thackur. All rights reserved.
# AlgoStack™ is proprietary software. Unauthorised copying or distribution is prohibited.
# AlgoStack v9.0 | Author: Ridhaant Ajoy Thackur
# config.py — Centralized configuration, reads ALL settings from .env
# ═══════════════════════════════════════════════════════════════════════
"""
config.py -- Centralized Configuration for AlgoStack v9.0
==========================================================
Loads .env when present; otherwise uses built-in defaults so the stack can run
with **python autohealer.py only** — no manual env setup (per deployment model).

Do not strip default fallbacks here: they exist for automatic, zero-intervention
operation. Production deployments may override any value via environment variables.
"""
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Optional

log = logging.getLogger("config")

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
        log.debug("Loaded .env from %s", _env_path)
    else:
        log.debug(".env not found -- using environment variables")
except ImportError:
    log.debug("python-dotenv not installed -- reading env vars directly")


def _req(key: str) -> str:
    v = os.environ.get(key, "").strip()
    if not v:
        raise EnvironmentError(f"Required env var '{key}' not set. Copy .env.template to .env")
    return v


def _opt(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


class _Config:
    """All AlgoStack v9.0 configuration in one place."""

    # ── Equity Telegram bot (set in .env — never commit tokens) ───────────────
    TG_TOKEN: str = _opt("TELEGRAM_BOT_TOKEN", "")
    TG_CHAT_IDS: list = [c.strip() for c in _opt("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]
    TG_CHAT_ID: str = TG_CHAT_IDS[0] if TG_CHAT_IDS else ""

    # ── Commodity Telegram bot ────────────────────────────────────────────────
    TG_COMMODITY_TOKEN: str = _opt("TELEGRAM_COMMODITY_BOT_TOKEN", "")
    _comm_ids_raw: str = _opt("TELEGRAM_COMMODITY_CHAT_IDS", "")
    TG_COMMODITY_CHATS: list = (
        [c.strip() for c in _comm_ids_raw.split(",") if c.strip()]
        if _comm_ids_raw
        else list(TG_CHAT_IDS)
    )

    # ── Crypto Telegram bot ───────────────────────────────────────────────────
    TG_CRYPTO_TOKEN: str = _opt("TELEGRAM_CRYPTO_BOT_TOKEN", "")
    TG_CRYPTO_CHATS: list = [c.strip() for c in _opt("TELEGRAM_CRYPTO_CHAT_IDS", "").split(",") if c.strip()] or list(
        TG_CHAT_IDS
    )

    # ── ngrok / tunnel API (optional — from environment only) ─────────────────
    NGROK_TOKEN_EQUITY: str    = _opt("NGROK_AUTHTOKEN_EQUITY", "")
    NGROK_TOKEN_2: str         = _opt("NGROK_AUTHTOKEN_2", "")
    NGROK_TOKEN_3: str         = _opt("NGROK_AUTHTOKEN_3", "")
    NGROK_API_KEY: str         = _opt("NGROK_API_KEY", "")
    NGROK_TOKEN_COMMODITY: str = _opt("NGROK_AUTHTOKEN_COMMODITY", "")

    # ── Ports (DO NOT CHANGE) ─────────────────────────────────────────────────
    DASH_PORT: int         = int(_opt("DASH_PORT",         "8050"))
    UNIFIED_DASH_PORT: int = int(_opt("UNIFIED_DASH_PORT", "8055"))
    XOPT_DASH_PORT: int    = int(_opt("XOPT_DASH_PORT",    "8063"))
    NEWS_DASH_PORT: int    = int(_opt("NEWS_DASH_PORT",    "8070"))

    # ── Equity trading parameters ─────────────────────────────────────────────
    CURRENT_X_MULTIPLIER: float = float(_opt("CURRENT_X_MULTIPLIER", "0.008"))
    CAPITAL_PER_TRADE: float    = float(_opt("CAPITAL_PER_TRADE",     "100000"))
    BROKERAGE_PER_SIDE: float   = float(_opt("BROKERAGE_PER_SIDE",    "10.0"))
    BROKER_SLIPPAGE_MODEL: str = _opt("BROKER_SLIPPAGE_MODEL", "none")  # none | realistic
    BROKER_RECORD_DB: str = _opt("BROKER_RECORD_DB", "1")  # 0 disables paper → trade_store mirroring
    BROKER: str = _opt("BROKER", "paper")  # paper | kite | zerodha | upstox | angel
    MAX_POSITION_PCT: float = float(_opt("MAX_POSITION_PCT", "0.05"))
    MAX_ORDERS_PER_SECOND: int = int(_opt("MAX_ORDERS_PER_SECOND", "10"))
    ALGOSTACK_EST_PORTFOLIO_INR: float = float(_opt("ALGOSTACK_EST_PORTFOLIO_INR", "3000000"))

    # ── ZMQ addresses (DO NOT CHANGE) ─────────────────────────────────────────
    ZMQ_PRICE_PUB: str = _opt("ZMQ_PRICE_PUB", "tcp://127.0.0.1:28081")
    ZMQ_PRICE_SUB: str = _opt("ZMQ_PRICE_SUB", "tcp://127.0.0.1:28081")

    # ── Commodity X multipliers (calibrated, read from .env with fallbacks) ───
    COMM_X: dict = {
        "GOLD":       float(_opt("COMMODITY_GOLD_X",       "0.008")),
        "SILVER":     float(_opt("COMMODITY_SILVER_X",     "0.008")),
        "NATURALGAS": float(_opt("COMMODITY_NATURALGAS_X", "0.008")),
        "CRUDE":      float(_opt("COMMODITY_CRUDE_X",      "0.008")),
        "COPPER":     float(_opt("COMMODITY_COPPER_X",     "0.008")),
    }

    # ── Crypto configuration ───────────────────────────────────────────────────
    CRYPTO_X_MULTIPLIER: float  = float(_opt("CRYPTO_X_MULTIPLIER",  "0.008"))
    CRYPTO_BUDGET_INR: float    = float(_opt("CRYPTO_BUDGET_INR",     "100000"))
    # USDT notional per crypto leg (preferred for sizing; avoids INR→USDT float loss)
    CRYPTO_BUDGET_USDT: float   = float(_opt("CRYPTO_BUDGET_USDT",    "1065"))
    USDT_TO_INR: float          = float(_opt("USDT_TO_INR",           "0")) or 84.0  # Set USDT_TO_INR in .env to override; falls back to 84.0
    CRYPTO_BROKERAGE_PCT: float = float(_opt("CRYPTO_BROKERAGE_PCT",  "0.001"))
    ENABLE_CRYPTO: bool         = _opt("ENABLE_CRYPTO", "1") == "1"

    # ── News & Sentiment APIs (optional) ─────────────────────────────────────
    NEWS_API_KEY: str         = _opt("NEWS_API_KEY",         "")
    GNEWS_API_KEY: str        = _opt("GNEWS_API_KEY",        "")
    REDDIT_CLIENT_ID: str     = _opt("REDDIT_CLIENT_ID",     "")
    REDDIT_CLIENT_SECRET: str = _opt("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str    = _opt("REDDIT_USER_AGENT",    "AlgoStack/9.0")
    TWITTER_BEARER_TOKEN: str = _opt("TWITTER_BEARER_TOKEN", "")

    # ── AI APIs ───────────────────────────────────────────────────────────────
    GEMINI_API_KEY:    str = _opt("GEMINI_API_KEY",    "")
    ANTHROPIC_API_KEY: str = _opt("ANTHROPIC_API_KEY", "")

    # ── Feature flags ─────────────────────────────────────────────────────────
    ENABLE_NEWS_DASHBOARD: bool = _opt("ENABLE_NEWS_DASHBOARD", "1") == "1"
    ENABLE_TUNNEL: bool         = _opt("ENABLE_TUNNEL",         "1") == "1"
    SKIP_WEEKEND_CHECK: bool    = _opt("SKIP_WEEKEND_CHECK",    "0") == "1"
    LOG_LEVEL: str              = _opt("LOG_LEVEL", "INFO").upper()

    # ── Roadmap / infra (optional — empty = legacy file/SQLite behaviour) ─────
    ENVIRONMENT: str = _opt("ENVIRONMENT", "development").lower()
    SECRET_BACKEND: str = _opt("SECRET_BACKEND", "env").lower()
    DATABASE_URL: str = _opt("DATABASE_URL", "")
    REDIS_URL: str = _opt("REDIS_URL", "")
    IPC_BACKEND: str = _opt("IPC_BACKEND", "zmq").lower()
    DB_POOL_MIN: int = int(_opt("DB_POOL_MIN", "1"))
    DB_POOL_MAX: int = int(_opt("DB_POOL_MAX", "10"))
    API_PORT: int = int(_opt("API_PORT", "8080"))
    API_JWT_EXPIRE_MINUTES: int = int(_opt("API_JWT_EXPIRE_MINUTES", "15"))
    API_RATE_LIMIT: str = _opt("API_RATE_LIMIT", "120/minute")
    SHOW_API_DOCS: str = _opt("SHOW_API_DOCS", "1")
    ALGOSTACK_PLATFORM_DB: str = _opt(
        "ALGOSTACK_PLATFORM_DB",
        str(Path(__file__).resolve().parent / "data" / "algostack_platform.db"),
    )

    def __repr__(self) -> str:
        return (
            f"Config(equity_x={self.CURRENT_X_MULTIPLIER}, "
            f"crypto_x={self.CRYPTO_X_MULTIPLIER}, "
            f"usdt_inr={self.USDT_TO_INR}, "
            f"capital={self.CAPITAL_PER_TRADE}, "
            f"tg_equity={bool(self.TG_TOKEN)}, "
            f"tg_commodity={bool(self.TG_COMMODITY_TOKEN)}, "
            f"tg_crypto={bool(self.TG_CRYPTO_TOKEN)})"
        )


cfg = _Config()


class SecretManager:
    """Resolve secrets by backend name. Default ``env`` reads os.environ (same as _opt).

    Backends ``aws_ssm``, ``hashicorp_vault``, and ``gcp_secret_manager`` are reserved
    for future wiring; until then they fall back to environment variables so existing
    deployments keep working without extra services.
    """

    def __init__(self, backend: Optional[str] = None) -> None:
        self.backend = (backend or cfg.SECRET_BACKEND or "env").lower()

    def get(self, key: str, default: str = "") -> str:
        """Return secret *key*, using ``default`` when unset (autohealer-friendly)."""
        if self.backend in ("aws_ssm", "hashicorp_vault", "gcp_secret_manager"):
            log.debug("Secret backend %s not implemented — using env for %s", self.backend, key)
        return _opt(key, default)


secret_manager = SecretManager()
