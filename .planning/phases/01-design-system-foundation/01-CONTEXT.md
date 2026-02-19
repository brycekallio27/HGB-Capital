# Phase 1: Design System Foundation - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the CSS injection infrastructure that all subsequent phases depend on: global black/gold palette, Inter font with tabular numerals, dark/light mode toggle with session persistence, semantic green/red P&L colors, and the DataFrame mutation bug fix in `get_portfolio_performance`. No component-level styling in this phase — that is Phases 2–5.

</domain>

<decisions>
## Implementation Decisions

### Dark/Light Mode Toggle
- Toggle lives at the **top of the sidebar**, above the partner selector and nav elements
- Toggle uses a **sun/moon icon** — icon-only, minimal footprint
- App defaults to **the last mode used** — persists across the current browser session via `st.session_state`
- Persistence is **per-session only** — resets to default on browser refresh (no cookie/URL param workaround needed)
- Dark mode is the brand default when no session preference exists yet

### Claude's Discretion
- Exact icon choice for sun/moon (emoji vs SVG vs Unicode character)
- CSS injection method (`st.html()` vs `st.markdown(unsafe_allow_html=True)`) — use whichever is cleanest for Streamlit 1.50
- Light mode palette implementation (PROJECT.md defines: #FAFAFA bg, #FFFFFF card bg, #1A1A1A text)
- Exact green/red hex values for semantic P&L colors — standard fintech conventions acceptable
- Font fallback stack if Google Fonts unavailable
- Whether to use separate DARK_CSS / LIGHT_CSS constants or a parameterized approach

</decisions>

<specifics>
## Specific Ideas

- Toggle should feel minimal — sun/moon icon, not a labeled button. Doesn't need a text label.
- Dark mode is the primary experience; light mode is an option, not the default.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-design-system-foundation*
*Context gathered: 2026-02-18*
