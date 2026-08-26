# Architecture Patterns: Dark/Light Mode Theming

**Domain:** Single-file Streamlit app theming system
**Researched:** 2026-02-18
**Versions verified:** Streamlit (installed, copyright 2022-2025), Plotly 5.24.1

---

## Recommended Architecture

A three-part system: session state holds the theme value, a CSS string constant maps theme to styles, and Plotly charts accept theme as an explicit argument.

```
User clicks toggle in sidebar
        |
        v
st.session_state["dark_mode"] = True/False
        |
        v
inject_theme_css(is_dark)        <-- st.html("<style>...</style>") at top of script
        |
        v
chart functions receive is_dark as argument  <-- cache keyed on this value
        |
        v
fig.update_layout(template=..., paper_bgcolor=..., plot_bgcolor=...)
```

---

## Component Boundaries

| Component | Responsibility | Location in app.py |
|-----------|---------------|-------------------|
| Theme state | Persist toggle value across reruns | `st.session_state["dark_mode"]` |
| Toggle widget | User input, lives in sidebar | Lines 21-24 block (sidebar section) |
| CSS injection | Apply brand palette to Streamlit chrome | Called immediately before `st.title()`, after `st.set_page_config()` |
| CSS constants | Immutable string templates per theme | Module-level constants before all functions |
| Plotly theming | Apply theme to each figure | Inside each chart-building call site |

---

## Where to Place Things in app.py

### Order of operations (critical)

```python
# 1. Page config — must be first st call
st.set_page_config(page_title="Project Photizo", layout="wide")

# 2. CSS constants — module-level, before any function definitions
DARK_CSS = """<style> ... </style>"""
LIGHT_CSS = """<style> ... </style>"""

# 3. Theme state initialization — before any rendering
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True  # default: dark

# 4. CSS injection — immediately after state init, before st.title()
_inject_theme_css(st.session_state["dark_mode"])

# 5. st.connection — unchanged, stays where it is
conn = st.connection("gsheets", type=GSheetsConnection)

# 6. Sidebar — toggle widget goes here, after conn
with st.sidebar:
    st.session_state["dark_mode"] = st.toggle(
        "Dark Mode",
        value=st.session_state["dark_mode"],
        key="dark_mode",
    )
    # existing sidebar widgets follow

# 7. @st.cache_data function definitions — unchanged
# 8. Tabs and chart code — charts receive is_dark as argument
```

**Why CSS injection happens before `st.connection`:** Streamlit executes top-to-bottom on every rerun. CSS injected at the top of the script is present before any content renders. If CSS injection were placed after tabs/charts, there is a one-frame flash of unstyled content. The `st.connection` call position is irrelevant to CSS — it just fetches data. The connection must stay before the cached function calls that use `conn`, but CSS injection has no dependency on the connection.

**Why toggle is in the sidebar and not at the top level:** `st.toggle` tied directly to `st.session_state["dark_mode"]` with `key="dark_mode"` means the widget and the state key are the same object. Streamlit automatically syncs them. The widget does not need to appear before the CSS injection call — Streamlit processes widget state from the *previous* rerun before the current script body executes.

---

## CSS Structure: One Constant Per Theme

Use two separate string constants — not a single parameterized f-string. The reason: parameterized strings are computed at call time and cannot be validated statically; separate constants are also easier to diff in version control.

```python
# --- THEME CSS CONSTANTS ---
# Placed at module level, before all function definitions

_BRAND_GOLD_PRIMARY = "#C5A059"
_BRAND_GOLD_MUTED   = "#9E804B"
_BRAND_BLACK        = "#000000"

DARK_CSS = """
<style>
    /* Root / app background */
    .stApp {
        background-color: #0A0A0A;
        color: #F0F0F0;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #C5A059;
    }
    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #111111;
        border: 1px solid #1E1E1E;
        border-radius: 8px;
        padding: 12px;
    }
    /* Metric value */
    [data-testid="stMetricValue"] > div {
        color: #C5A059;
    }
    /* Tab active indicator */
    .stTabs [aria-selected="true"] {
        border-bottom-color: #C5A059;
        color: #C5A059;
    }
    /* Dividers */
    hr {
        border-color: #1E1E1E;
    }
    /* Dataframe header */
    .stDataFrame th {
        background-color: #111111;
        color: #C5A059;
    }
</style>
"""

LIGHT_CSS = """
<style>
    .stApp {
        background-color: #FAFAFA;
        color: #1A1A1A;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #C5A059;
    }
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 12px;
    }
    [data-testid="stMetricValue"] > div {
        color: #9E804B;
    }
    .stTabs [aria-selected="true"] {
        border-bottom-color: #C5A059;
        color: #9E804B;
    }
    hr {
        border-color: #E0E0E0;
    }
    .stDataFrame th {
        background-color: #FFFFFF;
        color: #9E804B;
    }
</style>
"""
```

---

## CSS Injection: Use `st.html`, Not `st.markdown`

The Streamlit source (`streamlit/elements/html.py`, line 134) contains explicit logic: when the body of `st.html` contains **only** `<style>` tags, the content is sent to the **event container** rather than the main content container. This means it takes up zero vertical space in the app.

```python
def _inject_theme_css(is_dark: bool) -> None:
    """Inject brand CSS for the current theme. Zero layout impact."""
    st.html(DARK_CSS if is_dark else LIGHT_CSS)
```

`st.markdown(body, unsafe_allow_html=True)` also works but creates a zero-height markdown element that still occupies a slot in Streamlit's delta queue. `st.html` with style-only content is the correct API as of the installed Streamlit version.

**Note:** `st.html` sanitizes with DOMPurify. Style tags are not stripped by DOMPurify — CSS injected via `<style>` blocks passes through safely. JavaScript is not supported and should not be used.

---

## Plotly Theme Switching: The `is_dark` Argument Pattern

### The caching problem

`@st.cache_data` keys its cache on the **hash of all function arguments** (verified in `cache_utils.py`, `_make_value_key`). The hash is computed from every argument whose name does not start with `_`.

The existing cached functions in app.py take DataFrames or ticker strings as arguments. Theme does not belong in those functions because:
1. It would create two cached entries per DataFrame (one per theme) — doubling memory.
2. The financial data (prices, portfolio values) is the expensive part to compute. The Plotly figure layout is cheap.

**Solution:** Separate data computation (cached) from figure construction (uncached).

```python
# CACHED: returns DataFrame only — no Plotly figures
@st.cache_data(ttl=300)
def get_portfolio_performance(df):
    # ... existing logic returning (df_rich, total_equity, total_pl)
    ...

# UNCACHED: builds figures from already-cached data
def build_pie_chart(df: pd.DataFrame, values_col: str, names_col: str, is_dark: bool):
    """Construct a Plotly pie chart with brand theming. Not cached — fast."""
    fig = px.pie(df, values=values_col, names=names_col, hole=0.4)
    _apply_plotly_theme(fig, is_dark)
    return fig

def _apply_plotly_theme(fig, is_dark: bool) -> None:
    """Apply brand palette to any Plotly figure in-place."""
    if is_dark:
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A0A0A",
            plot_bgcolor="#111111",
            font=dict(color="#F0F0F0", family="sans-serif"),
            colorway=["#C5A059", "#9E804B", "#E8C87A", "#7A5F30",
                       "#F5DFA0", "#5C4020", "#D4B070", "#B8960A"],
        )
    else:
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="#FAFAFA",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#1A1A1A", family="sans-serif"),
            colorway=["#C5A059", "#9E804B", "#E8C87A", "#7A5F30",
                       "#F5DFA0", "#5C4020", "#D4B070", "#B8960A"],
        )
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
```

### Why `template="plotly_dark"` is a good base

The `plotly_dark` template (verified in `plotly/package_data/templates/plotly_dark.json`) sets `paper_bgcolor` and `plot_bgcolor` to `rgb(17,17,17)`, axis colors to `#506784`, and font color to `#f2f5fa`. This is close to the project's dark palette. Calling `update_layout` *after* setting `template` overrides the template's background values with brand-specific ones (`#0A0A0A`, `#111111`) while keeping the template's axis and grid styling.

For light mode, `plotly_white` sets white backgrounds and dark axes — a clean base.

---

## Data Flow: Toggle Click to Rendered Chart

```
Frame N (user interaction):
  1. User flips st.toggle("Dark Mode")
  2. Streamlit records widget state change
  3. Script rerun is triggered

Frame N+1 (rerun):
  1. st.set_page_config()  — no change
  2. Session state already contains updated dark_mode = True/False
     (widget state is committed before script body executes)
  3. _inject_theme_css(st.session_state["dark_mode"])
     → st.html(DARK_CSS or LIGHT_CSS) sent to event container
     → CSS applied globally via <style> tag in document <head>
  4. conn = st.connection(...)  — returns same connection (st.cache_resource)
  5. Sidebar toggle renders with updated value from session_state
  6. Tab content executes:
     a. get_portfolio_performance(raw_df)  — cache hit if df unchanged (same hash)
        Returns (df_rich, total_equity, total_pl)
     b. build_pie_chart(df_rich, ..., is_dark)  — executes every rerun (not cached)
        Calls _apply_plotly_theme(fig, is_dark)
        Returns themed fig
     c. st.plotly_chart(fig)  — renders with new colors
```

**Cache behavior on toggle:** `get_portfolio_performance(df)` receives the same `df` as before (fetched from Google Sheets with the same TTL). Its hash is unchanged. The function returns the cached result — no network call, no recomputation. Only the figure construction (cheap, milliseconds) re-executes. The toggle causes no cache invalidation.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Passing `is_dark` into `@st.cache_data` functions

```python
# BAD — forces two cache entries, wastes memory, confuses intent
@st.cache_data(ttl=300)
def get_portfolio_performance(df, is_dark: bool):  # <-- wrong
    ...
    fig = px.pie(...)
    fig.update_layout(template="plotly_dark" if is_dark else "plotly_white")
    return fig
```

**Why bad:** The financial calculation is now doubled in the cache (one entry for `is_dark=True`, one for `is_dark=False`). The yfinance API calls happen twice. Theme is a presentation concern — it does not belong in data functions.

**Instead:** Keep data and presentation separate as shown above.

### Anti-Pattern 2: CSS injection inside a tab or column

```python
# BAD — CSS is injected conditionally; tab-scoped elements may not receive it
with tab_portfolio:
    st.html(DARK_CSS)  # <-- wrong placement
```

**Why bad:** Streamlit's CSS injection via `st.html` injects into the document head, which is global. However, the *timing* of when the style tag appears in the delta stream may cause a flash if charts render before CSS is applied. Always inject at the top of the script body, before any content.

### Anti-Pattern 3: Using `pio.templates.default` to set global Plotly theme

```python
# BAD — global state, affects all charts across all sessions
import plotly.io as pio
pio.templates.default = "plotly_dark" if is_dark else "plotly_white"
```

**Why bad:** `pio.templates.default` is a module-level global. In a multi-user Streamlit deployment, this creates a race condition: User A's toggle changes the global template and User B's charts switch unexpectedly. Always pass the template explicitly via `update_layout` per figure.

### Anti-Pattern 4: Storing CSS in session_state

```python
# BAD — unnecessary overhead
st.session_state["css"] = DARK_CSS if is_dark else LIGHT_CSS
st.html(st.session_state["css"])
```

**Why bad:** CSS strings are constants — they never change. Session state is for user-specific mutable values. Store only the boolean `dark_mode` flag in session_state; derive the CSS string from it inline.

---

## Streamlit CSS Selector Stability Warning

Streamlit's HTML/CSS class names and `data-testid` attributes are **not part of the public API**. They can change between Streamlit versions without notice. The selectors used above (`[data-testid="stSidebar"]`, `[data-testid="stMetric"]`, etc.) were confirmed against the installed Streamlit version but should be verified after any `streamlit` upgrade.

Mitigation: Use `data-testid` selectors rather than generated class names like `.st-emotion-cache-*`. The `data-testid` attributes are more stable across Streamlit versions.

---

## Scalability Considerations

| Concern | Single-file app (current) | If ever multi-page |
|---------|--------------------------|-------------------|
| Theme persistence across pages | session_state persists automatically | Same pattern works — session_state is session-scoped, not page-scoped |
| CSS injection per page | Single injection at top of app.py | Each page file must call `_inject_theme_css()` at its top |
| Multiple chart types | `_apply_plotly_theme` is generic — works for pie, bar, line | No change needed |

---

## Sources

- Streamlit `elements/html.py` (installed): `_html_only_style_tags` function confirms style-only `st.html` uses event container (no layout space)
- Streamlit `elements/widgets/checkbox.py` (installed): `st.toggle` signature and `key` parameter behavior confirmed
- Streamlit `runtime/caching/cache_utils.py` (installed): `_make_value_key` confirms all non-underscore-prefixed args are hashed for cache key
- Plotly `io/_templates.py` (installed): `TemplatesConfig` — available built-in templates confirmed: `plotly_dark`, `plotly_white`, `simple_white`
- Plotly `package_data/templates/plotly_dark.json` (installed): Dark template base colors confirmed (`rgb(17,17,17)` backgrounds, `#f2f5fa` font)
- Streamlit `elements/markdown.py` (installed): `st.markdown` documentation recommends `st.html` for CSS-only injection
