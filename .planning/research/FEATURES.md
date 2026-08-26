# Feature Landscape: Premium Fintech Dashboard UI

**Domain:** Professional investment dashboard — internal fintech tool for institutional partners
**Project:** HGB Capital (Project Photizo) — UI redesign milestone only
**Researched:** 2026-02-18
**Confidence note:** WebSearch and WebFetch tools unavailable. All findings are from training data (cutoff August 2025) cross-referenced against the existing codebase and PROJECT.md. Patterns are drawn from Bloomberg Terminal, Robinhood web app, Wealthfront dashboard, Betterment, and Monzo/Revolut fintech UI conventions.

---

## Table Stakes

Features any professional dashboard must have. Missing = product feels like a prototype.

| Feature | Why Expected | Complexity in Streamlit | Notes |
|---------|--------------|------------------------|-------|
| Dark background with high-contrast text | Fintech convention since Bloomberg Terminal; reduces eye strain on number-dense screens | Low — CSS injection on `body`, `.stApp` | Default Streamlit light theme reads as "hackathon project" immediately |
| Consistent accent color throughout | Single primary color for interactive elements, highlights, positive values creates visual coherence | Low — CSS custom properties on buttons, metrics, tabs | Currently inconsistent default Streamlit blues |
| KPI cards with strong typographic hierarchy | Dollar values must dominate; labels must recede. Partners scan cards in under 1 second | Medium — CSS on `.stMetric`, custom HTML metric blocks | Current `st.metric` widgets have no visual weight |
| Green/red semantic color for gains/losses | Universal fintech convention: green = positive P&L, red = negative. Not brand gold | Low — CSS on delta values in `.stMetric [data-testid="stMetricDelta"]` | Applies to both the metric delta and any colored cells in dataframes |
| Chart dark theme matching app background | Charts on white background inside a dark app read as "components dropped in from another product" | Low — Plotly `template="plotly_dark"` + `fig.update_layout(paper_bgcolor, plot_bgcolor)` | Currently default plotly white |
| Monospace or tabular-figures font for numbers | Dollar values must align at decimal points. Proportional fonts cause misalignment in tables | Low — CSS `font-variant-numeric: tabular-nums` on metric and table cells | Bloomberg, every trading terminal — absolute table stakes |
| Clear tab/section separation | Partners need to know which context they are in without reading a label | Low — CSS on `.stTabs [data-baseweb="tab"]`, active tab styling | Current tabs are subtle gray underlines |
| Loading states that feel deliberate | Spinners/skeleton states tell the partner the data is live, not stale. "It's loading" = product is alive | Low — Streamlit's `st.spinner` is already in the codebase, needs styling | Currently default blue spinner |
| No horizontal scrollbars on dataframes | Data that overflows and requires horizontal scrolling reads as broken | Low — CSS `overflow-x: hidden` + column width management via `use_container_width=True` | Already using `use_container_width=True`, need CSS enforcement |
| Responsive column layouts | Metrics and charts should not stack awkwardly at any common desktop viewport width | Low — Streamlit's column system already handles this; CSS can reinforce minimum widths | Desktop-first is acceptable per PROJECT.md constraints |

---

## Differentiators

Features that separate a premium internal tool from a competent one. Not universally expected, but immediately noticed.

### Typography

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Inter or DM Sans as primary font (via Google Fonts) | Bloomberg uses proprietary fonts; Robinhood uses Inter; modern fintech has converged on clean geometric sans-serifs over system fonts | Low — single `@import` in CSS injection block | System fonts (Arial, Helvetica) read as default; one line of CSS changes the entire character of the app |
| Tight tracking on large headings (letter-spacing: -0.5px to -1px) | Large headings with negative tracking read as intentional and designed, not default rendered | Low — CSS on `h1`, `h2`, `h3` elements | Premium fintech (Stripe, Linear, Robinhood) consistently uses negative tracking at large sizes |
| Uppercase + extended tracking on section labels | Labels like "TOTAL EQUITY" in `letter-spacing: 0.1em` uppercase read as institutional, not casual | Low — CSS on metric labels, section headers | Bloomberg Terminal uses all-caps labels; creates visual hierarchy between data and metadata |
| Font weight contrast: bold values, light labels | In a KPI card, the dollar amount should be `font-weight: 700`; the label should be `font-weight: 400` or `300`. Contrast creates hierarchy without size difference | Low — CSS on `.stMetric` child elements | Current Streamlit metrics have insufficient weight contrast |

### KPI Card Design

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Custom KPI cards via `st.markdown` HTML blocks instead of `st.metric` | `st.metric` has no visual customization beyond CSS overrides. Custom HTML cards allow border-left accent, icon, micro-sparkline area, custom hover states | Medium — replace the 3 `st.metric` calls in the War Room header with `st.markdown` HTML inside columns | This is the single highest-leverage visual change in the entire app |
| Border-left accent stripe on cards | A 3px left border in the brand gold (`#C5A059`) on each KPI card is a Bloomberg/Refinitiv pattern that signals "this is a live data tile" | Low — CSS on the card `div` container | Zero implementation cost once custom card HTML is written |
| Subtle card background separation | Cards at `#111111` on `#0A0A0A` app background (11-point luminance difference) creates depth without shadow. Shadow-heavy cards read as consumer fintech (Robinhood); shadow-free cards read as institutional (Bloomberg) | Low — CSS on card wrappers | Wealthfront uses soft shadows; Bloomberg uses none; given HGB's brand positioning, shadow-free is more appropriate |
| Delta indicator as directional pill, not plain text | The default Streamlit delta is a small arrow and colored text. A small pill/badge with border reads as a designed component. Example: `[▲ 12.4%]` in a subtle green pill | Medium — requires custom HTML in metric card | Robinhood, Wealthfront, and Coinbase Pro all use this pattern |
| Hover state on cards | A very subtle `box-shadow: 0 0 0 1px #C5A059` on hover signals interactivity even if the card is not clickable | Low — CSS `:hover` on card containers | Small detail, disproportionate premium signal |

### Chart Styling

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Gold primary trace color, not Plotly default blue | Plotly default blue (`#636EFA`) is universally associated with "I didn't customize this chart." Gold trace on dark background reads as intentional | Low — `fig.update_traces(marker_color='#C5A059', line_color='#C5A059')` | One line per chart |
| Transparent chart background, not white or dark gray | Charts should feel embedded in the page, not dropped in. `paper_bgcolor='rgba(0,0,0,0)'`, `plot_bgcolor='rgba(0,0,0,0)'` makes charts feel native to the dark background | Low — `fig.update_layout()` call | This plus matching gridline color is the single biggest chart improvement |
| Muted gridlines in `#1A1A1A` or `#2A2A2A` | Gridlines that match the background color family instead of stark white lines read as professional and considered | Low — `fig.update_layout(xaxis=dict(gridcolor='#1A1A1A'), yaxis=dict(...))` | Bloomberg Terminal uses barely-visible gridlines; Robinhood removes them entirely on key charts |
| No Plotly mode bar (or minimal) | The default Plotly toolbar (zoom, download, autoscale icons) signals "this is a library component." Hiding or minimizing it makes charts feel native to the product | Low — `config=dict(displayModeBar=False)` in `st.plotly_chart()` or `displaylogo=False` | Internal tool does not need download-to-PNG functionality |
| Consistent axis label styling | Axis labels in the same font family as the app body, at a size that recedes behind the data | Low — `fig.update_layout(font=dict(family='Inter, sans-serif', color='#9E9E9E'))` | Plotly's default font does not match any custom font set on the page |
| Donut chart (existing) with gold primary slice, muted secondaries | The portfolio allocation donut should use `#C5A059` as the first color, then a sequence of muted tones. Currently uses `px.colors.sequential.RdBu` which is actively misleading (red = bad?) | Low — custom `color_discrete_sequence` passed to px.pie | Red/blue sequential palette on a portfolio allocation chart implies risk coding that is not actually there |

### Sidebar Design

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| HGB Capital logo/wordmark at top of sidebar | Every professional product has a logo in the sidebar. The current sidebar has a plain `st.sidebar.header("Operations")` text | Low — `st.sidebar.markdown` with HTML containing styled "HGB CAPITAL" text in brand gold + muted tracking | Logo doesn't need to be an image; styled text with the right font and color is sufficient |
| Partner indicator as a styled session badge, not a bare selectbox | Currently `st.sidebar.selectbox("Partner Login", [...])`. Replace with styled treatment that shows active partner prominently after selection | Medium — CSS on sidebar selectbox + a conditional `st.sidebar.markdown` display block for active partner | Robinhood shows account name prominently in nav; Bloomberg shows active user in the terminal header |
| Sidebar divider/navigation group labels | Grouping sidebar controls with thin `#1A1A1A` horizontal rules and uppercase group labels (`NAVIGATION`, `SESSION`) creates structure | Low — `st.sidebar.markdown("<hr>", unsafe_allow_html=True)` with CSS | Current sidebar has no visual grouping |
| Subtle sidebar background separation | Sidebar background at `#0D0D0D` vs app background at `#0A0A0A` creates a 3-shade distinction: app bg / sidebar bg / card bg | Low — CSS on `[data-testid="stSidebar"]` | Without this, sidebar and content area visually merge |
| Refresh button styled as an outlined secondary action | Current "Refresh Portfolio" button is a default Streamlit primary button. It should be a lower-visual-weight outlined or ghost button — it is a maintenance action, not a primary call to action | Low — CSS on `.stButton button` scoped to the refresh context, or global secondary button style | CTA hierarchy: primary (Optimize, Add to Watchlist) vs secondary (Refresh) |

### Data Tables

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Alternating row shading at very low contrast | `#111111` / `#141414` alternating rows aid scanning without creating the visual noise of strong stripe colors | Low — CSS on `.stDataFrame tbody tr:nth-child(even)` | Strong alternating colors (light gray / white) read as Excel; subtle shading reads as terminal |
| Positive/negative value coloring in Return column | Return (%) column should show green for positive, red for negative values inline. Streamlit 1.50 supports `st.dataframe` with column config that accepts style functions | Medium — requires `st.dataframe(df.style.applymap(...))` which is already partially in use | The existing `.style.format(...)` call can be extended with `.applymap(color_returns, subset=['Return (%)'])` |
| Tight row height in tables | Default Streamlit table rows are tall. Reducing padding to `4px 8px` allows more data per screen, which reads as dense and professional (Bloomberg density) vs spacious and consumer (Robinhood) | Low — CSS on `.stDataFrame td, .stDataFrame th` | Partners checking holdings daily will prefer seeing all positions at once |
| Column header uppercase with letter spacing | `TICKER`, `SECTOR`, `RETURN` in small-caps or uppercase with tracking reads as Bloomberg-style | Low — CSS on `.stDataFrame th` | Single CSS rule |
| Border-bottom only on table rows, no vertical lines | Vertical grid lines in tables read as spreadsheet. Horizontal-only lines read as a designed data table (every modern fintech app) | Low — CSS on `.stDataFrame td` | `border-right: none; border-left: none; border-bottom: 1px solid #1A1A1A` |

### Micro-Details (High Signal, Low Effort)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Section header with gold left-border accent | A `3px solid #C5A059` left border on `<h3>` or section header `<div>` elements reads as a deliberate design decision | Low — CSS on `h3` or a custom `st.markdown` header component | Bloomberg uses no decoration; Robinhood uses color sections; left-border is a middle ground suitable for a dashboard |
| Input focus ring in brand gold | When partner clicks the ticker input, the focus ring should be `#C5A059` not default blue | Low — CSS on `input:focus, textarea:focus` | Small detail but jarring when blue appears inside a gold-themed product |
| Tab active state in gold underline, not gray | Current active tab has a thin default-blue or gray underline. Gold underline on active tab reinforces the brand on every interaction | Low — CSS on `.stTabs [data-baseweb="tab"][aria-selected="true"]` | One CSS rule |
| Button hover state using gold, not default blue | Streamlit default button hovers turn blue. Gold hover on buttons reads as intentional theming | Low — CSS on `.stButton button:hover` | Jarring color switches undermine the overall theme |
| "Last updated" timestamp display | A small muted text showing "Data as of HH:MM" tells partners the data freshness level. Builds trust in live data | Low — Python: `st.sidebar.caption(f"Data as of {datetime.now().strftime('%H:%M')}")` | Robinhood, every portfolio tracker shows data freshness |

---

## Anti-Features

Patterns that actively make a dashboard look amateur. Deliberately avoid these.

| Anti-Feature | Why It Reads as Amateur | What to Do Instead |
|--------------|------------------------|--------------------|
| Default Streamlit blue color scheme | Signals no customization was applied. Blue is associated with "default library output" | Replace all blue with brand gold via CSS injection |
| White/light chart backgrounds inside a dark app | Creates a jarring light box effect. Looks like components from a different product pasted in | Use `paper_bgcolor='rgba(0,0,0,0)'` and `plot_bgcolor='rgba(0,0,0,0)'` on all Plotly charts |
| Emojis in section headers and tab names | Currently: `"📊 Portfolio War Room"`, `"🔬 Analysis Lab"`, `"⚙️ Portfolio Optimizer"`, `"🎯 Watchlist Targets"`. Emojis in fintech UI reads as a side project, not an institutional product. Bloomberg has zero emojis. Refinitiv has zero. Every serious terminal has zero. | Replace with text-only tab names and use typographic hierarchy / brand color for visual interest |
| `st.divider()` used as a design pattern | Current app uses 4+ `st.divider()` calls to separate sections. The default divider is a medium-gray horizontal rule that creates dead space without structure | Replace with tighter section spacing via CSS margin manipulation and/or branded section headers with gold accents |
| `st.write("**Holdings (By Size)**")` style labels | Bare `st.write` calls for section labels produce inconsistent, unstyled text that has no visual connection to the section they label | Use a reusable `section_header(text)` helper function that outputs styled `st.markdown` HTML |
| `st.info()` and `st.warning()` default callout boxes | Blue info boxes and orange warning boxes are visually loud and break the dark theme | Style custom alert blocks via CSS on `.stAlert`, or replace with inline muted text styled to match brand |
| `st.success("Synced!")` as feedback | Green success banner for a write operation reads as consumer-grade feedback. Use a brief, styled in-place confirmation message | Style `.stAlert[data-baseweb="notification"]` or use `st.toast()` (available in Streamlit 1.31+) for non-disruptive feedback |
| Default Streamlit tab emoji + label format | Two visual elements (emoji + text) compete for attention in the tab label. Tabs should have a single clear label | Text-only tabs |
| Overly wide input controls that span the full container | `st.text_input` and `st.text_area` at full width for a ticker symbol input reads as undesigned | Use `st.columns` to constrain inputs to appropriate widths |
| Red/blue sequential colorscale on portfolio allocation | `px.colors.sequential.RdBu` on the sector pie chart implies a risk-coding that doesn't exist. Red sectors look dangerous even if they are not | Custom color sequence using gold, muted gold, and neutral grays |
| `st.subheader("Portfolio Optimizer")` as the tab title | Streamlit places the subheader directly below the tab, creating a redundant label (tab label + subheader say the same thing) | Remove redundant subheaders inside tabs; use the tab as the header |
| Capital letters mixed with lowercase in metric labels | `st.metric("Total Equity", ...)` and `st.metric("Unrealized P&L", ...)` — inconsistent casing across metrics creates typographic noise | Standardize: either all sentence case or all uppercase-tracked labels, consistently |
| Bare `st.caption("No recent news available.")` | Fallback states styled with `st.caption` produce very small, very muted text that looks like a bug rather than a designed empty state | Design an explicit empty state: icon + message, styled consistently |

---

## Feature Dependencies

```
Custom KPI Cards → CSS Injection System (must be set up first)
Chart Theming → Dark background CSS (charts must match a dark background to work)
Sidebar Redesign → Dark background CSS (sidebar color depends on base app color)
Table Styling → CSS Injection System
Custom Tab Styling → CSS Injection System
Font Import → CSS Injection System (all typography depends on font being loaded)
Section Headers (custom) → Font Import (Inter/DM Sans must load before headers render correctly)
Dark/Light Toggle → CSS Injection System (toggle switches between two CSS variable sets)
```

The CSS injection system is the root dependency for every visual feature. It must be implemented first as a single coherent block, not accumulated as ad-hoc `st.markdown` calls scattered through the file.

---

## MVP Recommendation

The minimum set of changes that moves the app from "prototype" to "professional":

1. **CSS injection system** — Single `st.markdown` block at the top of `app.py` injecting:
   - App background `#0A0A0A`
   - Card background `#111111`
   - Brand gold accent `#C5A059` on tabs, buttons, focus rings
   - Inter font via Google Fonts `@import`
   - Tabular numeric figures on all data cells
   - Remove Streamlit's default top padding and hamburger menu (known CSS targets)

2. **Plotly dark theme** — Applied consistently to all 4 charts (2 pie charts + 1 bar chart in Analysis Lab + 1 bar chart in Optimizer) via a single `apply_chart_theme(fig)` helper function

3. **Remove emojis from all labels** — Tab names, section headers, subheaders. High-signal change, zero code complexity.

4. **Custom HTML KPI cards for War Room hero metrics** — Replace the 3 `st.metric` calls with `st.markdown` HTML cards using border-left accent, uppercase label, large bold value, styled delta pill.

5. **Gold-on-dark active tab indicator** — One CSS rule. Disproportionate impact.

Defer to a follow-on pass:
- Dark/light mode toggle (increases CSS complexity significantly; adds session state management)
- Per-row return coloring in dataframes (medium complexity for moderate visual gain)
- Sidebar logo treatment (low priority vs. the main content area)
- Optimizer results polish (lower-traffic tab; use War Room budget first)

---

## Streamlit CSS Target Reference

The following CSS selectors are the known injection targets for Streamlit 1.50. These are based on training data and the existing Streamlit component structure — **verify selector names against live browser dev tools during implementation.**

| Element | CSS Selector | Notes |
|---------|-------------|-------|
| App background | `.stApp` | Top-level container |
| Main content area | `.main .block-container` | Controls padding and max-width |
| Sidebar | `[data-testid="stSidebar"]` | Full sidebar panel |
| Metric container | `[data-testid="stMetric"]` | KPI card wrapper |
| Metric value | `[data-testid="stMetricValue"]` | The large number |
| Metric label | `[data-testid="stMetricLabel"]` | The small label text |
| Metric delta | `[data-testid="stMetricDelta"]` | Up/down percentage |
| Tab bar | `.stTabs [data-baseweb="tab-list"]` | Container for all tabs |
| Individual tab | `.stTabs [data-baseweb="tab"]` | Each tab button |
| Active tab | `.stTabs [data-baseweb="tab"][aria-selected="true"]` | Selected tab state |
| Buttons | `.stButton > button` | All Streamlit buttons |
| Text inputs | `.stTextInput input` | Single-line inputs |
| Text areas | `.stTextArea textarea` | Multi-line inputs |
| Sliders | `.stSlider` | Slider track and thumb |
| Dataframe | `.stDataFrame` | Full table wrapper |
| Dataframe header | `.stDataFrame th` | Column header cells |
| Dataframe cells | `.stDataFrame td` | Data cells |
| Alert/info/warning | `[data-testid="stAlert"]` | Info, warning, error banners |
| Spinner | `.stSpinner` | Loading indicator |
| Expander | `.streamlit-expanderHeader` | Collapsible section header |
| Divider | `.stDivider` | Horizontal rule |

**Confidence: MEDIUM.** Selector names are correct for Streamlit ~1.30–1.45 based on training data. Streamlit 1.50 may have renamed some `data-testid` values. Always verify with browser inspect before committing CSS.

---

## Sources

**Confidence assessment:**
- KPI card patterns, chart dark theming, typography conventions: HIGH confidence — widely documented in fintech design writing, visible in production applications (Robinhood, Wealthfront, Stripe Dashboard), stable patterns since 2020
- Bloomberg Terminal visual conventions: HIGH confidence — publicly documented, widely analyzed
- Streamlit CSS selector names: MEDIUM confidence — based on training data through August 2025; selector stability varies between Streamlit releases; verify against live DOM
- Specific Streamlit 1.50 `data-testid` values: LOW confidence — Streamlit changes these periodically without major version bumps; must be verified against the running app
- Dark/light mode toggle implementation: MEDIUM confidence — session state approach is standard; CSS variable swap is the correct pattern but requires testing against Streamlit's own color mode system

**Primary references used (from training knowledge):**
- Bloomberg Terminal UI conventions (publicly analyzed)
- Robinhood web app (publicly available, analyzed through training cutoff)
- Wealthfront and Betterment dashboard conventions (publicly available)
- Stripe Dashboard design system (publicly documented)
- Streamlit custom CSS injection patterns (Streamlit documentation, community examples through August 2025)
- Plotly dark theme configuration (Plotly documentation through August 2025)
- Google Material Design and Apple Human Interface Guidelines: data density and typographic hierarchy sections
