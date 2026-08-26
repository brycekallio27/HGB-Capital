# Domain Pitfalls: Streamlit Custom CSS and Theming

**Domain:** Streamlit CSS injection, dark/light mode theming, financial dashboard styling
**Project:** Project Photizo — HGB Capital Investment Engine
**Researched:** 2026-02-18
**Confidence note:** WebSearch and WebFetch were unavailable during this research session. All findings are drawn from training knowledge (Streamlit versions up to ~1.4x, pre-August 2025 cutoff) plus direct codebase inspection. Version-specific claims about Streamlit 1.50 are marked LOW confidence where they could not be verified. Structural/behavioral pitfalls that have been stable across many Streamlit versions are marked MEDIUM or HIGH.

---

## Critical Pitfalls

Mistakes that cause rewrites, visual regressions, or unrecoverable state.

---

### Pitfall 1: Internal CSS Class Names Are Not Stable Across Streamlit Versions

**Confidence:** HIGH (well-documented community pattern, stable across versions through 1.4x)

**What goes wrong:**
Streamlit compiles its React frontend and generates hashed or semi-stable class names like `.stMetric`, `.stDataFrame`, `.stButton`, `.css-1kyxreq`, `.css-ffhzg2`. The `css-*` classes are build-artifact names — they change with every Streamlit release. Targeting `.css-*` classes in injected CSS is the single most common cause of styling that silently breaks on Streamlit version upgrades.

**Why it happens:**
The React frontend is compiled with CSS modules or emotion-based styling. Some class names are intentional semantic names (`stMetric`, `stButton`) that Streamlit maintains as stable. Others are generated hashes with no stability guarantee.

**Consequences:**
- Styles silently stop applying after a `pip install --upgrade streamlit`
- Community Cloud auto-upgrades Streamlit in some deployment configurations, causing unexpected visual regressions in production
- The `.css-*` targeting pattern is extensively documented in community tutorials from 2021–2023, making it easy to copy bad examples

**Prevention:**
- Use ONLY the semantic class names that Streamlit intentionally exposes: `.stApp`, `.stSidebar`, `.stButton`, `.stMetric`, `.stMetricValue`, `.stMetricDelta`, `.stTabs`, `.stTab`, `.stDataFrame`, `.stPlotlyChart`, `.stMarkdown`, `.stTextInput`, `.stSelectbox`, `.stSlider`, `.stExpander`, `.stAlert`
- Never target `.css-*` classes. If a browser inspector shows only `.css-*` classes on an element, test with attribute selectors or parent-child relationships using stable ancestors
- Pin Streamlit version in `requirements.txt` with exact version: `streamlit==1.50.0` (not `streamlit>=1.50`)
- Before upgrading Streamlit, do a visual regression check on all CSS-injected components

**Warning signs:**
- A style is working but you can only find `.css-*` classes on the element in DevTools
- Styles stop working after `pip install --upgrade streamlit`
- The CSS you wrote worked on one machine but not another (different pip-resolved versions)

**Phase risk:** ALL phases. Pin version before writing a single line of CSS.

---

### Pitfall 2: CSS Injection Placement — `st.markdown` Injects Into DOM Flow, Not `<head>`

**Confidence:** HIGH

**What goes wrong:**
`st.markdown('<style>...</style>', unsafe_allow_html=True)` does not inject into `<head>`. It injects the `<style>` block as an inline element inside Streamlit's component container. This creates two problems:

1. **Specificity ordering:** CSS that comes from later `st.markdown` calls can override earlier injections. If theme CSS is injected inside a tab `with` block rather than at the top of the script, it may not apply on first render or may be overridden by subsequent component renders.

2. **Re-injection on rerun:** Every time Streamlit re-runs the script (user interaction, cached data refresh), `st.markdown` CSS injections are re-evaluated. If the CSS injection is conditional on session state (e.g., `if st.session_state.theme == 'dark': inject_dark_css()`), the style block is re-injected on every rerun. This is usually fine but can cause a flash of unstyled content on the rerun cycle.

**Why it happens:**
Streamlit's execution model runs the full script top to bottom on every user interaction. CSS injection is not special-cased — it goes through the same component lifecycle as `st.text()`.

**Prevention:**
- Place ALL `st.markdown` CSS injections at the very top of the script, immediately after `st.set_page_config()` and before any tabs, columns, or conditional blocks
- Use a single consolidated CSS injection function (e.g., `inject_styles(theme)`) called once at script top. Do not scatter CSS injections throughout the script
- Never place `st.markdown` CSS injections inside `with tab_X:` blocks

**Warning signs:**
- Styles apply on page load but disappear after a button click
- Styles apply in one tab but not another
- A component styled correctly until you interact with an unrelated widget

**Phase risk:** Implementation start. Getting injection placement wrong on the first commit creates compounding confusion.

---

### Pitfall 3: Flash of Unstyled Content (FOUC) on Theme Toggle

**Confidence:** HIGH (inherent to Streamlit's rerun model)

**What goes wrong:**
The dark/light mode toggle via `session_state` works by: user clicks toggle → `session_state.theme` flips → Streamlit reruns the script → CSS injection reflects new theme. Between the user click and the rerun completing, there is a brief window where Streamlit renders with the previous CSS. On slow connections or during cache misses (e.g., `get_portfolio_performance` cache miss triggers yfinance calls), this rerun gap can be 500ms–3s, producing a visible FOUC.

Additionally, on the very first page load, `session_state` is not yet initialized. If CSS injection reads `st.session_state.theme` before it is set, either an exception is raised or a fallback branch is taken. If the fallback injects no CSS, the page renders completely unstyled until the user initializes state.

**Why it happens:**
Streamlit's client-server model cannot hide rerun latency. CSS is delivered per-rerun, not persisted client-side.

**Consequences:**
- Every theme toggle shows a flash of the opposite theme's colors
- First page load may flash default Streamlit light theme before custom dark theme applies
- More severe on Community Cloud (higher latency) than localhost

**Prevention:**
- Initialize `session_state.theme` immediately after `st.set_page_config()`, before any conditional reads:
  ```python
  if 'theme' not in st.session_state:
      st.session_state.theme = 'dark'  # default to dark (HGB brand)
  ```
- Use `config.toml` to set the base Streamlit theme close to your dark default so the unstyled flash is less jarring:
  ```toml
  # .streamlit/config.toml
  [theme]
  base = "dark"
  backgroundColor = "#0A0A0A"
  primaryColor = "#C5A059"
  ```
- Accept that FOUC on toggle is unavoidable in pure Streamlit. Document this as a known limitation for partners. It cannot be fully eliminated without a custom component.

**Warning signs:**
- Page flashes white/default Streamlit theme on first load
- Theme switch produces a visible color flash
- `KeyError: 'theme'` in session state reads

**Phase risk:** Theme toggle implementation (whichever phase first introduces the toggle button and CSS switching logic).

---

### Pitfall 4: `st.set_page_config()` Must Be the First Streamlit Call — Theme Config Cannot Be Dynamic

**Confidence:** HIGH

**What goes wrong:**
`st.set_page_config()` must be called before any other Streamlit command. It can only be called once per script run. This means you cannot use it to set the theme dynamically based on `session_state`. The `base`, `backgroundColor`, `primaryColor`, etc. keys in `st.set_page_config(page_title=..., layout=...)` can accept a `theme` dict in older Streamlit versions, but the canonical approach is `config.toml`.

More critically: if any code before `st.set_page_config()` raises an exception (e.g., `conn = st.connection(...)` fails), Streamlit will show an error using its default unstyled layout. The custom CSS has not been injected yet.

**Why it happens:**
This is an intentional Streamlit constraint. Page configuration is sent to the browser before any component rendering begins.

**Consequences:**
- Attempting `st.set_page_config()` after `st.title()` or any other call raises `StreamlitAPIException`
- The base theme (light/dark) cannot be changed at runtime — only CSS injection can override colors after initial render
- Errors during connection setup (`st.connection("gsheets")`) will display in unstyled Streamlit UI

**Prevention:**
- Keep `st.set_page_config()` as the literal first executable Streamlit statement, before imports of connection objects if those imports could fail
- Set `config.toml` theme to dark base: this ensures even the error pages and loading spinner match the HGB dark palette
- Do not attempt to pass `theme=` to `set_page_config()` dynamically — use CSS injection for runtime theme switching

**Warning signs:**
- `StreamlitAPIException: set_page_config() can only be called once per app, and must be called as the first Streamlit command in your script.`

**Phase risk:** Initial setup phase, before any CSS work begins.

---

### Pitfall 5: `@st.cache_data` Functions Capture Mutable DataFrame — Theme State Cannot Be a Cache Argument

**Confidence:** HIGH (derived from Streamlit's caching model, stable behavior)

**What goes wrong:**
The existing code uses `@st.cache_data(ttl=300)` on `get_portfolio_performance(df)`. The `df` input is the raw DataFrame from Google Sheets. There is a documented bug in the existing code: `get_portfolio_performance` mutates the input DataFrame in-place (`df['Market Value'] = ...`). When this function is cached, the mutated DataFrame is what gets returned on cache hits, but more importantly, the original `raw_df` variable in the calling scope may be mutated.

This has a CSS/theming interaction: if you add per-row styling using `df.style` to the cached function's output, and the styling depends on `session_state.theme` (e.g., positive gains are gold in dark mode, green in light mode), you cannot pass `session_state.theme` as an argument to a `@st.cache_data` function and have it cache correctly across both themes without double-caching. The cache key includes function arguments — `session_state.theme` is not passed, so conditional styling inside the cached function will be frozen on first call.

**Why it happens:**
`@st.cache_data` is keyed on serializable function arguments. `session_state` is not a function argument — it's a global. Any logic inside a cached function that reads `session_state` will read the value at first-call time and that value is baked into the cached return.

**Consequences:**
- `df.style.applymap(color_function)` inside a cached function uses the theme at cache-fill time, not the current theme
- Dataframe styling that is theme-aware must be applied OUTSIDE cached functions, in the main script body where `session_state.theme` is accessible per-rerun
- The existing in-place mutation bug (`df['Market Value'] = df['Shares'] * df['Current Price']`) can cause `ValueError: Cannot set a frame with no columns` errors if the cached DataFrame's column state drifts — adding `df = df.copy()` at the start of `get_portfolio_performance` is needed before styling work begins

**Prevention:**
- Apply `df.style` formatting OUTSIDE `@st.cache_data` functions, in the main script body
- Add `df = df.copy()` as the first line of `get_portfolio_performance` (already flagged in PROJECT.md)
- Never read `st.session_state` inside a `@st.cache_data` function
- Keep cached functions responsible for data fetch/compute only; style application is a rendering concern that belongs in the main execution path

**Warning signs:**
- Dataframe colors don't change when theme is toggled
- `ValueError` on DataFrame operations after cache hit
- Styling correct on first load but wrong after cache is invalidated

**Phase risk:** Dataframe styling phase. Any phase that adds `df.style` to a cached data function.

---

## Moderate Pitfalls

---

### Pitfall 6: Streamlit Tab Styling — `.stTab` vs `.stTabs` Selector Ambiguity

**Confidence:** MEDIUM

**What goes wrong:**
Streamlit's tab component wraps content in multiple nested containers. The stable selectors are `.stTabs` (the outer container), `.stTabs [data-baseweb="tab-list"]` (the tab button row), `.stTabs [data-baseweb="tab"]` (individual tab buttons), and `.stTabs [data-baseweb="tab-panel"]` (the content panel). The `data-baseweb` attributes come from Streamlit's use of the Base Web UI library and have been stable across many versions.

However, the active tab indicator (the bottom border/underline) is styled via an element with `data-baseweb="tab-highlight"` or through pseudo-elements on `[aria-selected="true"]` tab buttons. Attempting to style just the active tab text color requires targeting `[data-baseweb="tab"][aria-selected="true"]`.

**Consequences:**
- CSS targeting the wrong container makes tab content panels style correctly but tab headers remain default
- Using `.stTab` (singular) vs `.stTabs` (plural) targets different elements — one is the panel, one is the wrapper
- Active tab indicator line color is controlled by a deeply nested pseudo-element that may require `!important` overrides

**Prevention:**
- Use `data-baseweb` attribute selectors for tab elements, not class name selectors
- Test active vs inactive tab states explicitly with `!important` on color overrides
- Style tab headers and tab content panels as two separate CSS blocks

**Warning signs:**
- Tab content panels styled but tab header buttons still show default blue highlight
- Active tab underline stays default primary color despite override

**Phase risk:** Tab styling implementation.

---

### Pitfall 7: `st.metric` Delta Color Cannot Be Fully Overridden with Simple CSS

**Confidence:** MEDIUM

**What goes wrong:**
`st.metric` renders a value, a label, and an optional delta with an arrow icon and color. The delta color (red for negative, green for positive) is controlled by Streamlit's internal logic and set as inline `color` styles on the delta span element. Overriding inline styles requires `!important` in CSS. The metric card container itself (`.stMetric`) is styleable, but the delta arrow icon color is set via SVG `fill` attribute, not CSS `color`, and requires a separate `svg path` selector with `!important`.

The PROJECT.md states hero metrics will be redesigned as custom KPI cards rather than default `st.metric`. This avoids the problem entirely — use `st.markdown` HTML blocks for the KPI cards instead of `st.metric`. This is the correct approach.

**Consequences:**
- Attempting to override delta colors on `st.metric` requires `!important` cascades
- SVG arrow icon color requires targeting `.stMetricDelta svg path { fill: #C5A059 !important; }`
- If using standard `st.metric`, the positive/negative semantic color coding (green/red) cannot be changed to gold without losing the semantic meaning

**Prevention:**
- Replace hero `st.metric` calls with custom HTML/CSS KPI card blocks for full styling control (as planned in PROJECT.md)
- If keeping any `st.metric` usage, accept that delta colors require `!important` and target both the text span and the SVG path separately
- Do not fight Streamlit's metric rendering — wrap the metric in a `st.container()` and overlay custom HTML instead

**Warning signs:**
- Metric value styled correctly but delta text/arrow remains default green/red
- CSS targeting `.stMetric` changes the card but not the delta colors

**Phase risk:** Portfolio War Room redesign (hero KPI cards).

---

### Pitfall 8: Plotly Chart Containers — Streamlit vs Plotly Theming Layers Conflict

**Confidence:** HIGH

**What goes wrong:**
A Plotly chart in Streamlit has two independent theming layers:
1. **Streamlit container:** The `.stPlotlyChart` wrapper div — height, margins, border, background of the frame
2. **Plotly figure layout:** `fig.update_layout(paper_bgcolor=..., plot_bgcolor=..., font_color=...)` — the chart's own background, gridlines, axis colors, legend

These are independent and both must be set for a coherent look. If only the Plotly layout is updated (dark background) but the Streamlit container is not (light container background), you get a dark chart inside a white box. Conversely, styling the container but not the figure gives a dark-framed chart with a white Plotly canvas.

Additionally, Plotly charts render in an iframe in some Streamlit deployment configurations. CSS injected via `st.markdown` does NOT penetrate iframe boundaries. However, in standard Streamlit rendering (non-iframe), the chart renders in the same DOM and container CSS applies.

**Consequences:**
- Partial theming: dark chart content inside a light container, or vice versa
- `paper_bgcolor` and `plot_bgcolor` must BOTH be set — `paper_bgcolor` is the outer chart area, `plot_bgcolor` is the inner plot area
- Pie charts (used in this project) have `paper_bgcolor` only (no `plot_bgcolor` for donut charts)

**Prevention:**
- Create a `apply_chart_theme(fig, theme)` function that sets all Plotly layout properties consistently
- Required properties for dark mode: `paper_bgcolor='#111111'`, `plot_bgcolor='#111111'`, `font=dict(color='#E0E0E0')`, `colorway=[gold palette]`
- Required properties for chart containers: add CSS on `.stPlotlyChart > div { background: #111111; border-radius: 8px; }`
- Apply chart theme function to every `fig` before `st.plotly_chart()` — do not rely on CSS alone

**Warning signs:**
- Charts have correct colors but are surrounded by a white/grey border box
- Chart axes and labels are dark but the background inside the chart is still white
- Donut charts show background mismatch between the hole and the outer ring

**Phase risk:** Chart styling (all three tabs have charts).

---

### Pitfall 9: Sidebar CSS Selectors — `.stSidebar` vs `[data-testid="stSidebar"]`

**Confidence:** MEDIUM

**What goes wrong:**
The sidebar can be targeted by either `.stSidebar` (class-based) or `[data-testid="stSidebar"]` (attribute-based). Streamlit has been inconsistent about which is present across versions. In Streamlit 1.2x+, `data-testid` attributes were added as stable testing anchors and are generally more reliable than class names for structural elements.

However, the sidebar's collapsed/expanded state changes the DOM structure — when collapsed, the sidebar content container is hidden and a toggle button is rendered instead. CSS that targets sidebar content may need to account for both states.

**Consequences:**
- `.stSidebar` styling may not apply in collapsed state
- Custom sidebar background color may not extend to full height if `height: 100vh` is not set on the correct parent
- Sidebar header (the "Operations" text in this project) is inside `.stSidebar .stMarkdown` and requires a separate selector from the sidebar background

**Prevention:**
- Use `[data-testid="stSidebar"]` as the primary selector (more stable than `.stSidebar` class)
- Set sidebar background on BOTH the sidebar container and its direct child: `[data-testid="stSidebar"] > div:first-child { background-color: #111111; }`
- Test sidebar in both expanded and collapsed states

**Warning signs:**
- Sidebar background correct when expanded but reverts to default when collapsed
- Custom sidebar colors apply only to part of the sidebar height (stops before the bottom)

**Phase risk:** Sidebar styling implementation.

---

### Pitfall 10: `session_state` Initialization Race — Theme Applied Before State Exists

**Confidence:** HIGH

**What goes wrong:**
On the very first script execution (cold start), `st.session_state` is empty. Any code that reads `st.session_state.theme` before setting a default will raise a `KeyError` or `AttributeError`. This is particularly dangerous when the theme CSS injection happens early in the script (as it should) — it is one of the first things that reads session state.

In the current app, `user = st.sidebar.selectbox("Partner Login", ...)` does not use session state. Once the dark/light toggle is added, state initialization order becomes critical.

Additionally, using `st.session_state.theme = 'dark'` as an initial assignment (not checking first) will reset the theme on every rerun, overriding the user's toggle. The correct pattern is:
```python
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
```

**Consequences:**
- `KeyError: 'theme'` on first load if initialization is not guarded
- Theme toggle resets to default on every page interaction if initialization is unconditional
- If initialization is placed inside a tab block, it only runs when that tab is active — leading to missing state when other tabs are visible

**Prevention:**
- Place ALL `session_state` initializations at the very top of the script, after `st.set_page_config()` and before any Streamlit rendering commands, in a dedicated "state initialization block"
- Use the `if 'key' not in st.session_state:` guard pattern exclusively — never unconditional assignment
- Initialize all session state keys in one place, not scattered through the script

**Warning signs:**
- `KeyError` or `AttributeError` on first page load
- Theme toggle works once but resets on next user interaction
- Theme only applied correctly on specific tabs

**Phase risk:** First implementation of any session state for theme management.

---

### Pitfall 11: `dataframe` Styling Via `df.style` — Pandas Styler Limitations

**Confidence:** HIGH (Pandas behavior, stable)

**What goes wrong:**
The current code uses `df.style.format({...})` for number formatting in `st.dataframe()`. Adding visual styling (background colors, font colors) via `df.style.applymap()` or `df.style.apply()` works, but Streamlit's `st.dataframe()` component does not fully honor all Pandas Styler properties — particularly cell `background-color` via `applymap` has inconsistent rendering in Streamlit's Arrow-based table rendering.

Streamlit 1.1x+ switched the internal table renderer to Apache Arrow for performance. Arrow-rendered tables honor some Pandas Styler properties but not all. Specifically: cell background colors from `applymap` do render, but they are overridden by Streamlit's own hover/selection row highlighting CSS, which requires additional CSS injection to neutralize.

Also, `st.dataframe()` renders in a scrollable container with its own internal styling. The outer Streamlit container (`.stDataFrame`) is accessible via CSS, but the inner table cells are rendered in a shadow DOM-like structure that can be difficult to target.

**Consequences:**
- `df.style.applymap(highlight_positive_returns)` works in a Jupyter notebook but renders differently in Streamlit
- Row hover colors from Streamlit's default theme override custom cell background colors
- Column header styling via `df.style.set_table_styles()` has limited support in Streamlit's Arrow renderer

**Prevention:**
- Use `df.style.format()` for number formatting (works reliably)
- For color coding rows (e.g., positive return = gold background), use `df.style.apply()` at the row level, not `applymap()` at the cell level — more reliable in Arrow renderer
- For deep table customization, use `st.dataframe()` with `column_config` parameter (available in Streamlit 1.2x+) instead of Pandas Styler — `column_config` is the officially supported styling API for `st.dataframe`
- Test DataFrame styling in Streamlit specifically, not just in Jupyter

**Warning signs:**
- Pandas Styler colors look correct in Jupyter preview but wrong in Streamlit
- Row highlight on hover overrides custom background colors
- Column headers not styled despite `set_table_styles()` call

**Phase risk:** Portfolio dataframe and optimizer results dataframe styling.

---

## Minor Pitfalls

---

### Pitfall 12: `!important` Overuse Creates Cascade Debt

**What goes wrong:**
Streamlit's default CSS has high-specificity rules. When overrides don't work, the temptation is to add `!important` to everything. This creates a specificity arms race where nothing can be overridden later without even more `!important` declarations, and debugging becomes extremely difficult.

**Prevention:**
- Use specificity strategically: increase selector specificity before reaching for `!important`
- Example: instead of `color: gold !important`, use `.stApp .stSidebar button { color: gold; }` — the chained selectors raise specificity without `!important`
- Reserve `!important` for known Streamlit inline style overrides (delta colors, some SVG fills)
- Document every `!important` usage with a comment explaining why it is necessary

**Phase risk:** Throughout implementation.

---

### Pitfall 13: Streamlit `st.html()` vs `st.markdown()` — Different Behavior

**Confidence:** MEDIUM (st.html was added in Streamlit ~1.3x)

**What goes wrong:**
Streamlit 1.3x+ added `st.html()` as a dedicated HTML injection function, distinct from `st.markdown(unsafe_allow_html=True)`. `st.html()` renders in an iframe sandbox in recent versions, meaning injected CSS in `st.html()` does NOT apply to the parent Streamlit document. Only `st.markdown(unsafe_allow_html=True)` injects CSS that affects the full page.

If a developer (following new Streamlit docs) uses `st.html('<style>...</style>')` for CSS injection, the styles will be silently sandboxed and have no effect on the rest of the app.

**Prevention:**
- Use `st.markdown('<style>...</style>', unsafe_allow_html=True)` exclusively for global CSS injection (as the project already plans to do)
- `st.html()` is appropriate only for self-contained HTML components that need no interaction with the parent page styles
- If Streamlit 1.50's `st.html()` behavior differs from this description, verify in DevTools whether the content is in an iframe

**Warning signs:**
- CSS injection via `st.html()` has no visible effect
- Styles apply correctly when moved to `st.markdown()` but not via `st.html()`

**Phase risk:** If any team member uses `st.html()` for CSS injection instead of `st.markdown()`.

---

### Pitfall 14: Streamlit Config.toml Is Not Sufficient for Full Dark Mode

**Confidence:** HIGH

**What goes wrong:**
`config.toml` with `[theme]` settings provides a baseline dark theme for Streamlit's built-in components (buttons use `primaryColor`, background uses `backgroundColor`). However, `config.toml` does NOT control:
- Plotly chart colors (always requires `fig.update_layout()`)
- Custom metric card HTML (always requires inline CSS)
- Dataframe header/cell colors (not configurable via config.toml)
- Sidebar branding elements
- Tab panel content backgrounds

The mistake is setting `config.toml` and assuming dark mode is complete. It handles the Streamlit chrome (background, text, widget colors) but not content-area theming.

**Prevention:**
- Use `config.toml` for the Streamlit structural chrome (page background, widget primary color, text color)
- Apply CSS injection for all content-area overrides
- Apply `fig.update_layout()` for all Plotly chart theming
- The two systems are complementary, not redundant

**Warning signs:**
- App background is dark but charts have white backgrounds
- Buttons use gold color but dataframes are still light-themed
- Sidebar background correct but sidebar content area is light

**Phase risk:** Initial theme setup.

---

### Pitfall 15: Community Cloud — CSS Injection Behavior May Differ From Local Dev

**Confidence:** MEDIUM

**What goes wrong:**
Streamlit Community Cloud runs apps in a containerized environment. CSS injected via `st.markdown` should behave identically to local development, but two differences have been observed in the community:

1. **Font loading:** `@font-face` declarations in injected CSS may not load external fonts correctly due to CSP (Content Security Policy) headers on Community Cloud
2. **Caching and CDN:** If Streamlit Community Cloud caches static assets differently, injected CSS may be stale after a deployment

**Prevention:**
- Test all CSS on a deployed Community Cloud instance, not just localhost
- Use system fonts or Google Fonts via `<link>` in `st.markdown` rather than `@font-face` declarations
- For font imports: `st.markdown('<link href="https://fonts.googleapis.com/css2?family=Inter..." rel="stylesheet">', unsafe_allow_html=True)`

**Warning signs:**
- Fonts render correctly locally but fall back to system fonts on Community Cloud
- CSS changes don't appear after redeployment (try force-refreshing or clearing Community Cloud cache)

**Phase risk:** Typography/font phase.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Initial theme setup + config.toml | config.toml doesn't cover everything (Pitfall 14) | Set up both config.toml AND CSS injection simultaneously |
| session_state theme toggle button | State initialization race (Pitfall 10), FOUC on toggle (Pitfall 3) | Initialize state at script top; accept FOUC as known limitation |
| Sidebar redesign | Selector ambiguity `.stSidebar` vs `data-testid` (Pitfall 9); collapsed state not styled | Use `[data-testid="stSidebar"]`; test collapsed and expanded |
| Hero KPI card redesign (replacing st.metric) | st.metric delta color limitations (Pitfall 7) | Use custom HTML cards instead of st.metric for full control |
| Tab styling | `.stTab` vs `data-baseweb` selector fragility (Pitfall 6) | Use `[data-baseweb="tab"]` selectors, not class names |
| Plotly chart theming | Two-layer theming (Streamlit container + Plotly layout) (Pitfall 8) | Always set both `fig.update_layout()` AND `.stPlotlyChart` CSS |
| Dataframe styling (portfolio table, optimizer table) | Arrow renderer limits Pandas Styler (Pitfall 11); cache/style conflict (Pitfall 5) | Use `column_config` for styling; apply `df.style` outside cached functions |
| Any CSS override not working | Fragile `.css-*` class targeting (Pitfall 1) | Never use `.css-*` selectors; use semantic or `data-*` selectors only |
| CSS injection not applying consistently | Injection placement in DOM flow (Pitfall 2) | Single injection function at script top |
| Future Streamlit upgrade | CSS class name breakage (Pitfall 1) | Pin version: `streamlit==1.50.0`; visual regression check before upgrade |

---

## Confidence Assessment

| Pitfall | Confidence | Basis |
|---------|------------|-------|
| CSS class name instability (Pitfall 1) | HIGH | Documented extensively in Streamlit community; stable behavioral pattern across versions |
| st.markdown injection placement (Pitfall 2) | HIGH | Inherent to Streamlit's script execution model |
| FOUC on theme toggle (Pitfall 3) | HIGH | Inherent to Streamlit's client-server rerun model |
| set_page_config constraints (Pitfall 4) | HIGH | Official Streamlit API constraint, unchanged across versions |
| cache_data + session_state interaction (Pitfall 5) | HIGH | Inherent to @st.cache_data's keying model |
| Tab data-baseweb selectors (Pitfall 6) | MEDIUM | Base Web library integration is documented; specific attributes not independently verified for 1.50 |
| st.metric delta styling (Pitfall 7) | MEDIUM | Observed behavior in Streamlit 1.2x-1.4x; may have changed in 1.50 |
| Plotly two-layer theming (Pitfall 8) | HIGH | Plotly/Streamlit boundary is clearly separate; both must be configured |
| Sidebar selector instability (Pitfall 9) | MEDIUM | data-testid attributes added in 1.2x; stable in recent versions |
| session_state initialization race (Pitfall 10) | HIGH | Fundamental Python/Streamlit execution model behavior |
| df.style Arrow renderer limits (Pitfall 11) | HIGH | Arrow renderer adoption is documented; limitations are well-known |
| !important overuse (Pitfall 12) | HIGH | Standard CSS cascade behavior |
| st.html sandboxing (Pitfall 13) | MEDIUM | st.html iframe behavior was introduced in 1.3x range; verify for 1.50 |
| config.toml scope limits (Pitfall 14) | HIGH | config.toml theming scope is documented and does not include Plotly/custom HTML |
| Community Cloud CSP differences (Pitfall 15) | MEDIUM | Observed in community reports; not independently verified |

---

## Sources

**Note:** WebSearch and WebFetch were unavailable during this research session. The following sources informed this document through training knowledge only — they should be consulted directly before implementation to verify version-specific details for Streamlit 1.50.

- Streamlit theming docs: `https://docs.streamlit.io/develop/concepts/configuration/theming`
- Streamlit API reference — st.markdown: `https://docs.streamlit.io/develop/api-reference/text/st.markdown`
- Streamlit API reference — st.dataframe column_config: `https://docs.streamlit.io/develop/api-reference/data/st.dataframe`
- Streamlit API reference — st.html: `https://docs.streamlit.io/develop/api-reference/utilities/st.html`
- Streamlit GitHub discussions on CSS injection (search: "custom css" in streamlit/streamlit issues)
- Plotly Python figure layout docs: `https://plotly.com/python/figure-factories/`
- Pandas Styler docs: `https://pandas.pydata.org/docs/user_guide/style.html`
