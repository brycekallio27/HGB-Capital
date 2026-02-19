# Roadmap: Project Photizo

## Overview

Five phases transform the HGB Capital investment engine from a default Streamlit prototype into a premium fintech interface. The build order follows the CSS dependency graph: the injection infrastructure and design tokens come first, then global widget overrides, then the high-traffic Portfolio War Room, then the sidebar, then the Analysis Lab and Optimizer tabs. Every visual feature in later phases depends on Phase 1 existing; nothing in Phase 3 can be called "done" without Phase 2's global overrides already applied.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Design System Foundation** - CSS injection infrastructure, config.toml, Inter font, dark/light toggle, semantic P&L colors, DataFrame mutation bug fix
- [ ] **Phase 2: Global Widget Overrides** - All Streamlit widget styles overridden (buttons, tabs, inputs, dataframes, spinners), visual hierarchy established, dividers consolidated
- [ ] **Phase 3: Portfolio War Room** - Custom KPI cards replace st.metric, Plotly charts restyled to brand palette, holdings dataframe styled to dark theme
- [ ] **Phase 4: Sidebar** - HGB Capital branding header, partner selector elevated to session-header treatment
- [ ] **Phase 5: Analysis Lab and Optimizer** - Card-based layouts for Analysis Lab controls and DCF results, polished allocation breakdown for Optimizer

## Phase Details

### Phase 1: Design System Foundation
**Goal**: The brand's CSS infrastructure is running — every subsequent phase has a stable, correct base to build on
**Depends on**: Nothing (first phase)
**Requirements**: DSYS-01, DSYS-02, DSYS-04, DSYS-05, PLSH-03
**Success Criteria** (what must be TRUE):
  1. Opening the app shows a black (`#0A0A0A`) background with gold (`#C5A059`) accent elements — no default Streamlit light theme visible anywhere
  2. Partners can click a dark/light toggle in the sidebar and the full app repaints immediately to the alternate palette
  3. All numeric data (dollar values, percentages) renders in Inter with tabular-nums alignment — decimal points column-align in all contexts
  4. Positive P&L values display in semantic green and negative values in semantic red, regardless of brand gold usage elsewhere
  5. The DataFrame mutation bug in `get_portfolio_performance` is patched — `df.copy()` is the first operation in that function
**Plans**: TBD

### Phase 2: Global Widget Overrides
**Goal**: Every standard Streamlit widget across the entire app matches the HGB brand palette, and layout clutter is cleaned up globally
**Depends on**: Phase 1
**Requirements**: DSYS-03, PLSH-01, PLSH-02
**Success Criteria** (what must be TRUE):
  1. Buttons, tabs, selectboxes, text inputs, sliders, dataframes, and spinners show no default Streamlit blue — all interactive elements use brand gold on dark surfaces
  2. Active tab is clearly distinguishable from inactive tabs via gold underline, not default gray
  3. A clear three-level text hierarchy is visible on every tab: primary data values dominate, secondary labels recede, tertiary metadata (footnotes, captions) are visually subordinate
  4. Redundant dividers and excessive vertical whitespace between sections are removed — sections are separated by spacing and typography, not repeated horizontal rules
**Plans**: TBD

### Phase 3: Portfolio War Room
**Goal**: Partners experience the Portfolio tab as a premium financial dashboard — live data reads as intentional and trustworthy, not default library output
**Depends on**: Phase 2
**Requirements**: PORT-01, PORT-02, PORT-03
**Success Criteria** (what must be TRUE):
  1. Hero metrics display as branded KPI cards with a gold left-border accent stripe and styled delta pills — no default `st.metric` widgets remain on the Portfolio tab
  2. All Plotly charts display with transparent or dark backgrounds matching the app surface, gold primary traces, muted dark gridlines, and no visible Plotly toolbar
  3. The holdings dataframe has no white background — rows alternate at low contrast on dark surfaces, number columns are tabular-aligned, and column headers read as intentional labels
**Plans**: TBD

### Phase 4: Sidebar
**Goal**: The sidebar reads as an institutional product's navigation header, not a default Streamlit control panel
**Depends on**: Phase 1
**Requirements**: SBAR-01, SBAR-02
**Success Criteria** (what must be TRUE):
  1. The top of the sidebar displays a styled HGB Capital wordmark or logotype treatment in brand gold — not plain `st.header` text
  2. The partner selector is visually elevated above a plain selectbox — the selected partner name reads as a session identity indicator, prominent and styled
**Plans**: TBD

### Phase 5: Analysis Lab and Optimizer
**Goal**: The Analysis Lab and Optimizer tabs deliver their results in structured, premium layouts — no raw Streamlit widgets on white
**Depends on**: Phase 2
**Requirements**: ANLS-01, ANLS-02, ANLS-03
**Success Criteria** (what must be TRUE):
  1. Analysis Lab ticker input, sliders, and controls are visually contained within a card structure — they do not sit as unframed widgets on the raw page background
  2. DCF valuation output renders in a styled result card where the intrinsic value number is visually dominant and labels are clearly subordinate
  3. Portfolio Optimizer allocation results display as a visual breakdown per ticker — not a raw dataframe — where each ticker's weighting is clearly readable at a glance
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

Note: Phase 4 (Sidebar) depends on Phase 1 only and could run in parallel with Phases 2–3 in principle, but is sequenced after Phase 3 for linear execution.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Design System Foundation | 0/? | Not started | - |
| 2. Global Widget Overrides | 0/? | Not started | - |
| 3. Portfolio War Room | 0/? | Not started | - |
| 4. Sidebar | 0/? | Not started | - |
| 5. Analysis Lab and Optimizer | 0/? | Not started | - |

---
*Roadmap created: 2026-02-18*
*Milestone: v1.0 — Premium UI Redesign*
