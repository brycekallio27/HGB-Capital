# Technology Stack: Streamlit CSS Theming & Styling

**Project:** Project Photizo — HGB Capital Premium UI Redesign
**Researched:** 2026-02-18
**Streamlit Version Verified:** 1.50.0 (inspected venv source directly)
**Overall Confidence:** HIGH (verified from Streamlit 1.50.0 source code in venv)

---

## Recommended Styling Stack

The complete styling approach uses no new dependencies. Everything is achieved through
Streamlit 1.50's native capabilities.

### CSS Injection (Primary Mechanism)

| Method | API | When to Use | Confidence |
|--------|-----|-------------|------------|
| `st.html()` with `<style>` tags | `st.html("<style>...</style>")` | **Preferred** — does not add a visible block to layout; routes to event container | HIGH |
| `st.markdown()` with `<style>` tags | `st.markdown("<style>...</style>", unsafe_allow_html=True)` | Fallback; works identically for CSS-only blocks since 1.40+ | HIGH |
| `st.html()` with CSS file path | `st.html(Path("styles.css"))` | When using separate CSS file and `server.enableStaticServing=true` | HIGH |

**Confirmed from source (`streamlit/elements/html.py` lines 117-137):** When `st.html()` receives
content that consists only of `<style>` tags (no other HTML), Streamlit routes it to the
`event_dg` (event container) instead of the main content container. This means pure CSS injection
via `st.html()` does not take up vertical space in the app layout — a significant improvement
over older `st.markdown()` patterns.

**Implementation pattern for this project:**

```python
def inject_styles(mode: str = "dark") -> None:
    """Call once at top of app.py, before any UI elements."""
    css = DARK_THEME_CSS if mode == "dark" else LIGHT_THEME_CSS
    st.html(f"<style>{css}</style>")
```

### config.toml Theming (Foundation Layer)

Set the baseline in `.streamlit/config.toml`. This handles the structural color surface
before any CSS injection runs. CSS injection then overrides the fine-grained details.

```toml
[theme]
base = "dark"
primaryColor = "#C5A059"
backgroundColor = "#0A0A0A"
secondaryBackgroundColor = "#111111"
textColor = "#E0E0E0"
font = "sans-serif"
borderColor = "#1A1A1A"
baseFontSize = 16
baseRadius = "4px"
showWidgetBorder = false
showSidebarBorder = false

[theme.sidebar]
backgroundColor = "#0A0A0A"
secondaryBackgroundColor = "#111111"
primaryColor = "#C5A059"
textColor = "#E0E0E0"
```

**Confirmed available options in 1.50.0** (from `streamlit/config.py` direct inspection):
- `theme.base` — "light" or "dark" baseline
- `theme.primaryColor` — accent color (buttons, active elements)
- `theme.backgroundColor` — main app background
- `theme.secondaryBackgroundColor` — widgets, expanders, sidebars
- `theme.textColor` — primary text
- `theme.font` — body font; accepts Google Fonts URL format: `"Inter:https://fonts.googleapis.com/css2?family=Inter&display=swap"`
- `theme.headingFont` — separate font for h1–h6
- `theme.baseFontSize` — root font size in px (integer)
- `theme.baseRadius` — border radius for UI elements (string with units, e.g. "4px")
- `theme.buttonRadius` — separate radius for buttons
- `theme.borderColor` — widget/container border color
- `theme.showWidgetBorder` — bool; hide widget borders for cleaner look
- `theme.showSidebarBorder` — bool
- `theme.linkColor` — anchor color
- `theme.codeBackgroundColor`
- `theme.chartCategoricalColors` — array of hex colors for Plotly/Altair/Vega charts
- `[theme.sidebar]` — all of the above, scoped to sidebar only
- `[[theme.fontFaces]]` — custom font face definitions (requires static serving)

**NOT configurable via config.toml** (require CSS injection):
- Individual widget hover states
- Metric card backgrounds and borders
- Tab active/inactive state colors beyond primaryColor
- Dataframe cell colors
- Padding/spacing within containers
- Animation/transitions

---

## Dark/Light Mode Toggle

### Architecture

The toggle lives in session_state. Streamlit does not provide a native dark/light toggle API.
The config.toml sets the default baseline; CSS injection overrides styles based on the current
mode stored in session_state.

**How it works:** On every rerun, `inject_styles()` is called at the top of the script before
any other `st.` calls. It reads `st.session_state.theme_mode` and injects the appropriate CSS
block. Since Streamlit reruns the entire script on every interaction, the CSS block is always
freshly injected for the current mode.

### Implementation Pattern

```python
import streamlit as st

# 1. Initialize session state (top of app.py, before set_page_config)
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"  # default to dark for HGB brand

# 2. st.set_page_config must be first Streamlit call
st.set_page_config(page_title="HGB Capital", layout="wide")

# 3. Inject styles based on current mode
inject_styles(st.session_state.theme_mode)

# 4. Toggle button in sidebar
with st.sidebar:
    mode_label = "Switch to Light" if st.session_state.theme_mode == "dark" else "Switch to Dark"
    if st.button(mode_label, key="theme_toggle"):
        st.session_state.theme_mode = (
            "light" if st.session_state.theme_mode == "dark" else "dark"
        )
        st.rerun()
```

**Why st.rerun() is required:** Streamlit re-executes the full script from top on each
interaction. The `st.button` click sets session_state, but `inject_styles()` has already run
with the old mode. `st.rerun()` forces a second pass where `inject_styles()` runs again with
the updated mode. Without `st.rerun()`, the style change would apply on the *next* natural
interaction, not immediately.

**Limitation — config.toml base is static:** The `theme.base` in config.toml is read at server
startup, not per-rerun. CSS injection fully overrides the visual result, but Streamlit's internal
color system (used to calculate derived colors for some widget states) is still anchored to the
config.toml base. Set `base = "dark"` in config.toml since dark is the primary mode. The light
mode CSS injection will override all visible surfaces correctly.

---

## CSS Selectors Verified in Streamlit 1.50

These selectors are derived from the Streamlit React component architecture (data-testid
attributes are part of Streamlit's stable internal structure used for testing). Confidence
is MEDIUM-HIGH — these are standard Streamlit DOM patterns that have been stable across
recent versions, but can shift between major versions.

### Layout Structure Selectors

```css
/* App root container */
[data-testid="stApp"] {
    background-color: #0A0A0A;
}

/* Main content area */
[data-testid="stAppViewContainer"] {
    background-color: #0A0A0A;
}

/* Main content block (inner padding wrapper) */
[data-testid="block-container"] {
    padding: 2rem 3rem;
    max-width: 1400px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0A0A0A;
    border-right: 1px solid #1A1A1A;
}

/* Sidebar content wrapper */
[data-testid="stSidebarContent"] {
    background-color: #0A0A0A;
}

/* Header/toolbar at top */
[data-testid="stHeader"] {
    background-color: transparent;
}
```

### Widget Selectors

```css
/* Metric card container */
[data-testid="metric-container"] {
    background-color: #111111;
    border: 1px solid #1A1A1A;
    border-radius: 8px;
    padding: 1.25rem;
}

/* Metric label */
[data-testid="stMetricLabel"] {
    color: #9E804B;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* Metric value */
[data-testid="stMetricValue"] {
    color: #E0E0E0;
    font-size: 1.75rem;
    font-weight: 600;
}

/* Metric delta */
[data-testid="stMetricDelta"] svg {
    /* Delta arrow icon */
}

/* Buttons */
[data-testid="stButton"] > button {
    background-color: transparent;
    border: 1px solid #C5A059;
    color: #C5A059;
    border-radius: 4px;
    font-weight: 600;
    transition: all 0.2s ease;
}

[data-testid="stButton"] > button:hover {
    background-color: #C5A059;
    color: #000000;
}

/* Tab bar */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #1A1A1A;
    gap: 0;
}

/* Individual tab */
[data-testid="stTabs"] [role="tab"] {
    color: #9E804B;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    padding: 0.5rem 1.25rem;
}

/* Active tab */
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #C5A059;
    border-bottom: 2px solid #C5A059;
}

/* Selectbox */
[data-testid="stSelectbox"] > div {
    background-color: #111111;
    border: 1px solid #1A1A1A;
    color: #E0E0E0;
}

/* Text input */
[data-testid="stTextInput"] > div > div > input {
    background-color: #111111;
    border: 1px solid #1A1A1A;
    color: #E0E0E0;
    border-radius: 4px;
}

/* Slider */
[data-testid="stSlider"] [role="slider"] {
    background-color: #C5A059;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #1A1A1A;
    border-radius: 4px;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid #1A1A1A;
    border-radius: 4px;
    background-color: #111111;
}

/* Divider */
[data-testid="stDivider"] hr {
    border-color: #1A1A1A;
}
```

### Global Typography

```css
/* All text */
h1, h2, h3, h4, h5, h6 {
    color: #E0E0E0;
    font-weight: 600;
}

/* Subheader */
h2[data-testid="stHeadingWithActionElements"] {
    letter-spacing: -0.02em;
}

/* Caption / small text */
[data-testid="stCaptionContainer"] {
    color: #555555;
    font-size: 0.75rem;
}
```

**Note on selector stability:** Streamlit's `data-testid` attributes are part of its testing
infrastructure and have been stable across 1.x releases, but are not publicly documented as
a stable public API. They may change in future major versions. Monitor the Streamlit changelog
when upgrading beyond 1.x.

---

## Plotly Chart Theming

### Two-Layer Approach

Plotly theming for HGB brand requires two layers:

**Layer 1 — fig.update_layout():** Sets background, fonts, axis styling, legend.
This is the primary mechanism and is fully reliable.

**Layer 2 — fig.update_traces():** Sets trace colors (bar fill, pie slices, line colors).

**Note on Streamlit's Plotly template:** Streamlit 1.50 registers a custom Plotly template
named "streamlit" at startup (confirmed from `streamlit/elements/lib/streamlit_plotly_theme.py`).
This template uses placeholder colors that the frontend JavaScript replaces with theme-appropriate
values. When you call `fig.update_layout()` with explicit colors, your values take precedence
over the template. Do not call `pio.templates.default = "plotly_dark"` — that overrides
Streamlit's template registration. Instead, apply layout overrides directly per figure.

### Standard Layout Template

Apply this to every Plotly figure in the app:

```python
PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor="#111111",   # chart card background
    plot_bgcolor="#0A0A0A",    # plot area background
    font=dict(
        family="Inter, Source Sans, sans-serif",
        color="#E0E0E0",
        size=12,
    ),
    title=dict(
        font=dict(color="#C5A059", size=14, weight=600),
        x=0.0,
        xanchor="left",
        pad=dict(l=0),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="#1A1A1A",
        borderwidth=1,
        font=dict(color="#9E804B", size=11),
    ),
    xaxis=dict(
        gridcolor="#1A1A1A",
        linecolor="#1A1A1A",
        tickfont=dict(color="#9E804B", size=10),
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="#1A1A1A",
        linecolor="#1A1A1A",
        tickfont=dict(color="#9E804B", size=10),
        showgrid=True,
        zeroline=False,
    ),
    margin=dict(t=40, b=40, l=40, r=20),
    hoverlabel=dict(
        bgcolor="#1A1A1A",
        bordercolor="#C5A059",
        font=dict(color="#E0E0E0"),
    ),
)

PLOTLY_LIGHT_LAYOUT = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#F5F5F5",
    font=dict(family="Inter, Source Sans, sans-serif", color="#1A1A1A", size=12),
    title=dict(font=dict(color="#9E804B", size=14, weight=600)),
    legend=dict(bgcolor="rgba(255,255,255,0)", bordercolor="#E0E0E0", borderwidth=1),
    xaxis=dict(gridcolor="#E0E0E0", linecolor="#E0E0E0", tickfont=dict(color="#555555")),
    yaxis=dict(gridcolor="#E0E0E0", linecolor="#E0E0E0", tickfont=dict(color="#555555")),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#C5A059"),
)

# HGB brand color palette for chart traces
HGB_COLORS = ["#C5A059", "#9E804B", "#7A6035", "#4A3A20", "#E8C87A", "#D4B06A"]
```

### Per-Figure Application Pattern

```python
def apply_hgb_theme(fig, mode="dark"):
    """Apply HGB theme to any Plotly figure."""
    layout = PLOTLY_DARK_LAYOUT if mode == "dark" else PLOTLY_LIGHT_LAYOUT
    fig.update_layout(**layout)
    return fig

# Pie chart traces
fig1.update_traces(
    marker=dict(colors=HGB_COLORS),
    textfont=dict(color="#E0E0E0"),
    hovertemplate="<b>%{label}</b><br>%{value:$,.2f}<br>%{percent}<extra></extra>",
)

# Bar chart traces
fig.update_traces(
    marker=dict(color="#C5A059", line=dict(color="#9E804B", width=1)),
    hovertemplate="<b>%{y}</b><br>%{x:.1%}<extra></extra>",
)
```

### Candlestick/Waterfall (fintech-specific)

Streamlit's Plotly theme sets `INCREASING` and `DECREASING` placeholder colors.
Override them explicitly for brand compliance:

```python
fig.update_traces(
    increasing=dict(line=dict(color="#C5A059"), fillcolor="#C5A059"),
    decreasing=dict(line=dict(color="#7A6035"), fillcolor="#7A6035"),
)
```

---

## What NOT to Use

| Approach | Why Not |
|----------|---------|
| `streamlit-extras` package | Adds dependency weight; most features achievable natively in 1.50 |
| `streamlit-option-menu` | Replaces native tabs with custom sidebar nav; not needed here |
| `st_aggrid` | Heavy dependency for custom dataframes; native `st.dataframe` + CSS suffices |
| Custom React components | Violates project scope (no frontend rewrite) |
| `plotly_dark` template via `pio.templates.default` | Overrides Streamlit's own template registration; use `fig.update_layout()` instead |
| CSS `!important` everywhere | Use it only where Streamlit's own inline styles create specificity conflicts; overuse makes future changes brittle |
| Inline style on individual `st.markdown()` calls | Hard to maintain; consolidate all CSS in one `inject_styles()` call |
| `st.markdown()` for CSS when `st.html()` is available | `st.html()` is cleaner for pure CSS (no layout space consumed); use `st.markdown()` only for mixed HTML+Markdown content |
| JS injection via `st.components.v1.html()` | CSS-in-JS is not needed; pure CSS injection covers all theming requirements |

---

## Complete config.toml Template

Create `.streamlit/config.toml` in the project root:

```toml
[theme]
base = "dark"
primaryColor = "#C5A059"
backgroundColor = "#0A0A0A"
secondaryBackgroundColor = "#111111"
textColor = "#E0E0E0"
font = "Inter:https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
headingFont = "Inter:https://fonts.googleapis.com/css2?family=Inter:wght@600;700&display=swap"
baseFontSize = 16
baseRadius = "4px"
buttonRadius = "4px"
borderColor = "#1A1A1A"
linkColor = "#C5A059"
linkUnderline = false
showWidgetBorder = false
showSidebarBorder = false

[theme.sidebar]
backgroundColor = "#0A0A0A"
secondaryBackgroundColor = "#111111"
primaryColor = "#C5A059"
textColor = "#E0E0E0"
borderColor = "#1A1A1A"

[server]
enableStaticServing = false   # set to true if serving local font/image assets

[client]
toolbarMode = "viewer"        # hides developer toolbar for non-dev sessions
```

**Font loading note:** The `font` config option accepts the URL format
`"FontName:https://fonts.googleapis.com/..."`. This is confirmed in `config.py` line 1535.
Inter is the recommended choice for premium fintech — readable, professional, widely used
by Robinhood and Linear.

---

## Known Hard Limits

| Limit | Description | Workaround |
|-------|-------------|------------|
| No native dark/light toggle API | Streamlit does not expose a toggle; `config.toml` is static per server start | session_state + CSS injection (documented above) |
| config.toml is server-global | All users share the same config.toml theme | CSS injection per-session via session_state handles per-user variation |
| `data-testid` selectors not officially stable | Streamlit tests use them but doesn't guarantee backward compatibility | Pin Streamlit version; test selectors after upgrades |
| Plotly template colors replaced by frontend | Streamlit's JS replaces placeholder colors; explicit `update_layout()` overrides trump the template | Always use `fig.update_layout()` rather than relying on template inheritance |
| `st.html()` sanitizes with DOMPurify | JavaScript is stripped from `st.html()` content | CSS works fine; JS injection not needed for theming |
| Streamlit rerenders entire script on interaction | CSS must be re-injected on every run (not persistent in browser) | Place `inject_styles()` at top of script before any `st.` UI calls |
| iframe isolation for some components | Custom Plotly charts, `st.components.v1.html()` iframes have their own scope; parent CSS does not cascade into them | Theme Plotly via `fig.update_layout()`, not CSS selectors |

---

## Confidence Assessment

| Area | Confidence | Source |
|------|------------|--------|
| `st.html()` CSS injection behavior | HIGH | Verified from `streamlit/elements/html.py` source (lines 117-140) |
| config.toml theme options | HIGH | Verified from `streamlit/config.py` source (lines 1145-1900) |
| `theme.font` URL format | HIGH | Verified from `streamlit/config.py` line 1535 comment |
| `theme.sidebar` scoping | HIGH | Verified — `CustomThemeCategories.SIDEBAR` in source |
| `data-testid` CSS selectors | MEDIUM | Standard Streamlit pattern; not officially guaranteed stable |
| dark/light mode via session_state | HIGH | Core Streamlit pattern; session_state is stable API |
| Plotly `fig.update_layout()` approach | HIGH | Verified Streamlit Plotly template mechanism in source |
| `pio.templates.default` conflict | HIGH | Verified from `streamlit/elements/lib/streamlit_plotly_theme.py` |

---

## Sources

- Streamlit 1.50.0 installed source: `/venv/lib/python3.9/site-packages/streamlit/elements/html.py`
- Streamlit 1.50.0 config source: `/venv/lib/python3.9/site-packages/streamlit/config.py`
- Streamlit 1.50.0 Plotly theme: `/venv/lib/python3.9/site-packages/streamlit/elements/lib/streamlit_plotly_theme.py`
- Existing app: `/app.py` (Streamlit 1.50.0, Plotly 5.24.1, Python 3.9)
- Existing stack: `.planning/codebase/STACK.md`
