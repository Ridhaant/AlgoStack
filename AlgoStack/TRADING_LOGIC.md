# AlgoStack Trading Logic (Code-Grounded)

This document describes the real execution flow used by the current codebase for equity, MCX commodity, and crypto.

## 1) Price ingest and live distribution

- **Equity**: `Algofinal.py` publishes equity prices to `levels/live_prices.json` (`prices` / `equity_prices`) and ZMQ topic `prices`.
- **Commodity**: `commodity_engine.py` ingests TradingView WS + REST fallback, writes `commodity_prices` into `levels/live_prices.json`, and publishes ZMQ topic `commodity` in-session.
- **Crypto**: `crypto_engine.py` ingests Binance WS (fallbacks: CoinCap/CoinGecko), writes `crypto_prices` into `levels/live_prices.json`, and publishes ZMQ topic `crypto`.
- **Dashboard read path**: `unified_dash_v3.py` (`_DataStore._refresh_fast`) consumes `live_prices.json`, scanner state JSONs, and trade JSONL files.

## 2) Anchor and re-anchor logic

### Equity

- Uses prev-close seeded levels and session-driven re-anchoring in `Algofinal.py`.
- Entry blackout and session handling are aligned to market window logic used by runtime checks and EOD square-off flow.

### MCX Commodity

- Initial levels from previous close or fallback loaders in `commodity_engine.py` (`_load_prev_closes`, `_calc_levels`).
- 09:30 re-anchor in `commodity_engine.py` (`_recalc_levels_930`).
- Session gating now uses `MarketCalendar.is_commodity_session()` via `_in_session`.

### Crypto

- Initial anchor from startup prices in `crypto_engine.py` (`startup`, `_fetch_initial_binance_prices`).
- Re-anchor every 6 hours in `crypto_engine.py` (`_do_reanchor`, `_NEXT_ANCHOR` in `_price_loop`).

## 3) Level generation

- **Equity**: Generated in `Algofinal.py` with X-multiplier path used by live engine and scanner ecosystem.
- **Commodity**: `commodity_engine.py` (`_calc_levels`):
  - `x_val = prev_close * COMM_X[sym]`
  - `buy_above`, `sell_below`, `T1..T5`, `ST1..ST5`, retreat thresholds.
- **Crypto**: `crypto_engine.py` (`_calc_levels`):
  - `x_val = anchor * CRYPTO_X`
  - `buy_above`, `sell_below`, `T1..T5`, `ST1..ST5`, stop loss, INR mirror fields.

## 4) Entry/exit and position lifecycle

### Shared structure

- Entry events are logged at trigger.
- Exit events include targets, stop-loss, retreat exits, and EOD/re-anchor forced exits.
- Trade artifacts are JSONL-first and consumed by dashboard and monitoring.

### Equity

- Entry/exit logic and EOD handling are in `Algofinal.py` (trade events + EOD summary writers).
- EOD flow closes remaining open positions and writes summary/trade artifacts used by dashboard and telegram flow.

### MCX Commodity

- Price tick processing in `commodity_engine.py` (`_process_price`).
- Entry when crossing `buy_above` / `sell_below`.
- Exit on `T*`, `ST*`, `SL_HIT`, `RETREAT`.
- EOD square-off in `commodity_engine.py` (`_eod_square_off`) with event reason `EOD_2330` (historical tag naming retained).

### Crypto

- Price tick processing in `crypto_engine.py` (`_process_price`).
- Entry when crossing `buy_above` / `sell_below`.
- Exit on `T*`, `ST*`, `SL_HIT`, `RETREAT`.
- Re-anchor square-off in `crypto_engine.py` (`_do_reanchor`) with event reason `RE_ANCHOR`.

## 5) Persistence and dashboard source-of-truth

- **Equity trade events**: `trade_logs/trade_events_YYYYMMDD.jsonl`
- **Commodity trade events**: `trade_logs/commodity_trade_events_YYYYMMDD.jsonl`
- **Crypto trade events**: `trade_logs/crypto_trade_events_YYYYMMDD.jsonl`
- **Levels**:
  - Equity: `levels/initial_levels*.xlsx` (+ adjusted/prevday variants)
  - Commodity: `levels/commodity_initial_levels_*.json` (+ xlsx fallback)
  - Crypto: `levels/crypto_initial_levels_latest.json`
- **Live price bus file**: `levels/live_prices.json`

Dashboard reads these in `unified_dash_v3.py` (`_DataStore._refresh_fast` and `_refresh_slow`) and presents:
- Engine lane (authoritative): positions/P&L from trade-event logs + engine state.
- Research lane: scanner, optimizer, and BestX outputs (non-executed simulation outputs).

## 6) EOD/open-position guardrails and monitoring

- `alert_monitor.py` performs:
  - feed staleness checks
  - tunnel health checks
  - EOD P&L cross-verification
  - open-position-after-EOD checks from same JSONL sources the dashboard uses

This keeps engine state, trade logs, and UI tables consistent across session boundaries.
