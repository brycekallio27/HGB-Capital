# Project Photizo — CLAUDE.md

**Last audit:** 2026-08-25

## What This Is

Project Photizo is HGB Capital's internal investment engine for 2-4 partners (Bryce, Hunter, Grayson) to track live portfolio performance, run DCF valuations, scan market opportunities, cross-reference holdings against news/risk flags, and optimize allocation across equity/bond sleeves. Portfolio data lives in Google Sheets (never connects to Fidelity or any brokerage directly) — partners update the sheet manually, the app reads from it. Market data comes from Yahoo Finance via `yfinance`.

## Architecture

Two deployables, one JWT handoff between them:

1. **`app.py` + `photizo/`** — the Streamlit dashboard. Deployed to Streamlit Community Cloud.
2. **`landing/`** — a Next.js app using Clerk for real email/password (+ 2FA) sign-in. Deployed to Netlify. This is the *only* way in — there is no local/PIN fallback.

**Auth flow:** partner visits the Netlify-hosted landing page → signs in via Clerk's `<SignIn>` component → landing page's `/dashboard` route mints a short-lived Clerk session JWT and redirects to the Streamlit URL with `?clerk_token=...` → `app.py` verifies that JWT against Clerk's JWKS (`_verify_clerk_token`), matches the verified email against `[partners.*].email` in `secrets.toml` (`_partner_session_from_claims`), and only then renders the dashboard. No token or unmatched email → user sees only the "Sign In With Clerk" gate.

**Stack:** Python 3.11, Streamlit 1.50, yfinance, pandas, plotly, PyPortfolioOpt (`pypfopt` import, `PyPortfolioOpt` PyPI package — easy to get wrong in requirements.txt), PyJWT[crypto], Google Sheets via `st-gsheets-connection`. Next.js 15 + Clerk + Tailwind for the landing app.

**`photizo/` module layout** (app.py imports from these; each is independently testable):
- `allocation.py` — mandate profiles, sleeve universe, optimizer, rebalance math
- `models.py` — portfolio performance, DCF, market scanner, optimizer (legacy mean-variance)
- `radar.py` — thesis-driven market radar (themes, anchor ticker expansion)
- `sentiment.py` — keyword-based news sentiment scoring (not a real NLP model — see Open Follow-ups in `PARTNER_NOTES.md`)
- `ui.py` — CSS constants (`DARK_CSS`/`LIGHT_CSS`), Plotly layout defaults, HTML card generators. Single source of truth for styling — `app.py` no longer has its own inline copy.
- `watchlist.py` — shared team watchlist with per-row ownership + per-partner star tracking

**Four workspaces in the app:** Portfolio War Room, Analysis Lab (DCF, market scanner, radar), Portfolio Optimizer, Allocation Dashboard (mandate-based sleeve allocation + rebalance deltas + per-ticker News Cross-Check with risk flags).

## What's Working

- Clerk email/password + 2FA auth gate, JWT-verified server-side
- Google Sheets portfolio + watchlist read/write, 5-minute cache
- News Cross-Check: per-ticker sentiment + risk flags (lawsuit, investigation, SEC probe, downgrade) for whatever's currently held, sourced from yfinance + Google News + SEC EDGAR
- Allocation Dashboard: three risk-mandate presets, sleeve caps, rebalance buy/sell deltas in dollar terms
- Dark/light theme toggle, black/gold HGB brand styling throughout
- 35 passing unit tests covering `allocation`, `models`, `radar`, `watchlist`

## Known Gaps (see `PARTNER_NOTES.md` → Open Follow-ups for detail)

- Sentiment is a finance-flavored keyword list, not a hosted model
- News Cross-Check capped at 8 tickers/run for responsiveness
- Bond pricing uses price-return history, not yield-curve/duration modeling
- No test coverage on `allocation.py`'s sleeve constraint solver (has tests now, but not for every edge case) or `sentiment.py`
- Google Sheets is a single point of failure — connection failure stops the whole app, not just the tab that needs it
- Placeholder partner emails (`hunter@email.com`, `grayson@email.com`) in `secrets.toml` need updating to real addresses before Clerk email-matching works for Hunter and Grayson

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Auth gate + tab routing + UI assembly |
| `photizo/*.py` | Financial logic, CSS, UI helpers (see Architecture above) |
| `requirements.txt` | Pinned-ish deps for the Streamlit deploy |
| `.streamlit/secrets.toml` | Google Sheets creds + `[clerk]` config + `[partners.*]` email map (gitignored, never committed) |
| `.streamlit/secrets.example.toml` | Template for the above — placeholders only, no real values |
| `landing/` | Next.js + Clerk sign-in gate, deployed separately to Netlify |
| `landing/netlify.toml` | Netlify build config (base dir `landing`) |
| `PARTNER_NOTES.md` | How auth/watchlist/allocation actually work today, partner-facing |
| `TASKS.md` | Active/done task tracking |
| `.planning/codebase/CONCERNS.md` | Remaining tech debt (trimmed to what's still true) |

## Running Locally

```bash
cd "HGB Capital"
./venv/bin/python -m streamlit run app.py
# Requires .streamlit/secrets.toml with real Google Sheets + Clerk config
# Runs on localhost:8501 — you'll only see the Clerk gate unless a valid
# clerk_token is passed in via query param (i.e. run landing/ too, or test
# against the deployed Netlify + Streamlit Cloud pair)
```

```bash
cd "HGB Capital/landing"
npm install && npm run dev
# Requires landing/.env.local with real Clerk keys
# Runs on localhost:3000
```

## Out of Scope (current milestone)

- Mobile responsiveness
- Backend refactoring beyond the existing `photizo/` split
- New financial features
- Real NLP-based sentiment (flagged as a follow-up, not started)
