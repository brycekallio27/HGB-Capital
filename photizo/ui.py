"""
photizo.ui — UI helpers, CSS constants, and HTML component generators.

All CSS strings and Plotly layout dicts live here so app.py stays clean.
The HTML generator functions (kpi_card, alloc_breakdown) are pure Python
and do not call Streamlit, making them testable in isolation.
"""
from __future__ import annotations

import streamlit as st


# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------

BRAND_COLORS = [
    "#C5A059", "#7C9BB5", "#5C8A6E", "#B57C7C",
    "#9B7CB5", "#B5A57C", "#7CB5B0", "#A07C9B",
]

PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#F5F5F5", family="Inter, sans-serif", size=12),
    legend=dict(font=dict(color="#AAAAAA", size=11), bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=0, b=0, l=0, r=0),
    height=300,
)


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------

DARK_CSS = """
<style>
/* Global app background */
.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #0A0A0A !important;
    color: #F5F5F5;
}

/* Sidebar surface */
[data-testid="stSidebar"] {
    background-color: #111111 !important;
}

/* Metric values — tabular numerals + gold accent */
[data-testid="stMetricValue"] {
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
    color: #F5F5F5;
}

/* Metric delta — tabular numerals */
[data-testid="stMetricDelta"] {
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
}

/* DataFrames outer wrapper — tabular numerals (may not penetrate canvas; see Phase 3) */
[data-testid="stDataFrame"] {
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
}

/* Semantic P&L colors — DSYS-05 */
.pl-positive { color: #16A34A !important; }
.pl-negative { color: #DC2626 !important; }

/* Gold accent on interactive elements */
.stButton > button {
    border-color: #C5A059;
    color: #C5A059;
}

/* Semantic P&L delta colors — DSYS-05 */
[data-testid="stMetricDelta"][aria-label*="increased"],
[data-testid="stMetricDelta"] svg[class*="up"],
.stMetricDelta--up {
    color: #16A34A !important;
    fill: #16A34A !important;
}
[data-testid="stMetricDelta"][aria-label*="decreased"],
[data-testid="stMetricDelta"] svg[class*="down"],
.stMetricDelta--down {
    color: #DC2626 !important;
    fill: #DC2626 !important;
}
[data-testid="stMetricDelta"] > div {
    font-variant-numeric: lining-nums tabular-nums;
}

/* ── Phase 2: Global Widget Overrides (DSYS-03) ───────────────────────── */

/* Tabs — gold active underline, no default blue */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    border-bottom: 1px solid #2A2A2A;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #9E804B;
    background-color: transparent;
    padding: 0.5rem 1.25rem;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #C5A059 !important;
    border-bottom: 2px solid #C5A059 !important;
    background-color: transparent !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #C5A059;
    background-color: rgba(197, 160, 89, 0.06);
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #C5A059 !important;
}

/* Buttons — full brand treatment with hover/active states */
.stButton > button {
    background-color: transparent;
    border: 1px solid #C5A059;
    color: #C5A059;
    font-weight: 500;
    letter-spacing: 0.03em;
    transition: background-color 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
    background-color: rgba(197, 160, 89, 0.1) !important;
    border-color: #C5A059 !important;
    color: #C5A059 !important;
    box-shadow: 0 0 0 1px #C5A059;
}
.stButton > button:active {
    background-color: rgba(197, 160, 89, 0.2) !important;
}

/* Text inputs and text areas */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #1A1A1A !important;
    border-color: #2A2A2A !important;
    color: #F5F5F5 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #C5A059 !important;
    box-shadow: 0 0 0 1px rgba(197, 160, 89, 0.4) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background-color: #1A1A1A !important;
    border-color: #2A2A2A !important;
}

/* Expander */
[data-testid="stExpander"] details {
    border-color: #2A2A2A !important;
    background-color: #111111 !important;
}

/* Spinner — gold */
[data-testid="stSpinner"] svg {
    stroke: #C5A059 !important;
}

/* Dividers — subtle, not heavy */
hr {
    border-color: #1E1E1E !important;
    margin: 0.75rem 0 !important;
}

/* ── Phase 2: Visual Hierarchy (PLSH-01) ──────────────────────────────── */

/* Metric labels — uppercase muted secondary tier */
[data-testid="stMetricLabel"] {
    color: #9E804B !important;
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Captions — tertiary, clearly subordinate */
.stCaption, [data-testid="stCaption"] p {
    color: #555555 !important;
    font-size: 0.75rem !important;
}

/* Subheaders — gold, intentional */
[data-testid="stHeadingWithActionElements"] h3,
h3 {
    color: #C5A059;
    font-weight: 600;
    letter-spacing: 0.01em;
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

/* Sidebar surface */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
}

/* Metric values — tabular numerals */
[data-testid="stMetricValue"] {
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
    color: #1A1A1A;
}

/* Metric delta — tabular numerals */
[data-testid="stMetricDelta"] {
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
}

/* DataFrames outer wrapper — tabular numerals (may not penetrate canvas; see Phase 3) */
[data-testid="stDataFrame"] {
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
}

/* Semantic P&L colors — DSYS-05 */
.pl-positive { color: #16A34A !important; }
.pl-negative { color: #DC2626 !important; }

/* Gold accent on interactive elements */
.stButton > button {
    border-color: #C5A059;
    color: #C5A059;
}

/* Semantic P&L delta colors — DSYS-05 */
[data-testid="stMetricDelta"][aria-label*="increased"],
[data-testid="stMetricDelta"] svg[class*="up"],
.stMetricDelta--up {
    color: #16A34A !important;
    fill: #16A34A !important;
}
[data-testid="stMetricDelta"][aria-label*="decreased"],
[data-testid="stMetricDelta"] svg[class*="down"],
.stMetricDelta--down {
    color: #DC2626 !important;
    fill: #DC2626 !important;
}
[data-testid="stMetricDelta"] > div {
    font-variant-numeric: lining-nums tabular-nums;
}

/* ── Phase 2: Global Widget Overrides (DSYS-03) ───────────────────────── */

/* Tabs — gold active underline */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    border-bottom: 1px solid #E0E0E0;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #9E9E9E;
    background-color: transparent;
    padding: 0.5rem 1.25rem;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #C5A059 !important;
    border-bottom: 2px solid #C5A059 !important;
    background-color: transparent !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #C5A059;
    background-color: rgba(197, 160, 89, 0.06);
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #C5A059 !important;
}

/* Buttons */
.stButton > button {
    background-color: transparent;
    border: 1px solid #C5A059;
    color: #C5A059;
    font-weight: 500;
    letter-spacing: 0.03em;
    transition: background-color 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
    background-color: rgba(197, 160, 89, 0.08) !important;
    border-color: #C5A059 !important;
    color: #C5A059 !important;
    box-shadow: 0 0 0 1px #C5A059;
}
.stButton > button:active {
    background-color: rgba(197, 160, 89, 0.15) !important;
}

/* Text inputs and text areas */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #FFFFFF !important;
    border-color: #D0D0D0 !important;
    color: #1A1A1A !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #C5A059 !important;
    box-shadow: 0 0 0 1px rgba(197, 160, 89, 0.4) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background-color: #FFFFFF !important;
    border-color: #D0D0D0 !important;
}

/* Expander */
[data-testid="stExpander"] details {
    border-color: #E0E0E0 !important;
    background-color: #FFFFFF !important;
}

/* Spinner — gold */
[data-testid="stSpinner"] svg {
    stroke: #C5A059 !important;
}

/* Dividers — subtle */
hr {
    border-color: #E8E8E8 !important;
    margin: 0.75rem 0 !important;
}

/* ── Phase 2: Visual Hierarchy (PLSH-01) ──────────────────────────────── */

/* Metric labels */
[data-testid="stMetricLabel"] {
    color: #9E804B !important;
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Captions */
.stCaption, [data-testid="stCaption"] p {
    color: #888888 !important;
    font-size: 0.75rem !important;
}

/* Subheaders — muted gold on light */
[data-testid="stHeadingWithActionElements"] h3,
h3 {
    color: #9E804B;
    font-weight: 600;
    letter-spacing: 0.01em;
}
</style>
"""


def inject_css(is_dark: bool) -> None:
    """Inject the appropriate CSS block based on current theme mode."""
    st.markdown(DARK_CSS if is_dark else LIGHT_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# HTML component generators — pure Python, no Streamlit, testable
# ---------------------------------------------------------------------------

def kpi_card(
    label: str,
    value: str,
    delta: str | None = None,
    delta_positive: bool = True,
    value_color: str = "#F5F5F5",
) -> str:
    """Return an HTML string for a branded KPI card."""
    delta_color = "#16A34A" if delta_positive else "#DC2626"
    delta_arrow = "▲" if delta_positive else "▼"
    delta_html = (
        f'<div style="color:{delta_color};font-size:12px;margin-top:6px;'
        f'font-variant-numeric:lining-nums tabular-nums;">{delta_arrow} {delta}</div>'
    ) if delta else '<div style="height:18px;margin-top:6px;"></div>'
    return f"""
<div style="background:#111111;border-left:3px solid #C5A059;border-radius:6px;
            padding:16px 20px;height:100%;box-sizing:border-box;">
  <div style="color:#9E804B;font-size:11px;letter-spacing:0.08em;
              text-transform:uppercase;margin-bottom:8px;font-weight:500;">{label}</div>
  <div style="color:{value_color};font-size:26px;font-weight:600;
              font-variant-numeric:lining-nums tabular-nums;line-height:1.1;">{value}</div>
  {delta_html}
</div>"""


def alloc_breakdown(weights_dict: dict) -> str:
    """Return HTML for a styled per-ticker allocation breakdown."""
    rows = ""
    for ticker, w in sorted(weights_dict.items(), key=lambda x: -x[1]):
        pct = w * 100
        bar_w = max(pct, 2)
        rows += f"""
<div style="display:flex;align-items:center;gap:12px;padding:8px 0;
            border-bottom:1px solid #1E1E1E;">
  <div style="width:52px;color:#F5F5F5;font-weight:600;font-size:13px;
              flex-shrink:0;">{ticker}</div>
  <div style="flex:1;background:#1E1E1E;border-radius:3px;height:6px;overflow:hidden;">
    <div style="width:{bar_w:.1f}%;background:#C5A059;height:100%;border-radius:3px;"></div>
  </div>
  <div style="width:44px;text-align:right;color:#C5A059;font-size:13px;
              font-variant-numeric:lining-nums tabular-nums;flex-shrink:0;">{pct:.1f}%</div>
</div>"""
    return f"""
<div style="background:#111111;border:1px solid #2A2A2A;border-radius:6px;padding:12px 16px;">
  <div style="color:#9E804B;font-size:10px;letter-spacing:0.12em;
              text-transform:uppercase;margin-bottom:8px;">Allocation Breakdown</div>
  {rows}
</div>"""
