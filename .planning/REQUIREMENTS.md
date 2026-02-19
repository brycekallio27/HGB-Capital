# Requirements: Project Photizo

**Defined:** 2026-02-18
**Core Value:** Partners can trust the numbers and feel confident sharing the screen — because the app looks as serious as the capital it tracks.

## v1.0 Requirements

Requirements for milestone v1.0 — Premium UI Redesign. Each maps to roadmap phases.

### Design System

- [ ] **DSYS-01**: App displays with black (`#0A0A0A`) background and gold (`#C5A059`) accent colors applied globally across all elements
- [ ] **DSYS-02**: Partners can toggle between dark mode and light mode using a control accessible from any tab
- [ ] **DSYS-03**: All default Streamlit widget styles (buttons, tabs, inputs, dataframes, spinners) are overridden to match brand palette via CSS injection
- [ ] **DSYS-04**: App uses Inter or DM Sans font (loaded via Google Fonts) with tabular numerals (`font-variant-numeric: tabular-nums`) for all dollar values and numeric data
- [ ] **DSYS-05**: Positive P&L values display in semantic green, negative values display in semantic red (independent of brand gold)

### Portfolio War Room

- [ ] **PORT-01**: Hero metrics on the Portfolio tab display as custom branded KPI cards with gold left-border accent stripe and styled delta pills — replacing default `st.metric` widgets
- [ ] **PORT-02**: All Plotly charts display with transparent/dark background, gold primary traces, muted dark gridlines (`#1A1A1A`), no Plotly toolbar, and consistent axis font styling
- [ ] **PORT-03**: Holdings dataframe styled to the dark theme — no white background, alternating row shading, tabular-aligned number columns

### Sidebar

- [ ] **SBAR-01**: Sidebar displays HGB Capital branding (logo/wordmark treatment) as a styled header at the top of the sidebar
- [ ] **SBAR-02**: Partner selector is styled as a prominent session-header element, elevated above plain selectbox treatment

### Analysis & Optimizer

- [ ] **ANLS-01**: Analysis Lab ticker input, sliders, and controls are organized within a structured card layout (not raw Streamlit widgets on white)
- [ ] **ANLS-02**: DCF valuation output renders in a styled result card with clear data hierarchy (value dominant, label recessive)
- [ ] **ANLS-03**: Portfolio Optimizer allocation results render as a polished visual breakdown — not a raw dataframe — with clear weighting display per ticker

### Polish

- [ ] **PLSH-01**: Clear visual hierarchy established across every tab — primary (live data values), secondary (labels), tertiary (metadata/footnotes) text levels are visually distinct
- [ ] **PLSH-02**: Redundant `st.divider()` calls consolidated and excessive vertical whitespace between sections removed across all tabs
- [ ] **PLSH-03**: In-place DataFrame mutation bug in `get_portfolio_performance` patched with `df = df.copy()` at function entry

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Authentication

- **AUTH-01**: Partners log in with individual credentials (not shared access)
- **AUTH-02**: Session is tied to partner identity for audit trail

### Mobile

- **MOBL-01**: App layout adapts to tablet/mobile viewports
- **MOBL-02**: Touch-friendly controls for sliders and selectors

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real authentication / login system | Adds backend complexity; out of scope for UI milestone |
| New financial features or data sources | UI-only milestone — no new financial logic |
| Mobile responsiveness | Desktop-first; Streamlit layout limitations accepted |
| Backend refactoring of `app.py` monolith | Deferred; only the DataFrame copy fix is a safe exception |
| Custom server or React frontend | Streamlit constraint — no server-side rendering changes |

## Traceability

Which phases cover which requirements. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DSYS-01 | — | Pending |
| DSYS-02 | — | Pending |
| DSYS-03 | — | Pending |
| DSYS-04 | — | Pending |
| DSYS-05 | — | Pending |
| PORT-01 | — | Pending |
| PORT-02 | — | Pending |
| PORT-03 | — | Pending |
| SBAR-01 | — | Pending |
| SBAR-02 | — | Pending |
| ANLS-01 | — | Pending |
| ANLS-02 | — | Pending |
| ANLS-03 | — | Pending |
| PLSH-01 | — | Pending |
| PLSH-02 | — | Pending |
| PLSH-03 | — | Pending |

**Coverage:**
- v1.0 requirements: 16 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 16 ⚠️

---
*Requirements defined: 2026-02-18*
*Last updated: 2026-02-18 after initial definition*
