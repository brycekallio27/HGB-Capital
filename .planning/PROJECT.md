# Project Photizo

## What This Is

Project Photizo is HGB Capital's internal investment engine — a Streamlit-based dashboard used by a small group of partners (2–4 people) to track live portfolio performance, run DCF valuations, scan market opportunities, and optimize portfolio allocations. The current app is functional but looks and feels like a default Streamlit prototype. This milestone transforms it into a premium, professional-grade fintech interface worthy of the HGB Capital brand.

## Core Value

Partners can trust the numbers and feel confident sharing the screen — because the app looks as serious as the capital it tracks.

## Current Milestone: v1.0 Premium UI Redesign

**Goal:** Transform the app from a default Streamlit prototype into a premium, professional-grade fintech interface worthy of the HGB Capital brand.

**Target features:**
- Full black/gold design system via CSS injection
- Dark/light mode toggle
- Custom KPI cards for Portfolio War Room
- Plotly charts restyled to brand palette
- Sidebar branding and partner selector overhaul
- Card-based layouts for Analysis Lab and Optimizer tabs
- Typography hierarchy and visual clutter cleanup

## Requirements

### Validated

- ✓ Live portfolio tracking (holdings, market value, P&L, sector) — connected to Google Sheets
- ✓ DCF valuation with adjustable growth/discount sliders — existing
- ✓ Market scanner across 15 blue-chip tickers — existing
- ✓ Portfolio optimizer (Max Sharpe / Min Volatility / Target Return via pypfopt) — existing
- ✓ Watchlist management with write-back to Google Sheets — existing
- ✓ News feed per ticker (yfinance) — existing (fixed)
- ✓ 5-minute caching on all yfinance calls — existing (fixed)
- ✓ Multi-ticker download robustness — existing (fixed)

### Active

- [ ] Premium design system: black (#000000) background, primary gold (#C5A059) accents, muted gold (#9E804B) secondary, applied consistently across the entire app
- [ ] Dark / light mode toggle accessible to all partners
- [ ] Custom Streamlit CSS injection to override default widget styling (buttons, metrics, tabs, sidebar, inputs, dataframes)
- [ ] Visual hierarchy overhaul — clear primary/secondary/tertiary information levels on every tab
- [ ] Portfolio War Room: hero metrics redesigned as large, branded KPI cards (not default st.metric)
- [ ] Charts restyled to match brand palette (Plotly theme: black background, gold traces, no default blue)
- [ ] Sidebar redesigned: HGB Capital branding, partner selector elevated to feel like a real session header
- [ ] Analysis Lab: ticker input and DCF results given a structured, card-based layout
- [ ] Optimizer tab: results displayed in a polished allocation breakdown, not a plain dataframe
- [ ] Typography: tighter heading hierarchy, professional font selection
- [ ] Remove visual clutter: consolidate redundant dividers, reduce excessive whitespace between sections

### Out of Scope

- Real authentication / login system — not in this milestone, marked as future
- New financial features or data sources — UI-only milestone
- Mobile responsiveness — desktop-first, Streamlit limitations accepted
- Backend refactoring — `app.py` monolith stays as-is for now

## Context

The app runs on Streamlit 1.50 with Python 3.9. Streamlit allows custom CSS injection via `st.markdown(..., unsafe_allow_html=True)` — this is the primary mechanism for overriding default styling. Plotly charts use `fig.update_layout()` for theming. The app has no external CSS framework; all styling will be injected inline.

Brand assets:
- Primary Gold: `#C5A059` — eagle icon, "HGB" logotype
- Muted Gold: `#9E804B` — "CAPITAL" secondary text
- Deep Black: `#000000` — logo background, dark mode base
- Dark mode base extended: `#0A0A0A` (app bg), `#111111` (card bg), `#1A1A1A` (border/separator)
- Light mode: `#FAFAFA` (bg), `#FFFFFF` (card bg), `#1A1A1A` (text)

The codebase map is in `.planning/codebase/`. Key concern from CONCERNS.md: in-place DataFrame mutation in `get_portfolio_performance` should be addressed (add `df = df.copy()`) during this milestone as a safe fix alongside styling changes.

## Constraints

- **Tech stack**: Streamlit only — no React, no frontend rewrite, no custom server
- **CSS mechanism**: `st.markdown(unsafe_allow_html=True)` for all custom styles; no external CSS files
- **Compatibility**: Must work with Streamlit Community Cloud deployment target
- **Scope**: UI and styling changes only — financial logic untouched

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Streamlit CSS injection for styling | Only option without rewriting the frontend | — Pending |
| Black/gold brand palette from HGB logo | Gives the app a premium, recognizable identity | — Pending |
| Dark/light mode via session state toggle | Requested by user; Streamlit supports session state switching | — Pending |
| All 3 tabs styled equally | No one tab is more important — partners use all of them | — Pending |

---
*Last updated: 2026-02-18 after milestone v1.0 started*
