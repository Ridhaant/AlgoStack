# Local PC + ngrok (one link, no tunnel restarts)

## What the code does now

- **Hardcoded** defaults: `NGROK_AUTHTOKEN` + `NGROK_API_KEY` in `unified_dash_v3.py` (overridable via env).
- **`python autohealer.py` on your laptop**: `UnifiedDash` gets  
  `DISABLE_PUBLIC_TUNNEL=0`, `TUNNEL_NGROK_ONLY=1`, `TUNNEL_SINGLE_URL=1`, `PUBLIC_BASE_URL` cleared → **one ngrok URL**, guardian does **not** send new links or restart the tunnel chain.
- **On Render** (`RENDER=true`): tunnel stays **off**; `PUBLIC_BASE_URL` is used instead.

## Run

1. Install deps: `pip install -r requirements.txt` (includes `pyngrok`).
2. Optional: install [ngrok](https://ngrok.com/download) and add to `PATH` if you prefer CLI fallback.
3. Start: `python autohealer.py`

Telegram should receive **one** `https://….ngrok…` URL for port **8055** (unified dashboard).

## Free-tier quota and rotation behavior

- ngrok free plans can return a valid HTTP page that contains `ERR_NGROK_727` / `HTTP Requests exceeded`.
- AlgoStack now treats that response as a **hard tunnel failure** (not healthy).
- Default remains `TUNNEL_SINGLE_URL=1` (no auto-rotation, one link policy).
- If you want automatic URL rotation + Telegram re-announce on failures, set:
  - `TUNNEL_SINGLE_URL=0`
  - `TUNNEL_NGROK_ONLY=1` (recommended if you only want ngrok)
  - then run `python autohealer.py`.

## Security

Secrets are in source code. If this repo is public or tokens were shared, **rotate** them in the ngrok dashboard and update the defaults (or use `.env` / env vars only).
