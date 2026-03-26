# AlgoStack
AlgoStack — Production Multi-Process Trading Platform

29k+ lines | 16 concurrent processes | GPU accelerated | self-healing infrastructure
<div align="center">

```
 █████╗ ██╗      ██████╗  ██████╗ ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗██║     ██╔════╝ ██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
███████║██║     ██║  ███╗██║   ██║███████╗   ██║   ███████║██║     █████╔╝ 
██╔══██║██║     ██║   ██║██║   ██║╚════██║   ██║   ██╔══██║██║     ██╔═██╗ 
██║  ██║███████╗╚██████╔╝╚██████╔╝███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
```

### Algorithmic Signal Engine & Live Trading Dashboard for Indian Markets

**NSE Equity · MCX Commodity · Crypto (Binance)**

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Plotly Dash](https://img.shields.io/badge/Plotly_Dash-2.17+-119DFF?style=for-the-badge&logo=plotly&logoColor=white)](https://dash.plotly.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![ZeroMQ](https://img.shields.io/badge/ZeroMQ-IPC_Bus-DF0000?style=for-the-badge&logo=zeromq&logoColor=white)](https://zeromq.org)
[![CUDA](https://img.shields.io/badge/NVIDIA_CUDA-Optional_GPU-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/License-Proprietary-FF4B4B?style=for-the-badge)](./LICENSE)

<br/>

> **"From raw price feed to actionable signal in milliseconds — fully self-hosted, zero cloud subscriptions."**

<br/>

[📸 Screenshots](#-dashboard-overview) · [⚡ Quickstart](#-installation) · [🏗 Architecture](#-architecture) · [🔧 Configuration](#-configuration) · [🐳 Docker](#-docker)

</div>

---

## ✦ What is AlgoStack?

**AlgoStack v9.0** is a production-grade, self-hosted algorithmic research and alerting platform purpose-built for **Indian retail and professional traders**. It ingests live price data across three asset classes, computes level-based entry/exit signals using a proprietary **X-Multiplier engine**, delivers instant **Telegram push alerts**, and surfaces everything through a rich **Plotly-Dash web dashboard** — all running on your own machine or a ₹500/month VPS.

No SaaS fees. No data vendor lock-in. You own every line of it.

```
┌────────────────────────────────────────────────────────────────────────┐
│  Live Prices → Signal Engine → ZMQ Bus → Scanners + Dashboard + Alerts │
└────────────────────────────────────────────────────────────────────────┘
```

> ⚠️ **Disclaimer** — AlgoStack is a *research and alerting* tool. It does **not** place orders automatically. All trading decisions remain entirely with the user. Past signal performance does not guarantee future results.

---

## ✦ Feature Highlights

<table>
<tr>
<td width="50%">

### 📈 Multi-Market Signal Engine
- **NSE Equity** — yfinance live feed, prev-close anchor, EOD auto square-off
- **MCX Commodity** — TradingView WebSocket + REST fallback; per-symbol X multipliers (Gold, Silver, Crude, NatGas, Copper)
- **Crypto** — Binance WebSocket (CoinCap / CoinGecko fallback), 6-hour re-anchor, USDT + INR sizing

</td>
<td width="50%">

### 🔍 Parallel Symbol Scanners
- 9 concurrent scanners (3 equity + 3 commodity + 3 crypto)
- Shared **sweep kernel** (`sweep_core.py`) with **Numba JIT** (5–10× speedup)
- **GPU-accelerated sweep** via CuPy on NVIDIA CUDA 12 (optional)
- **BestX Optimizer** — backtests optimal X-multiplier per symbol

</td>
</tr>
<tr>
<td width="50%">

### 🖥 Unified Live Dashboard
- **Engine Lane** — live P&L, open positions, trade history from JSONL logs
- **Research Lane** — scanner output, BestX backtest results
- **Crypto Lane** — crypto positions, level table, P&L
- **News Lane** — aggregated headlines with VADER sentiment scores
- Sub-second price polling via flat-file IPC (no DB required)

</td>
<td width="50%">

### 🔔 Intelligent Alert System
- Telegram push for entries, exits, EOD summaries, feed health
- `alert_monitor.py` continuously cross-checks live prices vs dashboard
- Detects stale feeds, dangling positions after market close, P&L drift
- Sends tunnel URL to Telegram every time it changes

</td>
</tr>
<tr>
<td width="50%">

### 🛡 Enterprise Auth (Optional)
- Flask-Login session management
- **TOTP 2FA** via PyOTP (Google Authenticator compatible)
- Password reset via Gmail App Password / SMTP
- **Google OAuth** single sign-on
- Enable with a single env var: `ALGOSTACK_AUTH_ENABLED=1`

</td>
<td width="50%">

### ⚙️ Self-Healing Infrastructure
- `autohealer.py` watchdog auto-restarts any crashed process
- `wifi_keepalive.py` network watchdog prevents silent feed drops
- `log_manager.py` rotates and purges stale logs automatically
- `process_affinity.py` pins processes to CPU cores (Windows)
- `resource_plan.py` models RAM/CPU usage before launch

</td>
</tr>
</table>

---

## ✦ Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                       AlgoStack Process Tree                           │
│                                                                        │
│  start_all.sh / start_all.bat                                          │
│        │                                                               │
│        ├─── Algofinal.py           ←  Equity engine  + ZMQ price pub  │
│        ├─── commodity_engine.py    ←  MCX feed       + ZMQ price pub  │
│        ├─── crypto_engine.py       ←  Binance WS     + ZMQ price pub  │
│        │                                                               │
│        ├─── scanner1/2/3.py        ←  Equity scanners (parallel)      │
│        ├─── commodity_scanner1/2/3.py                                  │
│        ├─── crypto_scanner1/2/3.py                                     │
│        │                                                               │
│        ├─── unified_dash_v3.py     ←  Main dashboard     :8055        │
│        ├─── news_dashboard.py      ←  News / sentiment   :8070        │
│        ├─── alert_monitor.py       ←  Feed health + EOD checks        │
│        ├─── autohealer.py          ←  Process watchdog                │
│        └─── wifi_keepalive.py      ←  Network watchdog                │
│                                                                        │
│  IPC :  ZMQ PUB/SUB   tcp://127.0.0.1:28081                           │
│  Data:  levels/live_prices.json  +  trade_logs/*.jsonl                │
└────────────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Zero shared database** — engines write flat JSON/JSONL; dashboard polls on a fast/slow cycle
- **ZMQ PUB/SUB** for low-latency inter-process price distribution
- **Flat-file IPC** keeps the stack deployable on the cheapest VPS with no DB daemon
- **Modular process tree** — any single component can crash and restart without taking down the rest

---

## ✦ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10 / 3.11 |
| **Dashboard** | Plotly Dash 2.17+, Dash Bootstrap Components |
| **Data Feeds** | yfinance (NSE), Binance WebSocket, TradingView WebSocket |
| **IPC** | ZeroMQ PUB/SUB (`pyzmq`) |
| **Signal Computation** | NumPy, Pandas, Numba JIT, CuPy (optional CUDA) |
| **Alerts** | Telegram Bot API (async via `tg_async.py`) |
| **Auth** | Flask-Login, PyOTP (TOTP 2FA), Google OAuth |
| **Sentiment** | VADER (`vaderSentiment`), NewsAPI, GNews, Reddit (PRAW) |
| **Tunnels** | Cloudflare Quick Tunnel (`cloudflared`), ngrok |
| **Container** | Docker + Docker Compose, Render.com deployment |
| **Config** | `python-dotenv`, centralised `config.py` |
| **Logging** | Loguru, Rich |

---

## ✦ Installation

### Prerequisites

- Python **3.10** or **3.11**
- 4 GB RAM minimum (8 GB recommended with all scanners)
- Internet access to `finance.yahoo.com`, `api.binance.com`, TradingView WebSocket
- *(Optional)* NVIDIA GPU with CUDA 12 for accelerated sweeps

### 1 — Clone the repository

```bash
git clone https://github.com/your-username/algostack.git
cd algostack
```

### 2 — Create a virtual environment

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

For GPU acceleration (NVIDIA only):

```bash
pip install numba cupy-cuda12x   # adjust CUDA version as needed
```

### 4 — Configure environment

```bash
cp .env.example .env   # Linux/macOS
copy .env.example .env # Windows
```

Open `.env` and set at minimum:

```ini
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_CHAT_IDS=<your-chat-id>
```

See [Configuration](#-configuration) for the full reference.

### 5 — Run pre-flight health check

```bash
python health_check.py
```

All green ✅ ticks → you're ready.

### 6 — Launch

```bash
# Windows
start_all.bat

# Linux / macOS
chmod +x start_all.sh && ./start_all.sh
```

Open **http://localhost:8055** in your browser.

---

## ✦ Configuration

All settings live in `.env`. **Never hardcode secrets in any `.py` file.**

### Minimum required

```ini
# Telegram (required for alerts)
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
TELEGRAM_CHAT_IDS=123456789

# SMTP for enterprise auth password reset (optional)
ALGOSTACK_SMTP_USER=you@gmail.com
ALGOSTACK_SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
ALGOSTACK_MAIL_FROM=you@gmail.com
```

### Trading parameters

```ini
CURRENT_X_MULTIPLIER=0.008       # equity signal width as fraction of price
CAPITAL_PER_TRADE=100000         # INR per equity trade

CRYPTO_X_MULTIPLIER=0.008
CRYPTO_BUDGET_USDT=1065
USDT_TO_INR=84.0                 # set 0 to auto-fetch live rate

COMMODITY_GOLD_X=0.003430
COMMODITY_SILVER_X=0.005145
COMMODITY_NATURALGAS_X=0.000857
COMMODITY_CRUDE_X=0.000602
COMMODITY_COPPER_X=0.004000
```

### Optional API keys

| Key | Purpose | Where to get |
|---|---|---|
| `GEMINI_API_KEY` | AI-powered analysis | [aistudio.google.com](https://aistudio.google.com/apikey) |
| `ANTHROPIC_API_KEY` | Claude integration | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `NEWS_API_KEY` | Richer news feed | [newsapi.org](https://newsapi.org/register) |
| `GNEWS_API_KEY` | GNews headlines | [gnews.io](https://gnews.io/) |
| `REDDIT_CLIENT_ID` / `SECRET` | Reddit sentiment | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) |
| `TWITTER_BEARER_TOKEN` | Twitter sentiment | [developer.twitter.com](https://developer.twitter.com/) |
| `NGROK_AUTHTOKEN_EQUITY` | Persistent tunnel | [dashboard.ngrok.com](https://dashboard.ngrok.com/) |
| `GOOGLE_OAUTH_CLIENT_ID` / `SECRET` | Google SSO | Google Cloud Console |

All optional keys gracefully disable their feature when absent.

---

## ✦ Dashboard Overview

The unified dashboard (`unified_dash_v3.py`, port **:8055**) has four tabs:

| Tab | Content |
|---|---|
| **Engine Lane** | Live P&L · Open positions · Full trade history (from authoritative JSONL logs) |
| **Research Lane** | Scanner sweep output · X-Optimizer results · BestX backtests |
| **Crypto Lane** | Crypto positions · Level table · USDT & INR P&L |
| **News Lane** | Aggregated headlines · VADER sentiment scores · Source breakdown |

The news dashboard (`news_dashboard.py`, port **:8070**) runs as a separate process and aggregates from NewsAPI, GNews, Reddit, and Twitter.

---

## ✦ Telegram Alerts

AlgoStack sends structured push notifications for every significant event:

- ✅ **Entry signal** — symbol, direction, price, levels
- 🎯 **Exit signal** — target hit / stop hit / retreat
- 📊 **EOD summary** — daily P&L across all three asset classes
- ⚠️ **Feed health warning** — if any price feed goes stale > 60 seconds
- 🔗 **Tunnel URL** — sent automatically each time the dashboard URL changes

You can use a single bot for all three markets or configure separate bots per asset class.

---

## ✦ Remote Access

### Cloudflare Quick Tunnel *(zero-config, recommended)*

```ini
# .env
ENABLE_TUNNEL=1
```

AlgoStack starts a `cloudflared` quick tunnel on launch and sends the HTTPS URL to Telegram. No Cloudflare account needed.

### ngrok *(persistent subdomain)*

```ini
NGROK_AUTHTOKEN_EQUITY=your-authtoken
```

See `NGROK_LOCAL.md` for named tunnel setup that preserves the same URL across restarts.

---

## ✦ Docker

```bash
# Build and start all services
docker-compose up --build

# Detached (background)
docker-compose up -d

# Stream logs
docker-compose logs -f
```

Exposed ports: **8055** (main dashboard) · **8070** (news dashboard)

Pass secrets via a `.env` file alongside `docker-compose.yml`. See `DEPLOY_RENDER_NO_CARD.md` for free-tier deployment on **Render.com**.

---

## ✦ Health Check & Diagnostics

```bash
# Pre-flight check — run before market open
python health_check.py

# Full diagnostic (dash, ports, ZMQ, data files)
python diagnose_dash.py

# Windows shortcut
RUN_DIAGNOSE.bat
```

`alert_monitor.py` runs continuously and fires Telegram alerts if:
- Any price feed is stale for > 60 seconds
- The dashboard tunnel goes down
- Open positions remain after EOD square-off time
- P&L in the dashboard drifts from the trade log

---

## ✦ Project Structure

```
AlgoStack/
│
├── .env.example                  ← Config template — copy to .env
├── requirements.txt
│
├── ── Engines ────────────────────────────────────────────────────────
├── Algofinal.py                  ← Equity price engine + signal generator
├── commodity_engine.py           ← MCX commodity engine
├── crypto_engine.py              ← Crypto engine (Binance WebSocket)
│
├── ── Scanners ───────────────────────────────────────────────────────
├── scanner1.py / scanner2.py / scanner3.py
├── commodity_scanner1/2/3.py
├── crypto_scanner1/2/3.py
├── sweep_core.py                 ← Shared Numba-JIT sweep kernel
├── gpu_sweep.py                  ← CUDA-accelerated sweep (optional)
├── best_x_trader.py              ← BestX optimizer / backtester
│
├── ── Dashboard ──────────────────────────────────────────────────────
├── unified_dash_v3.py            ← Main Plotly-Dash UI (port 8055)
├── news_dashboard.py             ← News & sentiment UI (port 8070)
│
├── ── Services ───────────────────────────────────────────────────────
├── config.py                     ← Centralised config (reads .env)
├── price_service.py              ← Shared price utilities
├── ipc_bus.py                    ← ZMQ pub/sub helpers
├── tg_async.py                   ← Async Telegram sender
├── alert_monitor.py              ← Feed health + EOD cross-checks
├── sentiment_analyzer.py         ← VADER sentiment wrapper
├── market_calendar.py            ← NSE / MCX / crypto session logic
│
├── ── Auth ───────────────────────────────────────────────────────────
├── enterprise_auth.py            ← Flask-Login + TOTP 2FA + Google OAuth
│
├── ── Infra ──────────────────────────────────────────────────────────
├── autohealer.py                 ← Process watchdog / auto-restart
├── wifi_keepalive.py             ← Network watchdog
├── log_manager.py                ← Log rotation and cleanup
├── health_check.py               ← Pre-flight diagnostic
├── diagnose_dash.py              ← Full diagnostic report
├── resource_plan.py              ← RAM/CPU usage planner
├── process_affinity.py           ← CPU core pinning (Windows)
│
├── ── Launchers ──────────────────────────────────────────────────────
├── start_all.bat / start_all.sh  ← Start everything
├── start_optimised.bat           ← Start with CPU affinity
│
├── ── Container ──────────────────────────────────────────────────────
├── Dockerfile
├── docker-compose.yml
├── render.yaml
│
└── ── Docs ───────────────────────────────────────────────────────────
    ├── TRADING_LOGIC.md          ← Signal and level generation explained
    ├── ENTERPRISE_AUTH.md        ← Auth system setup
    ├── NGROK_LOCAL.md
    └── DEPLOY_*.md
```

---

## ✦ Troubleshooting

<details>
<summary><strong>Dashboard shows stale prices / "No data"</strong></summary>

- Confirm `Algofinal.py`, `commodity_engine.py`, and `crypto_engine.py` are running
- Check that `levels/live_prices.json` exists and was updated recently
- Run `python diagnose_dash.py` for a full diagnostic report

</details>

<details>
<summary><strong>Telegram alerts not arriving</strong></summary>

- Confirm `TELEGRAM_BOT_TOKEN` is set in `.env`
- You must send at least one message to the bot first (Telegram requires this handshake)
- Verify `TELEGRAM_CHAT_IDS` matches your ID from @userinfobot

</details>

<details>
<summary><strong>ModuleNotFoundError on startup</strong></summary>

- Activate your virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate`
- Re-run `pip install -r requirements.txt`

</details>

<details>
<summary><strong>Port already in use</strong></summary>

- Change `UNIFIED_DASH_PORT` (default 8055) or `NEWS_DASH_PORT` (default 8070) in `.env`

</details>

<details>
<summary><strong>ZMQ connection errors on startup</strong></summary>

- Engines start in parallel; scanners may log ZMQ errors for the first few seconds until the price publisher is ready — **this is normal** and resolves automatically

</details>

<details>
<summary><strong>High CPU usage</strong></summary>

- Use `start_optimised.bat` (Windows) to pin processes to specific cores
- Reduce active scanners by commenting them out in `start_all.bat` / `start_all.sh`

</details>

---

## ✦ Security Notes

- **Never hardcode tokens in `.py` files.** All secrets must live in `.env`, which is excluded by `.gitignore`
- **Rotate any credentials that were ever committed** — once a secret is in git history it is compromised, even after deletion
- Enable enterprise auth (`ALGOSTACK_AUTH_ENABLED=1`) before exposing the dashboard to the internet
- Cloudflare Quick Tunnels generate a new URL on every restart; use a named tunnel for a stable URL
- The dashboard binds to `0.0.0.0` by default; change to `127.0.0.1` in `unified_dash_v3.py` on shared machines when using a tunnel

---

## ✦ Roadmap

- [ ] Order routing integration (Zerodha Kite API)
- [ ] Strategy backtesting framework with walk-forward validation
- [ ] Mobile-optimised PWA dashboard skin
- [ ] Multi-user portfolio aggregation
- [ ] Options chain integration (NSE)

---

<div align="center">

---

**Built with precision by [Ridhaant Ajoy Thackur](https://github.com/your-username)**

© 2026 Ridhaant Ajoy Thackur. All rights reserved.
AlgoStack™ is proprietary software. Unauthorised copying or distribution is prohibited.

*If this project helped you, consider leaving a ⭐*

</div>
