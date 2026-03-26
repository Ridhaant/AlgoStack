# ═══════════════════════════════════════════════════════════════════════
# © 2026 Ridhaant Ajoy Thackur. All rights reserved.
# AlgoStack™ is proprietary software. Unauthorised copying or distribution is prohibited.
# AlgoStack v9.0 | Author: Ridhaant Ajoy Thackur
# config.py — Centralized configuration, reads ALL settings from .env
# CURRENT_X_MULTIPLIER & CRYPTO_X_MULTIPLIER updated to 0.008 (was 0.008575)
# ═══════════════════════════════════════════════════════════════════════
"""
config.py -- Centralized Configuration for AlgoStack v9.0
==========================================================
Reads ALL secrets and settings from .env file.
No hardcoded tokens anywhere else.

Usage:
    from config import cfg
    token = cfg.TG_TOKEN
    comm_x = cfg.COMM_X["GOLD"]
    crypto_x = cfg.CRYPTO_X_MULTIPLIER
"""
from __future__ import annotations
import logging, os
from pathlib import Path

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

    # ── Equity Telegram bot ───────────────────────────────────────────────────
    TG_TOKEN: str = _opt("TELEGRAM_BOT_TOKEN",
                         "")
    TG_CHAT_IDS: list = [c.strip() for c in
        _opt("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]
    TG_CHAT_ID: str = TG_CHAT_IDS[0] if TG_CHAT_IDS else ""

    # ── Commodity Telegram bot ────────────────────────────────────────────────
    TG_COMMODITY_TOKEN: str = _opt("TELEGRAM_COMMODITY_BOT_TOKEN",
                                   "")
    _comm_ids_raw: str = _opt("TELEGRAM_COMMODITY_CHAT_IDS", "")
    TG_COMMODITY_CHATS: list = (
        [c.strip() for c in _comm_ids_raw.split(",") if c.strip()]
        if _comm_ids_raw
        else [c.strip() for c in _opt("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]
    )

    # ── Crypto Telegram bot ───────────────────────────────────────────────────
    TG_CRYPTO_TOKEN: str = _opt("TELEGRAM_CRYPTO_BOT_TOKEN", "")
    # Chat IDs for crypto bot — same as equity by default
    TG_CRYPTO_CHATS: list = [c.strip() for c in
        _opt("TELEGRAM_CRYPTO_CHAT_IDS", "").split(",") if c.strip()]

    # ── ngrok (env overrides; defaults for local unified dash / tunnels) ───
    NGROK_TOKEN_EQUITY: str    = _opt("NGROK_AUTHTOKEN_EQUITY",
                                      "")
    NGROK_TOKEN_2: str         = _opt("NGROK_AUTHTOKEN_2",   "")
    NGROK_TOKEN_3: str         = _opt("NGROK_AUTHTOKEN_3",   "")
    NGROK_API_KEY: str         = _opt("NGROK_API_KEY",
                                      "")
    NGROK_TOKEN_COMMODITY: str = _opt("NGROK_AUTHTOKEN_COMMODITY",
                                      "")

    # ── Ports (DO NOT CHANGE) ─────────────────────────────────────────────────
    DASH_PORT: int         = int(_opt("DASH_PORT",         "8050"))
    UNIFIED_DASH_PORT: int = int(_opt("UNIFIED_DASH_PORT", "8055"))
    XOPT_DASH_PORT: int    = int(_opt("XOPT_DASH_PORT",    "8063"))
    NEWS_DASH_PORT: int    = int(_opt("NEWS_DASH_PORT",    "8070"))

    # ── Equity trading parameters ─────────────────────────────────────────────
    CURRENT_X_MULTIPLIER: float = float(_opt("CURRENT_X_MULTIPLIER", "0.008"))
    CAPITAL_PER_TRADE: float    = float(_opt("CAPITAL_PER_TRADE",     "100000"))
    BROKERAGE_PER_SIDE: float   = float(_opt("BROKERAGE_PER_SIDE",    "10.0"))

    # ── ZMQ addresses (DO NOT CHANGE) ─────────────────────────────────────────
    ZMQ_PRICE_PUB: str = _opt("ZMQ_PRICE_PUB", "tcp://127.0.0.1:28081")
    ZMQ_PRICE_SUB: str = _opt("ZMQ_PRICE_SUB", "tcp://127.0.0.1:28081")

    # ── Commodity X multipliers (calibrated, read from .env with fallbacks) ───
    COMM_X: dict = {
        "GOLD":       float(_opt("COMMODITY_GOLD_X",       "0.003430")),
        "SILVER":     float(_opt("COMMODITY_SILVER_X",     "0.005145")),
        "NATURALGAS": float(_opt("COMMODITY_NATURALGAS_X", "0.000857")),
        "CRUDE":      float(_opt("COMMODITY_CRUDE_X",      "0.000602")),
        "COPPER":     float(_opt("COMMODITY_COPPER_X",     "0.004000")),
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
