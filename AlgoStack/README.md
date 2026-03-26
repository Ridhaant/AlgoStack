# AlgoStack v9.0

**Algorithmic trading dashboard and signal engine for Indian markets (NSE Equity, MCX Commodity, Crypto).**

AlgoStack is a self-hosted Python application that runs on your local machine or a low-cost VPS. It ingests live prices, computes level-based entry/exit signals, sends alerts to Telegram, and presents everything through a Plotly-Dash web dashboard. No cloud subscription is required — you own and run every part of the stack.

> **⚠️ Disclaimer** — AlgoStack is a *research and alerting* tool. It does not place orders automatically. All trading decisions remain entirely with the user. Past signal performance does not guarantee future results. Use at your own risk.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running AlgoStack](#running-algostack)
7. [Dashboard Overview](#dashboard-overview)
8. [Telegram Setup](#telegram-setup)
9. [Remote Access (Tunnels)](#remote-access-tunnels)
10. [Docker](#docker)
11. [Health Check & Diagnostics](#health-check--diagnostics)
12. [Troubleshooting](#troubleshooting)
13. [Project Structure](#project-structure)
14. [Security Notes](#security-notes)

---

## Features

| Category | What it does |
|---|---|
| **Equity (NSE)** | Live price feed via yfinance, prev-close anchor levels, X-multiplier signal engine, EOD square-off |
| **Commodity (MCX)** | TradingView WebSocket feed with REST fallback, per-symbol X multipliers (Gold, Silver, Crude, NatGas, Copper) |
| **Crypto** | Binance WebSocket (CoinCap/CoinGecko fallback), 6-hour re-anchor, USDT + INR sizing |
| **Scanners** | Parallel sweep across hundreds of symbols; Best-X optimizer; GPU-accelerated sweep (optional) |
| **Dashboard** | Unified Plotly-Dash UI — live P&L, open positions, trade log, scanner table, news sentiment |
| **Alerts** | Telegram push notifications for entries, exits, EOD summary, feed health, tunnel URL |
| **Enterprise Auth** | Optional login wall with TOTP 2FA, password reset via email, Google OAuth |
| **Self-healing** | Autohealer watchdog restarts crashed processes; WiFi keepalive for uninterrupted feeds |
| **Remote access** | Cloudflare Quick Tunnel (zero config) or ngrok for reaching the dashboard from any device |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AlgoStack Process Tree                       │
│                                                                      │
│  start_all.sh / start_all.bat                                        │
│        │                                                             │
│        ├── Algofinal.py          ← Equity engine + ZMQ price pub     │
│        ├── commodity_engine.py   ← MCX feed + ZMQ price pub          │
│        ├── crypto_engine.py      ← Binance feed + ZMQ price pub      │
│        │                                                             │
│        ├── scanner1/2/3.py       ← Equity scanners (parallel)        │
│        ├── commodity_scanner1/2/3.py                                 │
│        ├── crypto_scanner1/2/3.py                                    │
│        │                                                             │
│        ├── unified_dash_v3.py    ← Main dashboard  :8055             │
│        ├── news_dashboard.py     ← News/sentiment   :8070            │
│        ├── alert_monitor.py      ← Feed health + EOD checks          │
│        ├── autohealer.py         ← Process watchdog                  │
│        └── wifi_keepalive.py     ← Network watchdog                  │
│                                                                      │
│  IPC:  ZMQ PUB/SUB  tcp://127.0.0.1:28081                           │
│  Data: levels/live_prices.json  +  trade_logs/*.jsonl               │
└──────────────────────────────────────────────────────────────────────┘
```

Engines write live prices and trade events to flat files. The dashboard reads those files on a fast/slow polling cycle — no shared database needed.

---

## Requirements

- **Python 3.10 or 3.11** (3.12 works but some numba wheels lag behind)
- **Windows 10/11** recommended for the `.bat` launchers; Linux and macOS work via `.sh`
- 4 GB RAM minimum (8 GB recommended when all scanners run)
- Optional: NVIDIA GPU with CUDA 12 for accelerated sweeps (`gpu_sweep.py`)
- Internet connection with access to `finance.yahoo.com`, `api.binance.com`, TradingView WebSocket

---

## Installation

### 1 — Clone or unzip the project

```bash
# If cloning from git:
git clone https://github.com/youruser/algostack.git
cd algostack

# Or unzip the release archive and cd into it:
unzip AlgoStack_updated.zip
cd AlgoStack
```

### 2 — Create and activate a virtual environment (recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

For GPU acceleration (optional, NVIDIA only):

```bash
pip install numba
pip install cupy-cuda12x     # adjust to your CUDA version
```

### 4 — Create your `.env` file

```bash
# Linux / macOS
cp .env.example .env

# Windows CMD
copy .env.example .env
```

Now open `.env` in any text editor and fill in your values — see [Configuration](#configuration) below.

### 5 — Run the health check

```bash
python health_check.py
```

All green ticks means you are ready to go.

---

## Configuration

All settings live in `.env`. **Never put real tokens in any `.py` file.**

### Minimum required setup

```ini
# At least one Telegram bot to receive alerts:
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
TELEGRAM_CHAT_IDS=123456789

# SMTP for password-reset emails (skip if not using enterprise auth):
ALGOSTACK_SMTP_USER=you@gmail.com
ALGOSTACK_SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx   # Gmail App Password
ALGOSTACK_MAIL_FROM=you@gmail.com
```

### Getting a Telegram Bot Token

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the token (looks like `1234567890:ABCdefGHI...`) into `TELEGRAM_BOT_TOKEN`
4. Message **@userinfobot** to find your personal chat ID
5. Send any message to your new bot, then paste your chat ID into `TELEGRAM_CHAT_IDS`

You can create separate bots for equity, commodity, and crypto, or reuse one bot for all three.

### Getting a Gmail App Password

1. Enable 2-Step Verification on your Google account
2. Visit **myaccount.google.com/apppasswords**
3. Generate a password for "Mail" → "Windows Computer" (or any label)
4. Paste the 16-character password into `ALGOSTACK_SMTP_PASSWORD`

> Your main Gmail password will **not** work here — Google blocks it.

### Optional APIs

| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys |
| `NEWS_API_KEY` | https://newsapi.org/register |
| `GNEWS_API_KEY` | https://gnews.io/ |
| `REDDIT_CLIENT_ID` + `SECRET` | https://www.reddit.com/prefs/apps (read-only script app) |
| `TWITTER_BEARER_TOKEN` | https://developer.twitter.com/ |
| `NGROK_AUTHTOKEN_EQUITY` | https://dashboard.ngrok.com/get-started/your-authtoken |
| `GOOGLE_OAUTH_CLIENT_ID` + `SECRET` | Google Cloud Console → APIs & Services → Credentials |

All optional keys default to empty; the feature that requires them will be disabled gracefully.

### Trading parameters

```ini
CURRENT_X_MULTIPLIER=0.008      # equity signal width as fraction of price
CAPITAL_PER_TRADE=100000        # INR per equity trade for sizing

CRYPTO_X_MULTIPLIER=0.008
CRYPTO_BUDGET_USDT=1065         # USDT per crypto leg
USDT_TO_INR=84.0                # set to 0 to auto-fetch live rate

COMMODITY_GOLD_X=0.003430
COMMODITY_SILVER_X=0.005145
COMMODITY_NATURALGAS_X=0.000857
COMMODITY_CRUDE_X=0.000602
COMMODITY_COPPER_X=0.004000
```

X multipliers control how wide the entry/exit levels are around the anchor price. See `TRADING_LOGIC.md` for a full explanation.

---

## Running AlgoStack

### Windows (recommended)

```bat
start_all.bat
```

This opens separate console windows for each process. To run with CPU affinity optimisation:

```bat
start_optimised.bat
```

### Linux / macOS

```bash
chmod +x start_all.sh
./start_all.sh
```

### Individual processes

You can launch components individually for development or debugging:

```bash
# Equity engine only
python Algofinal.py

# Dashboard only (requires live_prices.json to exist)
python dash_launcher.py

# Commodity engine
python commodity_engine.py

# Crypto engine
python crypto_engine.py

# Autohealer watchdog (monitors and restarts all others)
python autohealer.py
```

### Dashboard URL

Once running, open your browser at:

```
http://localhost:8055
```

The news dashboard is at `http://localhost:8070`.

---

## Dashboard Overview

The unified dashboard (`unified_dash_v3.py`) has four main tabs:

| Tab | Content |
|---|---|
| **Engine Lane** | Live P&L, open positions, and trade history sourced from the authoritative JSONL trade logs |
| **Research Lane** | Scanner output, X-optimizer results, and BestX backtests — simulation only, not live trades |
| **Crypto** | Crypto positions, P&L, and level table |
| **News** | Aggregated headlines with VADER sentiment scores |

The dashboard polls `levels/live_prices.json` every second for prices, and reloads trade JSONL files every 5 seconds for P&L.

---

## Telegram Setup

Each of the three bots (equity, commodity, crypto) can be the same bot or separate bots.

```ini
# .env — example with one shared bot for all markets:
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_CHAT_IDS=<your-chat-id>

# Commodity and crypto will fall back to the equity bot if their tokens are blank:
TELEGRAM_COMMODITY_BOT_TOKEN=
TELEGRAM_CRYPTO_BOT_TOKEN=
```

Alerts sent include: entry signals, exit signals (target/stop/retreat), EOD P&L summary, feed health warnings, and the dashboard tunnel URL when it changes.

---

## Remote Access (Tunnels)

AlgoStack can expose the dashboard to the internet so you can check it from your phone.

### Cloudflare Quick Tunnel (zero setup, recommended)

Set `ENABLE_TUNNEL=1` in `.env`. AlgoStack will start a `cloudflared` quick tunnel automatically on launch and send the HTTPS URL to Telegram. No account needed.

Install cloudflared if not present:
- **Windows**: Download from https://github.com/cloudflare/cloudflared/releases
- **Linux**: `curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg` then follow the Cloudflare docs
- **macOS**: `brew install cloudflare/cloudflare/cloudflared`

### ngrok (persistent subdomain)

1. Sign up at https://ngrok.com
2. Copy your authtoken from the dashboard
3. Add to `.env`:

```ini
NGROK_AUTHTOKEN_EQUITY=your-authtoken-here
```

See `NGROK_LOCAL.md` for named tunnel setup (keeps the same URL across restarts).

---

## Docker

A `Dockerfile` and `docker-compose.yml` are included for containerised deployment.

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

The container exposes ports `8055` (main dashboard) and `8070` (news dashboard).

Pass environment variables via a `.env` file in the same directory as `docker-compose.yml`, or via `docker-compose.yml`'s `environment:` section.

See `DEPLOY_RENDER_NO_CARD.md` for free-tier deployment on Render.com.

---

## Health Check & Diagnostics

```bash
# Pre-flight check before market open
python health_check.py

# Full diagnostics (checks dash, ports, ZMQ, data files)
python diagnose_dash.py
# or on Windows:
RUN_DIAGNOSE.bat
```

`alert_monitor.py` runs continuously alongside the engines and sends Telegram alerts if:
- Price feeds go stale (no update for > 60 seconds)
- The dashboard tunnel goes down
- Open positions remain after EOD square-off time
- P&L in the dashboard doesn't match the trade log

---

## Troubleshooting

**Dashboard shows stale prices / "No data"**
- Make sure `Algofinal.py` / `commodity_engine.py` / `crypto_engine.py` are running
- Check that `levels/live_prices.json` exists and was modified recently
- Run `python diagnose_dash.py` for a full diagnostic

**Telegram alerts not arriving**
- Confirm `TELEGRAM_BOT_TOKEN` is set in `.env`
- Make sure you have sent at least one message to your bot first (Telegram requires this)
- Double-check `TELEGRAM_CHAT_IDS` matches your chat ID from @userinfobot

**`ModuleNotFoundError`**
- Make sure your virtual environment is activated: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate`
- Re-run `pip install -r requirements.txt`

**Port already in use**
- Change `UNIFIED_DASH_PORT` (default 8055) or `NEWS_DASH_PORT` (default 8070) in `.env`

**ZMQ errors on startup**
- Engines start in parallel; scanners may log ZMQ connection errors for the first few seconds until the price publisher is ready — this is normal and resolves automatically

**High CPU usage**
- Use `start_optimised.bat` (Windows) to pin processes to specific cores via `process_affinity.py`
- Reduce the number of active scanners by commenting them out in `start_all.bat` / `start_all.sh`

---

## Project Structure

```
AlgoStack/
│
├── .env.example            ← Configuration template — copy to .env and fill in
├── .env                    ← Your local secrets (never commit)
├── .gitignore
├── requirements.txt
├── README.md               ← This file
│
├── ── Engines ─────────────────────────────────────────────────────
├── Algofinal.py            ← Equity price engine + signal generator
├── commodity_engine.py     ← MCX commodity engine
├── crypto_engine.py        ← Crypto engine (Binance WS)
│
├── ── Scanners ────────────────────────────────────────────────────
├── scanner1.py / scanner2.py / scanner3.py        ← Equity scanners
├── commodity_scanner1/2/3.py                       ← Commodity scanners
├── crypto_scanner1/2/3.py                          ← Crypto scanners
├── sweep_core.py           ← Shared sweep kernel
├── gpu_sweep.py            ← CUDA-accelerated sweep (optional)
├── best_x_trader.py        ← Best-X optimizer / backtester
│
├── ── Dashboard ───────────────────────────────────────────────────
├── unified_dash_v3.py      ← Main Plotly-Dash UI (port 8055)
├── news_dashboard.py       ← News & sentiment UI (port 8070)
├── dash_launcher.py        ← UTF-8 safe launcher for the dashboard
│
├── ── Services ────────────────────────────────────────────────────
├── config.py               ← Centralised config (reads from .env)
├── price_service.py        ← Shared price utilities
├── ipc_bus.py              ← ZMQ pub/sub helpers
├── tg_async.py             ← Async Telegram sender
├── alert_monitor.py        ← Feed health + EOD cross-check alerts
├── sentiment_analyzer.py   ← VADER sentiment wrapper
├── market_calendar.py      ← NSE / MCX / crypto session logic
│
├── ── Auth ────────────────────────────────────────────────────────
├── enterprise_auth.py      ← Flask-Login + TOTP 2FA + Google OAuth
│
├── ── Infra / Ops ─────────────────────────────────────────────────
├── autohealer.py           ← Process watchdog / auto-restart
├── wifi_keepalive.py       ← Network watchdog
├── log_manager.py          ← Log rotation and cleanup
├── health_check.py         ← Pre-flight diagnostic
├── diagnose_dash.py        ← Full diagnostic report
├── resource_plan.py        ← RAM / CPU usage planner
├── process_affinity.py     ← CPU core pinning (Windows)
├── deploy_free_vps.py      ← VPS deployment helper
│
├── ── Launchers ───────────────────────────────────────────────────
├── start_all.bat / start_all.sh          ← Start everything
├── start_optimised.bat                   ← Start with CPU affinity
├── clear_cache_and_run.bat               ← Wipe __pycache__ then start
├── RUN_DIAGNOSE.bat                      ← Run diagnose_dash.py
│
├── ── Container ───────────────────────────────────────────────────
├── Dockerfile
├── docker-compose.yml
├── render.yaml
│
└── ── Docs ────────────────────────────────────────────────────────
    ├── TRADING_LOGIC.md    ← Signal and level generation explained
    ├── ENTERPRISE_AUTH.md  ← Auth system setup
    ├── NGROK_LOCAL.md      ← Persistent ngrok tunnel setup
    ├── DEPLOY_RENDER_NO_CARD.md
    ├── DEPLOY_ALWAYS_ON.md
    ├── RENDER_MEMORY.md
    └── RENDER_SETUP_STEPS.md
```

---

## Security Notes

- **Never hardcode tokens in `.py` files.** All secrets must live in `.env`, which is excluded from git by `.gitignore`.
- **Rotate any credentials that were previously committed** — once a secret appears in git history it should be considered compromised, even after deletion.
- The enterprise auth system (`ENTERPRISE_AUTH.md`) adds a login wall to the dashboard. Enable it before exposing the dashboard to the internet.
- Cloudflare Quick Tunnels generate a new random URL on every restart. Use a named tunnel (or ngrok) if you need a stable URL.
- The dashboard binds to `0.0.0.0` by default. On a shared machine, change the host binding in `unified_dash_v3.py` to `127.0.0.1` if you are using a tunnel.

---

## Credits

**Author:** Ridhaant Ajoy Thackur  
© 2026 Ridhaant Ajoy Thackur. All rights reserved.  
AlgoStack™ is proprietary software. Unauthorised copying or distribution is prohibited.
