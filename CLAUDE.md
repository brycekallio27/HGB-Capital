# Project Photizo — CLAUDE.md

**Last audit:** 2026-03-08

## What This Is

Project Photizo is HGB Capital's internal investment engine — a Streamlit dashboard for 2–4 partners to track live portfolio performance, run DCF valuations, scan market opportunities, and optimize portfolio allocations. Data lives in Google Sheets; market data comes from Yahoo Finance via yfinance.

## Architecture

Single-file monolith: `app.py` (338 lines). All logic — data fetching, financial modeling, UI rendering — lives in one file. No modules, no tests, no logging.

**Stack:** Python 3.9, Streamlit 1.50, yfinance 1.1, pandas, plotly, pypfopt, Google Sheets (via st-gsheets-connection)

**Three-tab interface:**
1. **Portfolio War Room** — Live holdings, KPI scoreboard, pie charts, watchlist
2. **Analysis Lab** — Market scanner (15 blue-chips), DCF valuation, financial history, news feed, add-to-watchlist
3. **Portfolio Optimizer** — Mean-variance optimization via pypfopt (Max Sharpe / Min Vol / Target Return)

## Current Milestone: v1.0 Premium UI Redesign

**Goal:** Transform from default Streamlit prototype into a premium black/gold fintech interface.

**Brand palette:** Black (#0A0A0A bg), Gold (#C5A059 primary), Muted Gold (#9E804B secondary), Light mode: #FAFAFA bg / #FFFFFF cards

**5 Phases, 16 requirements. All 5 phases complete. v1.0 Premium UI Redesign delivered.**

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Design System Foundation (CSS injection, dark/light toggle, Inter font) | 3 plans written, 0 executed |
| 2 | Global Widget Overrides (buttons, tabs, inputs, dataframes) | Not started |
| 3 | Portfolio War Room redesign (KPI cards, Plotly theming) | Not started |
| 4 | Sidebar branding (HGB Capital header, partner selector) | Not started |
| 5 | Analysis Lab & Optimizer polish (card layouts, result cards) | Not started |

Phase 1 plans are in `.planning/phases/01-design-system-foundation/`:
- `01-01-PLAN.md` — Create `.streamlit/config.toml` (Inter font + dark base)
- `01-02-PLAN.md` — Add DARK_CSS/LIGHT_CSS constants + `inject_css()` to app.py
- `01-03-PLAN.md` — Dark/light toggle + semantic P&L colors + DataFrame `.copy()` fix

## What's Working

- **Google Sheets connection** — reads Portfolio + Watchlist worksheets; write-back for watchlist works
- **Portfolio display** — holdings table with live prices, market value, P&L, sector, return %
- **KPI scoreboard** — Total Equity, Unrealized P&L, Active Positions via st.metric
- **Pie charts** — Holdings by size and Risk by sector (Plotly)
- **DCF valuation** — 5-year DCF with adjustable growth/discount sliders, beta-adjusted smart discount
- **Market scanner** — scans 15 blue-chip tickers for discounts (>10% off 52-week high or P/E < 25)
- **Portfolio optimizer** — Mean-variance optimization with three strategies, bar chart + table output
- **News feed** — latest 3 articles per ticker via yfinance
- **5-minute caching** — all yfinance calls cached with @st.cache_data(ttl=300)

## What's Broken / Needs Immediate Attention

### Critical Bugs

1. **DataFrame mutation bug** — `get_portfolio_performance()` mutates its input DataFrame in-place while decorated with `@st.cache_data`. Can cause stale/corrupt cached data. **Fix:** Add `df = df.copy()` at function start. (Planned for Phase 1, Plan 03)

2. **Division-by-zero risk** — Line 176: P&L % divides by `total_equity` which could be NaN if upstream prices are missing. The `if total_equity > 0` guard doesn't catch NaN.

3. **Bare `except` clauses everywhere** — Lines 39, 85, 106, 118, 135, 202, 280, 293. All errors swallowed silently. Debugging is impossible.

### Security Issues

4. **No input validation** — Ticker inputs (lines 220, 298) passed directly to yfinance unsanitized. Watchlist notes (line 273) written to Google Sheets without CSV injection prevention.

5. **Service account key on disk** — `financegmaildigestkey-*.json` contains a private key. It IS gitignored (line 8 of `.gitignore`) and has never been committed. Risk is accidental de-ignoring or sharing the project folder directly.

6. **No authentication** — Partner selector is a fake selectbox. Anyone with the URL can impersonate any partner and write to the shared Sheets.

### Performance Issues

7. **Sequential HTTP calls** — Per-ticker `.info` calls in `get_portfolio_performance` (line 53) and `scan_market_opportunities` (line 124). Portfolio with N holdings = N blocking HTTP requests. Market scan = 15 sequential requests (15–30 seconds).

8. **Portfolio data read twice** — `conn.read(worksheet="Portfolio")` called independently in Tab 1 (line 169) and Tab 3 (line 290).

### Tech Debt

9. **Unpinned dependencies** — `requirements.txt` has no version pins. yfinance breaks frequently on upstream changes.
10. **Zero test coverage** — No test files exist. Financial calculations (DCF, optimization) completely unvalidated.
11. **Zero logging** — No file/console logging anywhere. All feedback is UI-only.
12. **DCF doesn't handle negative FCF** — Growth companies with negative FCF produce negative intrinsic values displayed without warning.
13. **Google Sheets = single point of failure** — Connection failure calls `st.stop()`, killing the entire app including tabs that don't need Sheets.

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Entire application (338 lines) |
| `requirements.txt` | Dependencies (unpinned) |
| `.streamlit/secrets.toml` | Google Sheets credentials (gitignored) |
| `financegmaildigestkey-*.json` | GCP service account key for Sheets API |
| `.planning/PROJECT.md` | v1.0 milestone vision + brand guidelines |
| `.planning/REQUIREMENTS.md` | 16 requirements mapped to 5 phases |
| `.planning/ROADMAP.md` | 5-phase roadmap with success criteria |
| `.planning/STATE.md` | Current progress tracker |
| `.planning/codebase/CONCERNS.md` | Full tech debt + security audit |
| `.planning/phases/01-*/` | Phase 1 plans (3 task plans, context, research) |

## Tools in Repo

- **get-shit-done/** — GSD meta-prompting system (separate git repo). Used to structure v1.0 planning. Commands: `/gsd:new-project`, `/gsd:plan-phase`, `/gsd:execute-phase`, etc.
- **ui-ux-pro-max-skill/** — Claude Code design intelligence skill. Searchable database of UI styles, palettes, fonts, chart types. BM25 search engine.

## Key Decisions (Captured)

- CSS injection via `st.html()` preferred in Streamlit 1.50; fallback to `st.markdown(unsafe_allow_html=True)`
- Two separate CSS constants (DARK_CSS, LIGHT_CSS) over parameterized f-strings
- Plotly theming: `plotly_dark`/`plotly_white` as base, overridden per-figure via `fig.update_layout()`
- Dark/light toggle: sun/moon icon, top of sidebar, defaults to dark, session state only
- Font: Google Fonts Inter with tabular numerals
- Scope: UI/styling only — financial logic untouched in v1.0

## Blockers / Risks

- `data-testid` CSS selectors are medium confidence for Streamlit 1.50 — need verification in live browser DevTools
- `st.html()` sandboxing: if CSS injection has no effect, fall back to `st.markdown(unsafe_allow_html=True)`
- Community Cloud font loading: must use Google Fonts `<link>` tag (not `@font-face`) to avoid CSP issues
- yfinance is an unofficial scraper — breaks without notice on Yahoo layout changes

## Running Locally

```bash
cd "Project Photizo"
source venv/bin/activate
streamlit run app.py
# Requires .streamlit/secrets.toml with Google Sheets credentials
# Runs on localhost:8501
```

## Out of Scope (v1.0)

- Real authentication (deferred to v2)
- Mobile responsiveness
- Backend refactoring (monolith stays)
- New financial features
- Test coverage (deferred)
