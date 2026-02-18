# External Integrations

**Analysis Date:** 2026-02-18

## APIs & External Services

**Market Data:**
- Yahoo Finance (via yfinance 1.1.0) - Real-time and historical stock prices, fundamentals, cash flow statements, analyst estimates, and news
  - SDK/Client: `yfinance` (`import yfinance as yf` in `app.py`)
  - Auth: No API key required; unauthenticated public API calls
  - Usage: `yf.download()` for bulk price data, `yf.Ticker()` for per-stock fundamentals and news
  - TTL: 5-minute cache (`@st.cache_data(ttl=300)`)
  - Endpoints used: price history, `.info`, `.cashflow`, `.financials`, `.news`

## Data Storage

**Databases:**
- Google Sheets - Primary data store for portfolio holdings and watchlist
  - Connection: `st.connection("gsheets", type=GSheetsConnection)` in `app.py` line 16
  - Client: `st-gsheets-connection` 0.1.0 wrapping `gspread` 5.12.4
  - Worksheets read: `"Portfolio"` (positions), `"Watchlist"` (tracked tickers)
  - Operations: read (`conn.read()`), update (`conn.update()`) via `app.py` lines 169, 200, 277-278
  - Auth: Google service account JSON key (referenced in `.streamlit/secrets.toml`)
  - TTL: 5-second cache on sheet reads (`ttl=5`)

**File Storage:**
- Local filesystem only - no object storage (S3, GCS, etc.) detected

**Caching:**
- Streamlit in-memory cache (`@st.cache_data`) - not a persistent cache; resets on app restart

## Authentication & Identity

**Auth Provider:**
- Google OAuth2 / Service Account - used exclusively for Google Sheets API access
  - Implementation: Service account JSON key (`financegmaildigestkey-12081659191d.json` present at project root - this file contains credentials; do not commit)
  - Libraries: `google-auth` 2.48.0, `google-auth-oauthlib` 1.2.4
  - Secrets location: `.streamlit/secrets.toml` (service account key injected here)

**User Auth:**
- No real authentication - partner selection is a sidebar `st.selectbox` with hardcoded options `["Partner A", "Partner B", "Partner C"]` (`app.py` line 23)
- No session tokens, passwords, or identity verification

## Monitoring & Observability

**Error Tracking:**
- None - no Sentry, Datadog, or similar service detected

**Logs:**
- Streamlit default stdout logging only
- Errors surfaced to UI via `st.error()`, `st.warning()`, `st.caption()`

## CI/CD & Deployment

**Hosting:**
- Target: Streamlit Community Cloud (inferred from `requirements.txt` presence and `.streamlit/secrets.toml` pattern)
- No Dockerfile, Heroku Procfile, or cloud provider config files present

**CI Pipeline:**
- None detected

## Environment Configuration

**Required secrets (in `.streamlit/secrets.toml`):**
- Google Sheets connection credentials (service account JSON or OAuth token)
- Google Sheets spreadsheet URL or ID

**Secrets location:**
- `.streamlit/secrets.toml` - local development (never commit)
- Streamlit Community Cloud: platform secrets manager (mirrors `secrets.toml` keys)

**Credential file at project root:**
- `financegmaildigestkey-12081659191d.json` - Google service account key; must not be committed to version control; should be referenced from `.streamlit/secrets.toml` rather than stored in the repo

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None - all external calls are request/response (yfinance polling, Google Sheets read/write); no event-driven webhooks

---

*Integration audit: 2026-02-18*
