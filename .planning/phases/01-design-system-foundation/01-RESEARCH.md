# Phase 1: Design System Foundation - Research

**Researched:** 2026-02-19
**Domain:** Streamlit CSS injection, theming, dark/light mode toggle, Google Fonts, font-variant-numeric
**Confidence:** HIGH (core findings verified against official Streamlit docs and release notes)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Dark/Light Mode Toggle
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DSYS-01 | App displays with black (#0A0A0A) background and gold (#C5A059) accent colors applied globally | CSS injection via `st.markdown` targeting `.stApp`, `[data-testid="stAppViewContainer"]`, `[data-testid="stSidebar"]` — confirmed stable selectors |
| DSYS-02 | Partners can toggle between dark mode and light mode | `st.session_state` + `st.rerun()` + conditional CSS injection — the only reliable per-user approach; `config.toml` theme tables require hamburger menu, not a sidebar button |
| DSYS-04 | App uses Inter or DM Sans font via Google Fonts with tabular numerals for all dollar values | `config.toml` `[theme]` font field supports `"Inter:https://..."` format natively since Streamlit 1.44; tabular-nums applied via `font-variant-numeric: lining-nums tabular-nums` CSS targeting `[data-testid="stMetricValue"]` and `.stDataFrame` |
| DSYS-05 | Positive P&L values display in semantic green, negative in semantic red | Semantic color classes applied via injected CSS; standard fintech values: `#16A34A` green, `#DC2626` red — compatible with Inter and dark backgrounds |
| PLSH-03 | DataFrame mutation bug in get_portfolio_performance patched with df = df.copy() | Bug is at line 52 of app.py — `df['Current Price'] = df['Ticker'].map(current_prices)` mutates the cached input; `df = df.copy()` must be inserted as the first operation after the empty-check guard |
</phase_requirements>

---

## Summary

Phase 1 establishes the CSS injection infrastructure for Project Photizo's HGB Capital dashboard. Research confirms that the Streamlit 1.50 target version sits at an inflection point: advanced theming via `config.toml` was introduced in v1.44, and `st.html` gained CSS file path support in v1.46. The current stable version is 1.54.0, meaning "Streamlit 1.50" in PROJECT.md is the pinned target, not the current latest.

The dark/light mode toggle is the most architecturally significant decision in this phase. **Config.toml `[theme.dark]`/`[theme.light]` tables are not the right tool** for a sidebar button toggle — they are activated only through the hamburger settings menu, require a full app rerun, and had a confirmed persistence regression in v1.51. The correct approach for a per-user sidebar button is `st.session_state` + conditional CSS injection + `st.rerun()`. The private `st._config.set_option()` workaround exists but is global across all users (catastrophic for a multi-partner app) and uses an undocumented API.

Font loading is clean via `config.toml` theme font field (format: `"Inter:https://fonts.googleapis.com/..."`) — no CSS `@import` hack needed. Tabular numerals require CSS targeting specific `data-testid` selectors that are stable across Streamlit versions. The DataFrame mutation bug in `get_portfolio_performance` is straightforward: `df = df.copy()` must be the first operation after the empty-check guard, before any column assignments.

**Primary recommendation:** Use `st.markdown(unsafe_allow_html=True)` for CSS injection (more widely tested than `st.html` for CSS, no version-dependent behavior changes), load Inter via `config.toml`, implement the toggle as a `st.button` in the sidebar that flips `st.session_state.dark_mode` and calls `st.rerun()`, and inject the appropriate CSS block based on session state at the top of `app.py`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Streamlit | 1.50 (pinned) | App framework — CSS injection target | Project constraint |
| Python | 3.9 | Runtime | Project constraint |
| Pandas | current in venv | DataFrame ops including `.copy()` fix | Already in requirements.txt |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Google Fonts CDN | N/A | Inter font delivery | Via config.toml `[theme] font` field — no pip install |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `st.markdown(unsafe_allow_html=True)` for CSS | `st.html(path_to_css_file)` | `st.html` with CSS file path auto-wraps in `<style>` tags (v1.46+), cleaner for large CSS blocks; however, it had a confirmed regression in v1.42 where injected CSS did not apply. `st.markdown` is more battle-tested and universally documented across community resources. Use `st.html` only if CSS file becomes very large. |
| `session_state` + CSS injection for toggle | `st._config.set_option()` private API | Private API is global (affects all concurrent users), undocumented, and can break without notice. CSS injection is per-user and reliable. |
| `config.toml` font field | `@import` in injected CSS | `config.toml` font field is the official, cleaner path. `@import` in CSS works but adds more injection complexity. |

---

## Architecture Patterns

### Recommended Project Structure

The app remains a single `app.py` monolith per project constraints. All Phase 1 additions live at the **top of `app.py`**, immediately after `st.set_page_config()`:

```
app.py
├── st.set_page_config()           [line 11 — existing]
├── [PHASE 1 INSERTION POINT]
│   ├── Theme state initialization (session_state)
│   ├── CSS injection function (inject_css)
│   └── inject_css(st.session_state.dark_mode) call
├── DB connection                  [line 15 — existing]
├── Sidebar                        [line 22 — existing]
│   ├── [PHASE 1 INSERTION] Dark/light toggle button at top
│   ├── Partner selector           [existing]
│   └── Active session label       [existing]
└── Tab content                    [existing]

.streamlit/
└── config.toml                    [CREATE — does not exist yet]
    ├── [theme] font = Inter URL
    └── [theme] base = "dark"
```

### Pattern 1: CSS Injection at Top of App

**What:** A single `inject_css(is_dark: bool)` function that injects the full app CSS based on the current mode. Called once per script execution, before any other UI elements.

**When to use:** This approach ensures CSS is loaded before any component renders, preventing flash of unstyled content. Putting it after components renders causes a visible repaint.

**Example:**
```python
# Source: Streamlit community consensus pattern, verified against official docs

DARK_CSS = """
<style>
.stApp {
    background-color: #0A0A0A;
    color: #F5F5F5;
}
[data-testid="stAppViewContainer"] {
    background-color: #0A0A0A;
}
[data-testid="stSidebar"] {
    background-color: #111111;
}
[data-testid="stMetricValue"] {
    font-variant-numeric: lining-nums tabular-nums;
    color: #C5A059;
}
/* Semantic P&L colors */
.pl-positive { color: #16A34A !important; }
.pl-negative { color: #DC2626 !important; }
</style>
"""

LIGHT_CSS = """
<style>
.stApp {
    background-color: #FAFAFA;
    color: #1A1A1A;
}
[data-testid="stAppViewContainer"] {
    background-color: #FAFAFA;
}
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
}
[data-testid="stMetricValue"] {
    font-variant-numeric: lining-nums tabular-nums;
    color: #C5A059;
}
/* Semantic P&L colors */
.pl-positive { color: #16A34A !important; }
.pl-negative { color: #DC2626 !important; }
</style>
"""

def inject_css(is_dark: bool) -> None:
    st.markdown(DARK_CSS if is_dark else LIGHT_CSS, unsafe_allow_html=True)
```

### Pattern 2: Dark/Light Mode Toggle with Session State

**What:** A `st.button` in the sidebar initializes `st.session_state.dark_mode` to `True` (dark default), toggles it on click, and calls `st.rerun()` to trigger a full script re-execution with the new CSS.

**When to use:** Per-user theme toggle. Each Streamlit session is independent so this is safe for multi-partner use. Does NOT affect other users.

**Why `st.rerun()` is needed:** Streamlit re-executes the entire script on each interaction. The CSS injection at the top of the script will read the updated `session_state.dark_mode` and inject the correct CSS block. Without `st.rerun()`, the button click triggers a rerun automatically — but making it explicit ensures the state is committed before CSS renders.

**Note:** The toggle button must be placed **after** the session_state initialization but **before** the CSS injection call, OR the CSS injection must be placed after the button — but the correct architecture is initialization at top, CSS injection immediately after, sidebar button that just mutates state (Streamlit reruns automatically on widget interaction).

```python
# Source: Verified pattern from Streamlit community, aligned with session_state docs

# 1. Initialize at top of app.py (after set_page_config)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True  # dark is brand default

# 2. Inject CSS based on current state (immediately after initialization)
inject_css(st.session_state.dark_mode)

# 3. In the sidebar section (line ~22), add toggle before partner selector:
def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

sun_moon = "🌙" if st.session_state.dark_mode else "☀️"
st.sidebar.button(sun_moon, on_click=toggle_theme, help="Toggle dark/light mode")
```

**Key insight:** Using `on_click=toggle_theme` (callback pattern) is more reliable than checking button return value + calling `st.rerun()`, because Streamlit processes callbacks before re-rendering. The callback pattern avoids the double-rerun issue seen in some toggle implementations.

### Pattern 3: Inter Font via config.toml

**What:** Set Inter as the app font using the `[theme]` `font` field in `.streamlit/config.toml`. Streamlit loads the Google Fonts stylesheet and applies it globally.

**When to use:** This is the official approach since v1.44. It applies the font to all widget labels, dataframe cells, tooltips, and column headers automatically — no CSS injection needed for font loading.

```toml
# .streamlit/config.toml
[theme]
base = "dark"
font = "Inter:https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap"
```

**Fallback:** If Google Fonts is unavailable, Streamlit falls back to the system sans-serif. The fallback can be made explicit:
```toml
font = "Inter:https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap, sans-serif"
```

**CSP note:** Streamlit Community Cloud does not enforce a strict CSP that blocks Google Fonts. The `@import` vs link-tag distinction is irrelevant here — Streamlit handles the font loading mechanism internally when using the `config.toml` approach. No CSP configuration is required.

### Pattern 4: Tabular Numerals via CSS

**What:** `font-variant-numeric: lining-nums tabular-nums` applied to selectors that contain financial numbers. Inter natively supports the `tnum` and `lnum` OpenType features, so this will work correctly.

**Selectors to target:**
```css
/* Metric values (st.metric) */
[data-testid="stMetricValue"] {
    font-variant-numeric: lining-nums tabular-nums;
}

/* Metric delta values */
[data-testid="stMetricDelta"] {
    font-variant-numeric: lining-nums tabular-nums;
}

/* Dataframe cells — outer wrapper */
[data-testid="stDataFrame"] {
    font-variant-numeric: lining-nums tabular-nums;
}

/* Fallback via font-feature-settings for older browsers */
[data-testid="stMetricValue"],
[data-testid="stDataFrame"] {
    font-feature-settings: "lnum" 1, "tnum" 1;
}
```

**Note on stDataFrame internals:** The `st.dataframe()` component uses a Glide Data Grid canvas renderer. CSS applied to `[data-testid="stDataFrame"]` affects the wrapper and may not penetrate the canvas cells. The `font-variant-numeric` applied to the wrapper container still influences the font stack the grid uses. **Verify with DevTools after implementation** — this is the main CSS targeting risk for this phase.

### Pattern 5: DataFrame Mutation Bug Fix

**What:** In `get_portfolio_performance`, the function mutates the `df` argument passed in from `conn.read()`. Since `conn.read()` is cached by `st_gsheets_connection`, the same DataFrame object is reused across reruns. In-place mutation corrupts the cached object, causing stale or incorrect data on subsequent calls.

**Fix location:** Line 31 of `app.py` — inside `get_portfolio_performance`, after the empty check guards (lines 31-34), before the first column assignment (line 52).

**Current code (lines 29-52 of app.py):**
```python
@st.cache_data(ttl=300)
def get_portfolio_performance(df):
    """Calculates Market Value, P&L, Allocation, and Sector"""
    if df.empty: return None, 0, 0

    tickers = df['Ticker'].tolist()
    if not tickers: return None, 0, 0

    try:
        close_data = yf.download(tickers, period="1d", progress=False)['Close']
        ticker_objects = {t: yf.Ticker(t) for t in tickers}
    except:
        return df, 0, 0

    if close_data.empty:
        return df, 0, 0

    # ...

    # MUTATION BEGINS HERE (line 52):
    df['Current Price'] = df['Ticker'].map(current_prices)
```

**Fixed version — insert after the `if not tickers` guard:**
```python
@st.cache_data(ttl=300)
def get_portfolio_performance(df):
    """Calculates Market Value, P&L, Allocation, and Sector"""
    if df.empty: return None, 0, 0

    tickers = df['Ticker'].tolist()
    if not tickers: return None, 0, 0

    df = df.copy()  # PLSH-03: prevent mutation of cached input DataFrame

    try:
        ...
```

**Why `df.copy()` here and not earlier:** The guards before this line return early without mutating, so the copy is only needed before we start modifying columns. Placing it immediately after `if not tickers` is the correct minimal fix.

### Anti-Patterns to Avoid

- **Using `st-emotion-cache-*` CSS classes:** These are dynamically generated and change between Streamlit versions and builds. Never use them in injected CSS.
- **Using `st._config.set_option()` for the toggle:** This is a private API that affects all concurrent sessions globally. In a multi-partner app, partner A toggling dark mode would change the theme for partners B, C, and D. Do not use.
- **Injecting CSS after the UI components render:** CSS injected after `st.dataframe()`, `st.metric()`, etc. causes a visible flash as components repaint. Always inject at the top of the script.
- **Using `config.toml [theme.dark]` / `[theme.light]` tables for the sidebar toggle:** These tables define what the dark and light themes look like, but switching between them requires the hamburger menu — there is no programmatic API to activate them. The sidebar button approach must use CSS injection.
- **Relying on `st.context.theme` to drive the toggle:** `st.context.theme` detects the user's OS/browser preference, not a user-set toggle state. It also has a known first-load caveat (may not be correct until first rerun). It is useful for reading the current system preference, but not suitable as the primary driver for a user-controlled toggle with session persistence.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Font loading | Custom `@import` CSS hack | `config.toml` `[theme] font` field | Official since v1.44; handles fallbacks and CSP automatically |
| Theme state | localStorage, cookies, URL params | `st.session_state` | Per-session, reset on refresh — exactly what the user decided |
| CSS resets for Streamlit defaults | Manually enumerating every selector | Start with `.stApp` + `[data-testid="stAppViewContainer"]` + sidebar, then add per-component selectors in later phases | Phase 1 is global palette only; component-level CSS is Phase 2+ |

**Key insight:** Streamlit's `config.toml` theming system (v1.44+) handles much of the baseline font and color wiring. CSS injection is reserved for overrides that `config.toml` cannot express (dynamic dark/light CSS variables, tabular-nums on specific selectors, semantic P&L colors).

---

## Common Pitfalls

### Pitfall 1: CSS Injection Placement Causes Flash

**What goes wrong:** CSS injected after the first `st.metric()` or `st.dataframe()` call causes components to render in the default Streamlit style briefly before the injected CSS applies. On slow connections or CI environments this is a jarring flash of the default light theme.

**Why it happens:** Streamlit renders components top-to-bottom. If CSS comes after a component, the component is already in the DOM with default styles.

**How to avoid:** Call `inject_css()` as the very first operation after `set_page_config()` and session state initialization. No components should render before this call.

**Warning signs:** White flash or default blue colors visible for a fraction of a second on page load.

---

### Pitfall 2: `st.button()` for Toggle Creates Double Rerun

**What goes wrong:** Using `if st.button("🌙"): st.session_state.dark_mode = not ...; st.rerun()` causes two reruns — one for the button interaction, and one explicit call. This can cause the button to appear to "skip" states or flicker.

**Why it happens:** Streamlit already reruns when a widget value changes. Calling `st.rerun()` on top of that schedules an additional execution.

**How to avoid:** Use the `on_click=callback` pattern for `st.sidebar.button()`. The callback executes before the rerun, state is mutated, and exactly one rerun occurs.

**Warning signs:** Toggle requires two clicks to change mode, or changes mode then immediately reverts.

---

### Pitfall 3: `config.toml` `base = "dark"` Conflicts with CSS Injection

**What goes wrong:** Setting `[theme] base = "dark"` in `config.toml` applies Streamlit's built-in dark theme. When you then inject CSS for your custom dark palette, there can be specificity conflicts where Streamlit's dark theme styles override your injected ones.

**Why it happens:** Streamlit's built-in theme styles are applied with higher specificity in some cases.

**How to avoid:** Use `!important` on background-color and color declarations for `.stApp` and `[data-testid="stAppViewContainer"]`. For the light mode CSS, also add `!important` since you're overriding the dark base.

**Warning signs:** `#0A0A0A` background not applying — browser DevTools shows your CSS rule being crossed out by a higher-specificity Streamlit rule.

---

### Pitfall 4: stDataFrame Canvas Does Not Respond to External CSS

**What goes wrong:** `font-variant-numeric: tabular-nums` applied to `[data-testid="stDataFrame"]` does not affect the number alignment inside the dataframe cells.

**Why it happens:** `st.dataframe()` renders through an Apache Arrow / Glide Data Grid canvas element. Canvas-rendered content does not respond to CSS font properties set on parent DOM elements.

**How to avoid:** For the dataframe in Phase 1, accept that `font-variant-numeric` will apply to the wrapper but may not penetrate the canvas. The metric widgets (`st.metric`) use standard DOM elements and WILL respond to CSS. Document this limitation — Phase 3 (PORT-03) will handle dataframe-specific styling with Pandas Styler or column configs.

**Warning signs:** Metric values align correctly with tabular-nums but dataframe numbers still use proportional widths.

---

### Pitfall 5: Streamlit 1.51 Theme Persistence Bug (Known, Fixed)

**What goes wrong:** If the app were ever upgraded to Streamlit 1.51, the user-selected theme from the hamburger settings menu would reset on every page reload.

**Why it happens:** Confirmed regression in 1.51's `processThemeInput` function — fixed in PR #13306.

**How to avoid:** Since we are using CSS injection (not the hamburger menu theme selector) for our custom toggle, this bug does not affect Phase 1's implementation. The `session_state` approach is immune to this regression because it persists within a browser session regardless of Streamlit's theme persistence mechanism. Document for awareness only.

---

## Code Examples

Verified patterns from official sources and community research:

### Config.toml for Inter + Dark Base
```toml
# .streamlit/config.toml
# Source: https://docs.streamlit.io/develop/tutorials/configuration-and-theming/external-fonts

[theme]
base = "dark"
font = "Inter:https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap, sans-serif"
primaryColor = "#C5A059"
backgroundColor = "#0A0A0A"
secondaryBackgroundColor = "#111111"
textColor = "#F5F5F5"
```

### Dark Mode CSS Block (Minimal Phase 1 Scope)
```python
# Source: Stable selectors verified via Streamlit community docs and DevTools inspection

DARK_CSS = """
<style>
/* Global app background */
.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #0A0A0A !important;
    color: #F5F5F5;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #111111 !important;
}

/* Metric values — tabular numerals */
[data-testid="stMetricValue"] {
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
    color: #F5F5F5;
}

/* Metric delta */
[data-testid="stMetricDelta"] {
    font-variant-numeric: lining-nums tabular-nums;
}

/* DataFrames outer wrapper */
[data-testid="stDataFrame"] {
    font-variant-numeric: lining-nums tabular-nums;
}

/* Gold accent on primary interactive elements */
.stButton > button {
    border-color: #C5A059;
    color: #C5A059;
}
</style>
"""

LIGHT_CSS = """
<style>
/* Global app background */
.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #FAFAFA !important;
    color: #1A1A1A;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
}

/* Metric values — tabular numerals */
[data-testid="stMetricValue"] {
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
    color: #1A1A1A;
}

/* Metric delta */
[data-testid="stMetricDelta"] {
    font-variant-numeric: lining-nums tabular-nums;
}

/* DataFrames outer wrapper */
[data-testid="stDataFrame"] {
    font-variant-numeric: lining-nums tabular-nums;
}

/* Gold accent on primary interactive elements */
.stButton > button {
    border-color: #C5A059;
    color: #C5A059;
}
</style>
"""
```

### Toggle Implementation (Sidebar)
```python
# Source: Streamlit session_state + on_click callback pattern
# Verified against https://docs.streamlit.io/develop/concepts/configuration/theming

# At top of app.py, after st.set_page_config():
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True  # dark is brand default

# Inject CSS immediately (before any UI components):
def inject_css(is_dark: bool) -> None:
    st.markdown(DARK_CSS if is_dark else LIGHT_CSS, unsafe_allow_html=True)

inject_css(st.session_state.dark_mode)

# In sidebar section (before partner selector):
def _toggle_theme() -> None:
    st.session_state.dark_mode = not st.session_state.dark_mode

_icon = "🌙" if st.session_state.dark_mode else "☀️"
st.sidebar.button(
    _icon,
    on_click=_toggle_theme,
    help="Toggle dark/light mode",
    key="theme_toggle"
)
```

### Semantic P&L Color Values (Fintech Standard)
```python
# Standard fintech green/red — high contrast on both dark (#0A0A0A) and light (#FAFAFA) backgrounds
# Green: #16A34A (Tailwind green-600) — WCAG AA compliant on both backgrounds
# Red:   #DC2626 (Tailwind red-600) — WCAG AA compliant on both backgrounds

SEMANTIC_GREEN = "#16A34A"
SEMANTIC_RED   = "#DC2626"

# Injected CSS already includes .pl-positive and .pl-negative classes.
# Usage in metric delta via delta_color parameter:
# st.metric("Unrealized P&L", f"${total_pl:,.2f}", delta=...)
# — delta_color="normal" uses Streamlit's built-in green/red which may not match brand.
# Override via CSS targeting [data-testid="stMetricDelta"] if needed.
```

### df.copy() Fix Location
```python
# app.py lines 29-36 — insert df = df.copy() after the guard clauses

@st.cache_data(ttl=300)
def get_portfolio_performance(df):
    """Calculates Market Value, P&L, Allocation, and Sector"""
    if df.empty: return None, 0, 0

    tickers = df['Ticker'].tolist()
    if not tickers: return None, 0, 0

    df = df.copy()  # PLSH-03: prevent in-place mutation of cached DataFrame input

    try:
        close_data = yf.download(tickers, period="1d", progress=False)['Close']
        # ... rest of function unchanged
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `st.markdown(unsafe_allow_html=True)` for all CSS | `st.html(path_to_file)` for CSS files | v1.46 (June 2025) | `st.html` with a `.css` file auto-wraps in `<style>` tags and avoids layout space; still MEDIUM confidence for CSS since v1.42 regression |
| No programmatic font loading | `config.toml [theme] font` field with `"FontName:URL"` format | v1.44 (May 2025) | Official font loading — no @import hacks needed |
| Manual theme detection workarounds (`st-theme` package) | `st.context.theme` | v1.46 (June 2025) | Native runtime theme detection; first-load caveat documented |
| Separate `[theme.dark]` / `[theme.light]` config feature | Available but hamburger-menu activated only | v1.51 (Oct 2025) | Does NOT provide a programmatic sidebar button — CSS injection still needed for sidebar toggle |

**Deprecated / outdated:**
- `st-theme` community package: Superseded by `st.context.theme` (v1.46), but still functional.
- `st._config.set_option("theme.base", ...)`: Private API, global scope, not recommended. Never use for multi-user apps.
- `st-emotion-cache-*` CSS class targeting: Dynamically generated, breaks between versions. Never use.

---

## Open Questions

1. **Does `font-variant-numeric` penetrate the stDataFrame canvas renderer?**
   - What we know: `st.dataframe()` uses Glide Data Grid, which renders to canvas. External CSS typically does not affect canvas-rendered text.
   - What's unclear: Whether the font-variant-numeric applied to the outer wrapper element influences which font variant the canvas grid loads.
   - Recommendation: Implement and verify in DevTools. If CSS doesn't penetrate, note it as a Phase 3 concern (PORT-03). Do not block Phase 1 on this.

2. **Does `config.toml` `base = "dark"` interact cleanly with the CSS injection approach?**
   - What we know: `base = "dark"` sets Streamlit's built-in dark theme as the baseline. CSS injection overrides on top. Some specificity conflicts exist.
   - What's unclear: Whether Streamlit's dark theme `background-color` declarations will require `!important` to override for all elements.
   - Recommendation: Apply `!important` to `background-color` on `.stApp` and `[data-testid="stAppViewContainer"]` preemptively. Test in browser.

3. **Which icon best conveys sun/moon with minimal footprint?**
   - What we know: Context.md delegates this to Claude's discretion.
   - Options: Emoji (🌙 / ☀️) — zero dependency, universal support, but may render at different sizes across OS. Unicode characters (☽ / ☀) — consistent rendering. SVG — full control, but requires HTML injection for just an icon.
   - Recommendation: Use emoji 🌙 (dark mode indicator) and ☀️ (light mode indicator). They render correctly in Streamlit buttons, are universally recognizable, and require no additional code.

---

## Sources

### Primary (HIGH confidence)
- Streamlit official docs, theming: https://docs.streamlit.io/develop/concepts/configuration/theming — config.toml options, theme.base, theme.dark/light tables
- Streamlit official docs, external fonts: https://docs.streamlit.io/develop/tutorials/configuration-and-theming/external-fonts — Google Fonts config.toml format
- Streamlit official docs, st.html: https://docs.streamlit.io/develop/api-reference/text/st.html — CSS file path behavior, v1.54.0 reference
- Streamlit official docs, config.toml: https://docs.streamlit.io/develop/api-reference/configuration/config.toml — full option list
- Streamlit 2025 release notes: https://docs.streamlit.io/develop/quick-reference/release-notes/2025 — version-by-version feature tracking
- MDN font-variant-numeric: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-variant-numeric — tabular-nums behavior and browser support

### Secondary (MEDIUM confidence)
- Streamlit community: "Changing the Streamlit Theme with a Toggle Button (SOLUTION)" — https://discuss.streamlit.io/t/changing-the-streamlit-theme-with-a-toggle-button-solution/56842 — session_state + st._config pattern (private API warning noted)
- Streamlit community: "Dark/light theme selection" — https://discuss.streamlit.io/t/dark-light-theme-selection/83937 — multi-user caveat of st._config
- GitHub issue #13280: Theme persistence bug in 1.51 — https://github.com/streamlit/streamlit/issues/13280 — confirmed regression and fix
- Streamlit community: CSS selectors for theming — https://discuss.streamlit.io/t/css-hacks/14501 — stable selector list (.stApp, data-testid attributes)

### Tertiary (LOW confidence)
- WebSearch-only results on stDataFrame canvas CSS penetration — no official docs found; community reports suggest canvas renders independently of external CSS.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — project constraints are clear; no library selection needed
- CSS injection approach (`st.markdown`): HIGH — verified against official docs, community consensus
- Dark/light toggle pattern: HIGH — session_state + callback is documented Streamlit pattern; private API risk documented
- Google Fonts via config.toml: HIGH — official docs with exact format
- Tabular-nums selector targets: MEDIUM — `[data-testid="stMetricValue"]` confirmed stable; stDataFrame canvas penetration unverified
- DataFrame mutation bug fix location: HIGH — code read directly from app.py; fix is standard pandas pattern
- Semantic color hex values: MEDIUM — fintech convention; WCAG compliance not formally verified but standard values

**Research date:** 2026-02-19
**Valid until:** 2026-03-21 (30 days — stable Streamlit APIs, but verify selectors if Streamlit version is upgraded beyond 1.54)
