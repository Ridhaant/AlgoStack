<div align="center">

<!-- Animated Typing Header -->
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=30&duration=3000&pause=1000&color=00FF41&center=true&vCenter=true&width=900&lines=AlgoStack+v10.7;30%2C595+Lines.+16+Processes.+3+Markets.+Live.;GPU+Inference+%3C1ms+on+GTX+1650;Self-Healing+%7C+ZeroMQ+%7C+CUDA+%7C+Production" alt="AlgoStack" />

<br/>

<!-- Stats Badges -->
![Lines of Code](https://img.shields.io/badge/Lines%20of%20Code-30%2C595-00FF41?style=for-the-badge&logo=python&logoColor=white)
![Processes](https://img.shields.io/badge/Concurrent%20Processes-16-00D4FF?style=for-the-badge&logo=linux&logoColor=white)
![GPU Speed](https://img.shields.io/badge/GPU%20Inference-%3C1ms%20%2F%20GTX%201650-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![Markets](https://img.shields.io/badge/Live%20Markets-NSE%20%7C%20MCX%20%7C%20Binance-FF6B35?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

<br/>

**Production-grade multi-asset quantitative trading & intelligence platform.**<br/>
Sole-authored by **[Ridhaant Ajoy Thackur](https://github.com/Ridhaant)** · Top 2.4% Nationally (JEE Mains 97.55 Percentile)

<br/>

<!-- Tech Stack Icons -->
<img src="https://skillicons.dev/icons?i=python,docker,linux,redis,postgres,fastapi,react,ts,git,github,vscode,cpp&theme=dark" />

<br/><br/>

<!-- Custom Badges for Non-Standard Tech -->
![ZeroMQ](https://img.shields.io/badge/ZeroMQ-DF0000?style=flat-square&logo=zeromq&logoColor=white)
![CuPy CUDA 12](https://img.shields.io/badge/CuPy_CUDA_12-76B900?style=flat-square&logo=nvidia&logoColor=white)
![Numba JIT](https://img.shields.io/badge/Numba_JIT-00A3E0?style=flat-square&logo=llvm&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![Plotly Dash](https://img.shields.io/badge/Plotly_Dash-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic_Claude-191919?style=flat-square&logo=anthropic&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=flat-square&logo=google&logoColor=white)
![Binance](https://img.shields.io/badge/Binance_WS-F0B90B?style=flat-square&logo=binance&logoColor=black)
![Telegram](https://img.shields.io/badge/Telegram_Bots-26A5E4?style=flat-square&logo=telegram&logoColor=white)
![Flask](https://img.shields.io/badge/Flask_Login-000000?style=flat-square&logo=flask&logoColor=white)
![JWT](https://img.shields.io/badge/JWT_Auth-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)
![Redis](https://img.shields.io/badge/Redis_7-DC382D?style=flat-square&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=black)
![Cloudflare](https://img.shields.io/badge/Cloudflare_Tunnel-F38020?style=flat-square&logo=cloudflare&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat-square&logo=terraform&logoColor=white)

</div>

---

## ⚡ What Is AlgoStack?

A sole-authored, **30,595-line, 16-process live production trading platform** running simultaneously across **NSE equities, MCX commodities, and Binance crypto** — with GPU-accelerated parameter sweeps processing **2,352,000 vectorised evaluations per price tick in <1ms**.

This is not a tutorial project. This is not a notebook. This is a **deployed, autonomous system** with self-healing process supervision, enterprise authentication, NLP sentiment intelligence, and zero-downtime deployment across 3 environments.

---

## 📊 Live Performance Metrics

<div align="center">

| Metric | Value | Status |
|:---|:---|:---:|
| **GPU Evaluations/Tick** | 2,352,000 vectorised | 🟢 LIVE |
| **Inference Latency** | < 1ms (GTX 1650, CuPy CUDA 12) | 🟢 LIVE |
| **NSE Symbols** | 38 equities | 🟢 LIVE |
| **MCX Symbols** | 5 commodities (Gold/Silver/Crude/NatGas/Copper) | 🟢 LIVE |
| **Binance Pairs** | 5 crypto pairs | 🟢 LIVE |
| **IPC Bus Processes** | 16 concurrent (CPU-affinity pinned, 10 cores) | 🟢 LIVE |
| **Zero-Loss Guarantee** | ZMQ PUB/SUB + atomic JSON fallback | ✅ PROD |
| **Auth System** | TOTP 2FA RFC 6238, RBAC, multi-tenant | ✅ PROD |
| **Uptime Supervisor** | Market-calendar-aware, WiFi keepalive | ✅ PROD |
| **NLP Pipeline** | VADER + 130 domain boosters, 11-sector classifier | ✅ PROD |
| **Deployment** | Docker / Render / Cloudflare Tunnel / K8s-ready | ✅ PROD |

</div>

---

## 🏗️ System Architecture — 16 Supervised Processes

```mermaid
graph LR
    subgraph "🧠 Supervisor (L1)"
        AH["autohealer.py<br/>(1,025 lines)"]
    end

    subgraph "⚡ Execution Layer (L2 — 16 Processes)"
        subgraph "Trading Engines"
            EQ["Equity<br/>Algofinal.py"]
            CO["Commodity<br/>engine.py"]
            CR["Crypto<br/>engine.py"]
        end
        subgraph "Scanners (GPU/JIT)"
            SC["6. Sweep Scanners<br/>(3 Equity, 3 MCX/Crypto)"]
        end
        subgraph "Observability"
            UD["unified_dash_v3.py"]
            TG["3 Telegram Bots"]
            WK["wifi_keepalive.py"]
            AM["alert_monitor.py"]
        end
    end

    subgraph "📡 Data Layer (L3)"
        NPB["nexus-price-bus<br/>ZMQ PUB/SUB"]
        ST["sentitrade<br/>NLP Pipeline"]
        VS["vectorsweep<br/>CuPy / CUDA"]
        DB["Redis & Postgres"]
    end

    subgraph "🔒 Security Perimeter"
        EA["enterprise_auth.py<br/>(1,459 lines)"]
    end

    AH -->|Spawns & Supervises| EQ
    AH --> CO & CR & SC & UD & TG & WK & AM

    NPB -->|ZMQ Price Ticks| EQ & CO & CR & SC
    ST -->|Sentiment| UD & TG
    VS -->|Parallel Results| SC
    
    EQ & CO & CR -->|Trade Events| DB
    DB --> UD & AM
    
    EA -->|TOTP 2FA + RBAC| UD

    style AH fill:#0d1117,stroke:#00FF41,stroke-width:2px,color:#00FF41
    style NPB fill:#0d1117,stroke:#00D4FF,stroke-width:2px,color:#00D4FF
    style EA fill:#0d1117,stroke:#FF6B35,stroke-width:2px,color:#FF6B35
    style SC fill:#0d1117,stroke:#76B900,stroke-width:2px,color:#76B900
```

<details>
<summary><b>💡 Why this architecture matters to hiring managers</b></summary>

This is a **production supervisor–subagent framework** — architecturally identical to LLM multi-agent systems (AutoGen, CrewAI, LangGraph):

| AlgoStack Component | LLM Multi-Agent Equivalent |
|:---|:---|
| `autohealer.py` (1,025 lines) | **Orchestrator agent** — spawns, monitors, restarts subagents |
| 16 OS processes | **Specialized subagents** — each with a single responsibility |
| ZMQ PUB/SUB bus | **Inter-agent message passing** — topic-based routing |
| GPU sweep (2.35M evals/tick) | **Batched parallel inference** — analogous to batched LLM token generation |
| Market-calendar scheduling | **Context-aware task gating** — only run agents when relevant |

**ML/AI recruiters:** If you understand multi-agent orchestration, you already understand AlgoStack's architecture.

</details>

---

## 🎯 X-Multiplier Strategy — Proprietary Signal Framework

The core intellectual property — a level-based signal generation system operating across all three asset classes:

```python
# ═══════════════════════════════════════════════════════════════
# AlgoStack X-Multiplier Level Framework (production code)
# ═══════════════════════════════════════════════════════════════

# Core entry triggers
buy_above  = prev_close + X              # Long trigger
sell_below = prev_close - X              # Short trigger

# 5-Tier Target Ladder (standard symbols)
T1 = buy_above + 1.0*X  |  ST1 = sell_below - 1.0*X
T2 = buy_above + 2.0*X  |  ST2 = sell_below - 2.0*X
T3 = buy_above + 3.0*X  |  ST3 = sell_below - 3.0*X
T4 = buy_above + 4.0*X  |  ST4 = sell_below - 4.0*X
T5 = buy_above + 5.0*X  |  ST5 = sell_below - 5.0*X

# High-Volatility Names (RELIANCE, SBIN, KOTAKBANK, ICICIBANK)
target_step = 0.6 * X                   # Compressed ladder

# Symmetric Stop-Losses
buy_sl  = buy_above  - X                # Long protection
sell_sl = sell_below + X                # Short protection

# Peak-Retreat Risk System (SymbolState state machine)
retreat_65 = peak * 0.65   # Warning  (None → warned_65)
retreat_45 = peak * 0.45   # Activate (warned_65 → activated_45)
retreat_25 = peak * 0.25   # EXIT     (force close + re-anchor)

# X-Optimizer Composite Score (147,000+ variants evaluated)
score = 0.5 * pnl_norm + 0.3 * win_rate + 0.2 * (1 - drawdown_norm)
```

| Feature | Implementation |
|:---|:---|
| **Re-anchoring** | Equity: 09:15–09:34 ladder + 09:35 hard re-anchor · Commodity: 09:30 · Crypto: 6h cycle |
| **EOD Square-off** | Equity 15:11 IST · Commodity 23:30 IST · Crypto configurable |
| **Production X** | `0.008` (0.8% band) — override via `.env` per asset class, no code edits |

---

## 🌐 Open-Source Ecosystem

AlgoStack's production subsystems, extracted as standalone libraries:

```
AlgoStack Core (30,595 lines)
├── nexus-price-bus  →  ZMQ PUB/SUB multi-source price bus (NSE + MCX + Binance)
├── sentitrade       →  Real-time Indian market NLP sentiment pipeline
└── vectorsweep      →  GPU-accelerated parameter sweep library (CuPy/Numba/NumPy)
```

<div align="center">

[![nexus-price-bus](https://img.shields.io/badge/nexus--price--bus-ZMQ%20Price%20Bus-00D4FF?style=for-the-badge&logo=zeromq&logoColor=white)](https://github.com/Ridhaant/Nexus-Price-Bus)
[![sentitrade](https://img.shields.io/badge/sentitrade-NLP%20Sentiment-00FF41?style=for-the-badge&logo=python&logoColor=white)](https://github.com/Ridhaant/SentiTrade)
[![vectorsweep](https://img.shields.io/badge/vectorsweep-GPU%20Sweeps-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://github.com/Ridhaant/VectorSweep)
[![SentinelVault](https://img.shields.io/badge/SentinelVault-Security%20%26%20Auth-FF6B35?style=for-the-badge&logo=hackthebox&logoColor=white)](https://github.com/Ridhaant/SentinelVault)

</div>

| Sub-Project | What It Proves | Key Metric |
|:---|:---|:---|
| **[nexus-price-bus](https://github.com/Ridhaant/Nexus-Price-Bus)** | Distributed systems, ZMQ IPC, fault tolerance | 16 concurrent subscribers, zero data loss |
| **[sentitrade](https://github.com/Ridhaant/SentiTrade)** | NLP, data engineering, domain adaptation | 130+ keyword boosters, 11-sector classifier |
| **[vectorsweep](https://github.com/Ridhaant/VectorSweep)** | GPU computing, numerical methods, quant research | 2,352,000 evals/tick, <1ms CuPy CUDA |
| **[SentinelVault](https://github.com/Ridhaant/SentinelVault)** | AppSec, DevSecOps, enterprise auth | 1,459-line auth, TOTP 2FA, RBAC |

---

## 🔒 Enterprise Security (1,459 Lines of Production Auth)

`enterprise_auth.py` — a self-hosted, zero-dependency authentication system:

| Feature | Implementation |
|:---|:---|
| **TOTP 2FA** | RFC 6238 via `pyotp` — QR enrolment, ±1 step, Google Authenticator compatible |
| **Backup Codes** | 8 single-use, bcrypt-hashed, survive authenticator loss |
| **RBAC** | `admin` / `analyst` / `client_readonly` with filesystem-level isolation |
| **Multi-Tenant** | Per-org file roots at `levels/tenants/<org_id>/` |
| **Token Reset** | 48-char hex, 30-min expiry, one-time-use, replay-resistant |
| **Audit Trail** | 20MB rotating append-only log — tamper-evident, no delete/update |
| **OAuth** | Optional Google sign-in, env-configured |
| **ZMQ Hardening** | SNDHWM=2 backpressure, LINGER=0, SNDTIMEO=5ms |
| **Atomic Writes** | write-to-.tmp + os.replace — zero partial-read corruption |

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technologies |
|:---|:---|
| **Languages** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) ![C++](https://img.shields.io/badge/C++-00599C?style=flat-square&logo=cplusplus&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white) ![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat-square&logo=mysql&logoColor=white) ![CUDA](https://img.shields.io/badge/CUDA-76B900?style=flat-square&logo=nvidia&logoColor=white) ![Bash](https://img.shields.io/badge/Bash-4EAA25?style=flat-square&logo=gnubash&logoColor=white) |
| **GPU & Compute** | ![CuPy](https://img.shields.io/badge/CuPy_CUDA_12-76B900?style=flat-square&logo=nvidia&logoColor=white) ![Numba](https://img.shields.io/badge/Numba_JIT-00A3E0?style=flat-square&logo=llvm&logoColor=white) ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white) |
| **Messaging** | ![ZeroMQ](https://img.shields.io/badge/ZeroMQ-DF0000?style=flat-square&logo=zeromq&logoColor=white) ![Redis](https://img.shields.io/badge/Redis_7-DC382D?style=flat-square&logo=redis&logoColor=white) ![JSON IPC](https://img.shields.io/badge/JSON_IPC-000000?style=flat-square&logo=json&logoColor=white) |
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) ![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white) ![JWT](https://img.shields.io/badge/JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white) ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white) |
| **Frontend** | ![React](https://img.shields.io/badge/React_TS-61DAFB?style=flat-square&logo=react&logoColor=black) ![Plotly](https://img.shields.io/badge/Plotly_Dash-3F4F75?style=flat-square&logo=plotly&logoColor=white) ![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white) |
| **Database** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) ![JSONL](https://img.shields.io/badge/JSONL_Ledger-000000?style=flat-square&logo=json&logoColor=white) |
| **NLP & AI** | ![VADER](https://img.shields.io/badge/VADER_NLP-3fb950?style=flat-square) ![Anthropic](https://img.shields.io/badge/Claude-191919?style=flat-square&logo=anthropic&logoColor=white) ![OpenAI](https://img.shields.io/badge/GPT--4o-412991?style=flat-square&logo=openai&logoColor=white) ![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=flat-square&logo=google&logoColor=white) |
| **Auth** | ![TOTP](https://img.shields.io/badge/TOTP_2FA-FF6B35?style=flat-square) ![RBAC](https://img.shields.io/badge/RBAC-7c3aed?style=flat-square) ![OAuth](https://img.shields.io/badge/OAuth_2.0-4285F4?style=flat-square&logo=google&logoColor=white) |
| **Infrastructure** | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) ![K8s](https://img.shields.io/badge/Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white) ![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat-square&logo=terraform&logoColor=white) ![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=black) ![Cloudflare](https://img.shields.io/badge/Cloudflare-F38020?style=flat-square&logo=cloudflare&logoColor=white) |
| **Monitoring** | ![Telegram](https://img.shields.io/badge/Telegram_Bots-26A5E4?style=flat-square&logo=telegram&logoColor=white) ![Binance](https://img.shields.io/badge/Binance_WS-F0B90B?style=flat-square&logo=binance&logoColor=black) |

</div>

---

## 📁 Module Map — 30,595 Lines

<details>
<summary><b>Click to expand full module breakdown</b></summary>

| Module | ~Lines | Responsibility |
|:---|---:|:---|
| `Algofinal.py` | 8,000 | Equity engine — X-levels, position lifecycle, session logic, EOD |
| `unified_dash_v3.py` | 10,000 | Single-pane operator UI — engine + research lanes |
| `sweep_core.py` | 2,400 | Shared vectorized sweep engine, simulation core |
| `enterprise_auth.py` | 1,459 | TOTP 2FA, RBAC, multi-tenant, OAuth, audit |
| `commodity_engine.py` | 1,500 | MCX engine — 4-tier data fallback, session gating |
| `crypto_engine.py` | 1,650 | Binance engine — WS + REST fallback, 6h re-anchor |
| `autohealer.py` | 1,025 | Process supervisor, health checks, WiFi keepalive |
| `alert_monitor.py` | 1,250 | Feed staleness, tunnel health, EOD P&L verification |
| `x.py` | 1,050 | X-optimizer — 147K variant aggregation, composite scoring |
| `news_dashboard.py` | 950 | RSS, Reddit, FII/DII flow, sector heatmap |
| `gpu_sweep.py` | 800 | CuPy/Numba/NumPy auto-detecting GPU compute |
| `scanner1/2/3.py` | 2,100 | Equity X-value sweep scanners (narrow/dual/wide) |
| `commodity_scanner1/2/3.py` | 1,800 | MCX commodity sweep scanners |
| `crypto_scanner1/2/3.py` | 1,600 | Binance crypto sweep scanners |
| `wifi_keepalive.py` | 670 | Connectivity monitoring, captive portal re-auth |
| `ipc_bus.py` | 600 | ZMQ + Redis bus abstraction |
| `best_x_trader.py` | 640 | Execution simulation from sweep results |
| `price_service.py` | 400 | Multi-source price publisher |
| `config.py` | 300 | Environment-driven config, SecretManager |
| `market_calendar.py` | 290 | NSE/MCX/Binance session gating, holidays |
| `sentiment_analyzer.py` | 250 | VADER + domain boosters, sector classification |
| `risk_controls.py` | 150 | Drawdown limits, trade caps, cooldown |

</details>

---

## 🚀 Installation

```bash
# Clone
git clone https://github.com/Ridhaant/AlgoStack.git
cd AlgoStack

# Environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# Dependencies
pip install -r requirements.txt
pip install cupy-cuda12x         # Optional: 15-30× faster scanners

# Configure (never commit .env)
cp .env.template .env

# Launch — Full 16-process production stack
python autohealer.py
```

```bash
# OR — Docker Compose (full stack with Postgres + Redis)
docker-compose up --build
```

| Access Point | URL |
|:---|:---|
| **Dashboard** | `http://localhost:8055` |
| **FastAPI Docs** | `http://localhost:8080/docs` |
| **React Frontend** | `http://localhost:5173` (dev) |

---

## 👤 About the Author

<div align="center">

**Ridhaant Ajoy Thackur**

Top 2.4% Nationally (JEE Mains 97.55 Percentile)

[![Email](https://img.shields.io/badge/Email-redantthakur%40gmail.com-D14836?style=flat-square&logo=gmail&logoColor=white)](mailto:redantthakur@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://linkedin.com/in/Ridhaant)
[![Phone](https://img.shields.io/badge/Phone-%2B91--7021610641-25D366?style=flat-square&logo=whatsapp&logoColor=white)](tel:+917021610641)
[![GitHub](https://img.shields.io/badge/GitHub-Ridhaant-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/Ridhaant)

</div>


<div align="center">

**Production-verified. Sole-authored. Zero data loss. Live.**

© 2026 Ridhaant Ajoy Thackur · MIT License

</div>
