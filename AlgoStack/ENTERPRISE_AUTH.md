# AlgoStack enterprise auth (self-hosted)

**Decision:** Identity is **self-hosted** in this repository (Flask-Login + SQLite + TOTP).  
Managed IdP (Auth0, Clerk, Supabase) or SSO (Entra / Google + oauth2-proxy) remains an optional future swap for the same `before_request` boundary.

## Enable authentication

1. Set a strong secret (required when auth is on):

   ```bash
   set ALGOSTACK_SECRET_KEY=your-long-random-secret
   set ALGOSTACK_AUTH_ENABLED=1
   ```

2. **First user** — either set bootstrap env vars **once** before first start:

   ```bash
   set ALGOSTACK_BOOTSTRAP_ADMIN_EMAIL=you@example.com
   set ALGOSTACK_BOOTSTRAP_ADMIN_PASSWORD=your-secure-password
   ```

   Or run the CLI after install:

   ```bash
   python enterprise_auth.py bootstrap --email you@example.com --password "..."
   python enterprise_auth.py add-user --email analyst@example.com --password "..." --role analyst --org default
   ```

3. Restart UnifiedDash / autohealer.

4. Open the dashboard — you will be redirected to `/auth/login`.

5. **2FA:** After login, open `/auth/enroll-2fa`, scan the secret with an authenticator app, confirm with a 6-digit code, and store the one-time backup codes.

## Environment variables

| Variable | Description |
|----------|-------------|
| `ALGOSTACK_AUTH_ENABLED` | `1` / `true` to require login (default `0` for backward compatibility). |
| `ALGOSTACK_SECRET_KEY` | Flask session signing; **required** when auth enabled. |
| `ALGOSTACK_SESSION_COOKIE_SECURE` | Set `1` behind HTTPS reverse proxy (recommended). |
| `ALGOSTACK_DB_PATH` | SQLite path (default `data/algostack_auth.db`). |
| `AUTH_AUDIT_LOG` | Audit log file (default `logs/auth_audit.log`). |
| `AUTH_AUDIT_MAX_BYTES` | When exceeded, log is rotated to `.1` (default 20MB). |
| `ALGOSTACK_BOOTSTRAP_ADMIN_EMAIL` / `PASSWORD` | Create first admin if DB is empty (optional). |
| `PUBLIC_LINK_PASSWORD` | Optional ngrok/tunnel **hint** only — no default in code; never commit real values. |

### Email password reset (SMTP)

Forgot-password emails require SMTP. Copy `.env.example` to `.env` and set:

| Variable | Description |
|----------|-------------|
| `ALGOSTACK_SMTP_HOST` | SMTP server hostname |
| `ALGOSTACK_SMTP_PORT` | Usually `587` (STARTTLS) |
| `ALGOSTACK_SMTP_USER` / `ALGOSTACK_SMTP_PASSWORD` | Credentials (Gmail: use an [App Password](https://support.google.com/accounts/answer/185833)) |
| `ALGOSTACK_MAIL_FROM` | From address shown to recipients |
| `PUBLIC_BASE_URL` | Optional; use your stable public URL so reset links work behind tunnels |

Without SMTP, use: `python enterprise_auth.py set-password --email you@x.com --password "..."`.

### Google sign-in (optional)

Set `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` (see `.env.example`). In Google Cloud Console, add redirect URI `https://<your-host>:8055/auth/google/callback` (and your tunnel URL if used).

## HTTPS

Terminate TLS at **Caddy**, **nginx**, or your PaaS edge, then set `ALGOSTACK_SESSION_COOKIE_SECURE=1` so session cookies are not sent over plain HTTP.

## Multi-tenant

Users belong to an **organization** (`organizations` table) with roles: `admin`, `analyst`, `client_readonly`.  
Per-tenant file roots are under `levels/tenants/<org_id>/` (hooks for future client-scoped exports).
