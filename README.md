<div align="center">

```
 █████╗ ██╗      ██████╗  ██████╗ ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗██║     ██╔════╝ ██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
███████║██║     ██║  ███╗██║   ██║███████╗   ██║   ███████║██║     █████╔╝
██╔══██║██║     ██║   ██║██║   ██║╚════██║   ██║   ██╔══██║██║     ██╔═██╗
██║  ██║███████╗╚██████╔╝╚██████╔╝███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
```

# AlgoStack v10.7

**Production Multi-Process Algorithmic Trading & Research Platform**

*30,595 lines · 16 concurrent processes · GPU accelerated · self-healing infrastructure*

**NSE Equity · MCX Commodity · Crypto (Binance)**

[![Python](https://img.shields.io/badge/Python-3.10%20|%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Plotly Dash](https://img.shields.io/badge/Plotly_Dash-2.17+-119DFF?style=for-the-badge&logo=plotly&logoColor=white)](https://dash.plotly.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![ZeroMQ](https://img.shields.io/badge/ZeroMQ-IPC_Bus-DF0000?style=for-the-badge&logo=zeromq&logoColor=white)](https://zeromq.org)
[![CUDA](https://img.shields.io/badge/NVIDIA_CUDA-Optional_GPU-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/License-Proprietary-FF4B4B?style=for-the-badge)](./LICENSE)

<br/>

> **"From raw price feed to actionable signal in milliseconds — fully self-hosted, zero cloud subscriptions."**

<br/>

[📸 Dashboard](#-dashboard-overview) · [⚡ Quickstart](#-installation) · [🏗 Architecture](#-architecture) · [🔧 Configuration](#-configuration) · [🐳 Docker](#-docker) · [👤 Author](#-author)

</div>

---

## ✦ What is AlgoStack?

**AlgoStack v10.7** is a production-grade, self-hosted algorithmic research and alerting platform purpose-built for **Indian retail and professional traders**. It ingests live price data across three asset classes, computes level-based entry/exit signals using a proprietary **X-Multiplier engine**, delivers instant **Telegram push alerts**, and surfaces everything through a rich **Plotly-Dash web dashboard** — all running on your own machine or a ₹500/month VPS.

No SaaS fees. No data vendor lock-in. You own every line of it.

```
┌────────────────────────────────────────────────────────────────────────┐
│  Live Prices → Signal Engine → ZMQ Bus → Scanners + Dashboard + Alerts │
└────────────────────────────────────────────────────────────────────────┘
```

> ⚠️ **Disclaimer** — AlgoStack is a *research and alerting* tool. It does **not** place orders automatically. All trading decisions remain with the user.

---

## ✦ Key Numbers

<div align="center">

| Metric | Value |
|--------|-------|
| Total lines of Python | **30,595** |
| Concurrent processes | **16** |
| GPU strategy evaluations / tick | **2,352,000** |
| CuPy sweep latency (GTX 1650) | **< 1ms** |
| NSE equity symbols | **38** |
| MCX commodity feeds | **5** |
| Crypto pairs (Binance WS) | **5** |
| Enterprise auth codebase | **1,459 lines** |
| Self-healing watchdog | **1,025 lines** |
| CPU cores pinned (i5-12450H) | **10** |

</div>

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
- `alert_monitor.py` cross-checks live prices vs dashboard continuously
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
- RBAC: admin / analyst / client_readonly
- Enable with one env var: `ALGOSTACK_AUTH_ENABLED=1`

</td>
<td width="50%">

### ⚙️ Self-Healing Infrastructure
- `autohealer.py` watchdog auto-restarts any crashed process
- **Market-calendar-aware** — no restarts on NSE/MCX holidays
- `wifi_keepalive.py` re-authenticates captive portal automatically
- `log_manager.py` rotates and purges stale logs
- `process_affinity.py` pins processes to CPU cores (Windows)

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
│  IPC :  ZMQ PUB/SUB   tcp://127.0.0.1:28081  SNDHWM=2  SNDTIMEO=5ms  │
│  Data:  levels/live_prices.json  +  trade_logs/*.jsonl                │
└────────────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Zero shared database** — engines write flat JSON/JSONL; dashboard polls on a fast/slow cycle
- **ZMQ PUB/SUB** with SNDHWM=2 backpressure — stale ticks dropped, consumers never block
- **Flat-file IPC** keeps the stack deployable on the cheapest VPS with no DB daemon
- **Modular process tree** — any single component can crash and restart without taking down the rest
- **Atomic writes** (`write-to-.tmp + os.replace`) — zero partial-read corruption risk

---

## ✦ X-Multiplier Signal Engine

The proprietary signal framework used across all three asset classes:

```
buy_above  = prev_close + X          ← long entry trigger
sell_below = prev_close − X          ← short entry trigger
sl_buy     = buy_above  − X          ← long stop-loss
sl_sell    = sell_below + X          ← short stop-loss
t1..t5     = buy_above  + n×X        ← target ladder (5 levels)

Retreat risk system:
  65% of peak → warning
  45% of peak → retreat activated
  25% of peak → force-exit + re-anchor
```

BestX Optimizer (`best_x_trader.py`) backtests 32,000+ X variants per symbol and identifies the historically optimal configuration — running in < 1ms on GPU hardware.

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

### Quick Start

```bash
# 1. Clone
git clone https://github.com/Ridhaant/algostack.git && cd algostack

# 2. Virtual environment
python3 -m venv .venv && source .venv/bin/activate  # Linux/macOS
# python -m venv .venv && .venv\Scripts\activate     # Windows

# 3. Dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env   # then set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_IDS

# 5. Pre-flight check
python health_check.py

# 6. Launch
./start_all.sh          # Linux/macOS
# start_all.bat         # Windows
```

Open **http://localhost:8055** in your browser.

For GPU acceleration (NVIDIA only):
```bash
pip install numba cupy-cuda12x
```

---

## ✦ Configuration

All settings live in `.env`. **Never hardcode secrets in `.py` files.**

```ini
# Telegram (required for alerts)
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
TELEGRAM_CHAT_IDS=123456789

# Trading parameters
CURRENT_X_MULTIPLIER=0.008
CAPITAL_PER_TRADE=100000
CRYPTO_X_MULTIPLIER=0.008
CRYPTO_BUDGET_USDT=1065

# Commodity X multipliers
COMMODITY_GOLD_X=0.003430
COMMODITY_SILVER_X=0.005145
COMMODITY_CRUDE_X=0.000602

# Optional: Enable enterprise auth
ALGOSTACK_AUTH_ENABLED=1
```

### Optional API Keys

| Key | Purpose |
|---|---|
| `GEMINI_API_KEY` | AI-powered analysis |
| `ANTHROPIC_API_KEY` | Claude integration |
| `NEWS_API_KEY` | Richer news feed |
| `REDDIT_CLIENT_ID/SECRET` | Reddit sentiment |
| `NGROK_AUTHTOKEN_EQUITY` | Persistent tunnel |
| `GOOGLE_OAUTH_CLIENT_ID/SECRET` | Google SSO |

---

## ✦ Dashboard Overview

| Tab | Content |
|---|---|
| **Engine Lane** | Live P&L · Open positions · Full trade history (authoritative JSONL) |
| **Research Lane** | Scanner sweep output · X-Optimizer results · BestX backtests |
| **Crypto Lane** | Crypto positions · Level table · USDT & INR P&L |
| **News Lane** | Aggregated headlines · VADER sentiment scores · Source breakdown |

News dashboard (`news_dashboard.py`, port **:8070**) runs as a separate process aggregating from NewsAPI, GNews, Reddit, and Twitter.

---

## ✦ Docker

```bash
docker-compose up --build          # build and start
docker-compose up -d               # detached
docker-compose logs -f             # stream logs
```

Exposed ports: **8055** (main dashboard) · **8070** (news dashboard)

See `DEPLOY_RENDER_NO_CARD.md` for free-tier deployment on **Render.com**.

---

## ✦ Open-Source Libraries

Three architectural layers of AlgoStack are available as standalone open-source libraries:

| Library | Description |
|---|---|
| **[nexus-price-bus](https://github.com/Ridhaant/nexus-price-bus)** | Multi-source ZMQ market data bus (NSE + Binance) |
| **[vectorsweep](https://github.com/Ridhaant/vectorsweep)** | GPU-accelerated strategy parameter sweep engine |
| **[sentitrade](https://github.com/Ridhaant/sentitrade)** | Real-time Indian financial news NLP pipeline |

---

## ✦ Troubleshooting

<details>
<summary><strong>Dashboard shows stale prices / "No data"</strong></summary>
Confirm all three engines are running. Check `levels/live_prices.json` is being updated. Run `python diagnose_dash.py`.
</details>

<details>
<summary><strong>Telegram alerts not arriving</strong></summary>
Confirm `TELEGRAM_BOT_TOKEN` is set. You must send at least one message to the bot first. Verify `TELEGRAM_CHAT_IDS` via @userinfobot.
</details>

<details>
<summary><strong>ModuleNotFoundError on startup</strong></summary>
Activate your virtual environment, then `pip install -r requirements.txt`.
</details>

<details>
<summary><strong>ZMQ connection errors on startup</strong></summary>
Normal — engines start in parallel; scanner ZMQ errors for the first few seconds resolve automatically once publishers are ready.
</details>

<details>
<summary><strong>High CPU usage</strong></summary>
Use `start_optimised.bat` (Windows) to pin processes to specific cores. Reduce active scanners by commenting them out in the launcher.
</details>

---

## ✦ Roadmap

- [ ] Order routing integration (Zerodha Kite API)
- [ ] Strategy backtesting framework with walk-forward validation
- [ ] Mobile-optimised PWA dashboard
- [ ] Options chain integration (NSE)
- [ ] Multi-user portfolio aggregation

---

## ✦ Security Notes

- **Never hardcode tokens in `.py` files.** All secrets must live in `.env`
- **Rotate any credentials ever committed** — once in git history, always compromised
- Enable enterprise auth before exposing the dashboard to the internet
- The dashboard binds to `0.0.0.0` by default; change to `127.0.0.1` on shared machines

---

## ✦ Author

<div align="center">

**[Ridhaant Ajoy Thackur](https://github.com/Ridhaant)**

*Systems Engineer · Quant Developer · FinTech Infrastructure*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-ridhaant--thackur-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/ridhaant-thackur-09947a1b0)
[![Email](https://img.shields.io/badge/Email-redantthakur%40gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:redantthakur@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-Ridhaant-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Ridhaant)

---

© 2026 Ridhaant Ajoy Thackur. All rights reserved.
AlgoStack™ is proprietary software. Unauthorised copying or distribution is prohibited.

*If this project helped you, consider leaving a ⭐*

</div>
