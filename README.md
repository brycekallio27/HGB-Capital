# Project Photizo

An investment operations dashboard I built for a small private investment partnership (HGB Capital) — live portfolio tracking, DCF valuation, a thesis-driven market scanner, and mandate-based allocation optimization, all backed by a Google Sheet the partners already update by hand.

## Why I built this

A few of us pool capital and needed a shared source of truth that was more useful than a spreadsheet but didn't require standing up brokerage API integrations or handing anyone new infrastructure to maintain. Photizo reads directly from the Google Sheet the partners already use, layers real market data and analysis on top of it (via `yfinance`), and turns "where do we stand and what should we do next" into an actual dashboard instead of a periodic manual review.

## What it does

- **Portfolio War Room** — live performance, P&L, and holdings pulled from the shared Google Sheet
- **Analysis Lab** — DCF valuation, a market opportunity scanner, and a thesis-driven Market Radar (theme-based screens like AI Compute, GLP-1/Metabolic Health, Infrastructure — plus anchor-ticker expansion, e.g. entering NVDA pulls in its supply chain)
- **Allocation Dashboard** — three preset risk mandates (Balanced Growth / Aggressive Growth / Conservative Income), each with equity/bond sleeve caps, run through `PyPortfolioOpt` to produce expected return, volatility, Sharpe, and a dollar-denominated rebalance plan against the current portfolio
- **News Cross-Check** — per-holding sentiment and named risk flags (lawsuits, investigations, SEC probes, downgrades) sourced from `yfinance`, Google News, and SEC EDGAR
- **Team watchlist** — shared across partners, with per-row ownership (only the person who added an entry can edit/delete it) and independent per-partner starring
- **Auth** — real email/password + 2FA via Clerk, not a shared PIN. A partner signs in on a small Next.js landing site, which mints a short-lived JWT and hands off into the dashboard; the dashboard verifies that token server-side against Clerk's JWKS before rendering anything

## Tech stack

| Layer | Technology |
|---|---|
| Dashboard | Python 3.11 + Streamlit |
| Market data | yfinance, Google News, SEC EDGAR |
| Portfolio optimization | PyPortfolioOpt |
| Data viz | Plotly |
| Data source | Google Sheets (`st-gsheets-connection`) — partners edit the sheet directly, the app reads from it |
| Auth | Clerk (email/password + 2FA), JWT verified server-side with `PyJWT` against Clerk's JWKS |
| Landing / auth gate | Next.js 15 + Tailwind, deployed to Netlify |
| Testing | pytest — unit tests on the allocation optimizer, radar, and watchlist logic |

## Architecture

Two deployables, one JWT handoff between them — there's no local password or PIN fallback anywhere:

```
Partner's browser
      │
      ▼
landing/ (Next.js, Netlify)  ──Clerk sign-in (email/password + 2FA)──▶  Clerk
      │
      │  mints short-lived session JWT, redirects with ?clerk_token=...
      ▼
app.py (Streamlit, Streamlit Community Cloud)
      │  verifies JWT against Clerk JWKS, matches email → partner record
      ▼
photizo/ modules (allocation, models, radar, sentiment, watchlist, ui)
      │
      ▼
Google Sheets  (portfolio holdings + shared watchlist, 5-minute cache)
```

## Project structure

```
app.py                  # Auth gate, tab routing, UI assembly
photizo/
├── allocation.py        # Mandate profiles, sleeve universe, optimizer, rebalance math
├── models.py             # Portfolio performance, DCF, market scanner
├── radar.py               # Thesis-driven market radar
├── sentiment.py            # Keyword-based news sentiment scoring
├── ui.py                    # CSS + Plotly styling, HTML card generators
└── watchlist.py              # Shared team watchlist with per-row ownership
tests/                   # pytest suite for allocation, models, radar, watchlist
landing/                 # Next.js + Clerk sign-in gate (deployed separately)
```

## Current status

Actively used, not a finished product. What's solid: the Clerk auth flow, Google Sheets read/write with caching, the allocation optimizer with sleeve constraints, and unit test coverage on the core financial logic. What's known and intentionally deferred:

- News sentiment is a finance-flavored keyword lexicon, not a hosted NLP model
- Bond pricing uses historical price returns rather than yield-curve/duration modeling
- Google Sheets is a single dependency — if that connection fails, the whole app stops rather than degrading gracefully

## Running locally

You'll need both pieces running, since the dashboard only accepts a verified Clerk token:

```bash
# Dashboard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml   # fill in your own Google Sheets + Clerk config
streamlit run app.py          # localhost:8501

# Landing / auth gate
cd landing
npm install
cp .env.local.example .env.local   # fill in your own Clerk keys
npm run dev                    # localhost:3000
```

Sign in at `localhost:3000` — it redirects into the dashboard already authenticated.

```bash
# Run the test suite
pytest
```
