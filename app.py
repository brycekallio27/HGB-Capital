import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
from datetime import datetime, timezone
from pypfopt import EfficientFrontier, risk_models, expected_returns

# --- PAGE SETUP ---
st.set_page_config(page_title="Project Photizo", layout="wide")

# --- DESIGN SYSTEM: CSS Constants & Injection ---

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


# Initialize theme session state (dark is brand default)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Inject CSS immediately — must happen before any UI element renders
inject_css(st.session_state.dark_mode)

st.title("Project Photizo | Investment Engine")

# --- 1. CONNECT TO DATABASE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"❌ Connection Failed. Check secrets.toml: {e}")
    st.stop()

# --- 2. SIDEBAR ---

def _toggle_theme() -> None:
    """Callback: flip dark_mode in session_state before rerun."""
    st.session_state.dark_mode = not st.session_state.dark_mode

_theme_icon = "🌙" if st.session_state.dark_mode else "☀️"
st.sidebar.button(
    _theme_icon,
    on_click=_toggle_theme,
    help="Toggle dark/light mode",
    key="theme_toggle",
)

st.sidebar.header("Operations")
user = st.sidebar.selectbox("Partner Login", ["Bryce K.", "Hunter S.", "Grayson W."])
st.sidebar.success(f"Active Session: {user}")

# --- 3. THE BRAIN: FINANCIAL MODELS & DATA ---

@st.cache_data(ttl=300)
def get_portfolio_performance(df):
    """Calculates Market Value, P&L, Allocation, and Sector"""
    df = df.copy()
    if df.empty: return None, 0, 0

    tickers = df['Ticker'].tolist()
    if not tickers: return None, 0, 0

    # Cash / money-market positions are priced at $1.00 — never pass to yfinance
    CASH_TICKERS = {"CASH", "MMKT", "SPAXX", "FDRXX", "FDIC", "FCASH", "CORE"}
    cash_mask = df['Ticker'].str.upper().isin(CASH_TICKERS)
    equity_tickers = df[~cash_mask]['Ticker'].tolist()

    # Stamp cash rows immediately — price is always $1.00, no P&L
    df.loc[cash_mask, 'Current Price'] = 1.00
    df.loc[cash_mask, 'Sector'] = 'Cash'

    # Fetch prices + sector only for equity positions
    if equity_tickers:
        try:
            close_data = yf.download(equity_tickers, period="1d", progress=False)['Close']
            ticker_objects = {t: yf.Ticker(t) for t in equity_tickers}
        except Exception as e:
            return df, 0, 0

        if close_data.empty:
            return df, 0, 0

        # Normalize: yfinance 1.1+ always returns a DataFrame with tickers as columns
        # but guard against a Series being returned in edge cases
        if isinstance(close_data, pd.Series):
            close_data = close_data.to_frame(name=equity_tickers[0])

        current_prices = close_data.iloc[-1]
        df.loc[~cash_mask, 'Current Price'] = df.loc[~cash_mask, 'Ticker'].map(current_prices)
        df.loc[~cash_mask, 'Sector'] = df.loc[~cash_mask, 'Ticker'].apply(
            lambda t: ticker_objects[t].info.get('sector', 'Unknown') if t in ticker_objects else 'Unknown'
        )

    # Metrics
    df['Market Value'] = df['Shares'] * df['Current Price']
    if 'Cost' not in df.columns: df['Cost'] = 0
    df['Total Cost'] = df['Shares'] * df['Cost']
    df['Unrealized Gain ($)'] = df['Market Value'] - df['Total Cost']
    df['Return (%)'] = df.apply(lambda x: ((x['Market Value'] - x['Total Cost']) / x['Total Cost'] * 100) if x['Total Cost'] > 0 else 0, axis=1)

    total_equity = df['Market Value'].fillna(0).sum()
    total_pl = df['Unrealized Gain ($)'].fillna(0).sum()

    return df, total_equity, total_pl

@st.cache_data(ttl=300)
def get_financial_data(ticker):
    """Fetches data for DCF + History Charts + News"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        cashflow = stock.cashflow
        
        if cashflow.empty: return None
        try:
            fcf = cashflow.loc['Free Cash Flow'].iloc[0]
        except KeyError:
            try:
                ocf = cashflow.loc['Operating Cash Flow'].iloc[0]
                capex = cashflow.loc['Capital Expenditure'].iloc[0]
                fcf = ocf + capex
            except KeyError:
                fcf = 0
        
        analyst_growth = info.get('earningsGrowth', 0.10)
        if analyst_growth is None: analyst_growth = 0.08
        if analyst_growth > 0.20: analyst_growth = 0.20 
        if analyst_growth < 0: analyst_growth = 0.02 
        
        # History for charts
        fin = stock.financials
        history = pd.DataFrame()
        if not fin.empty:
            transposed = fin.T.sort_index(ascending=True)
            if 'Total Revenue' in transposed.columns and 'Net Income' in transposed.columns:
                history['Revenue ($B)'] = transposed['Total Revenue'] / 1e9
                history['Net Income ($B)'] = transposed['Net Income'] / 1e9
                history.index = history.index.strftime('%Y')

        news = []
        try:
            news = stock.news[:3]
        except Exception:
            pass

        return {
            "Price": info.get('currentPrice', 0),
            "Shares": info.get('sharesOutstanding', 0),
            "Beta": info.get('beta', 1.0),
            "FCF": fcf,
            "Analyst_Growth": analyst_growth,
            "Name": info.get('shortName', ticker),
            "History": history,
            "News": news
        }
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def scan_market_opportunities():
    watchlist_titans = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM", "V", "JNJ", "PFE", "KO", "PEP", "XOM", "CVX"]
    opportunities = []
    for ticker in watchlist_titans:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            current = info.get('currentPrice', 0)
            high_52 = info.get('fiftyTwoWeekHigh', 0)
            pe = info.get('trailingPE', 999) 
            if current > 0 and high_52 > 0:
                discount = ((high_52 - current) / high_52) * 100
                if discount > 10 or (pe < 25 and pe > 0):
                    opportunities.append({"Ticker": ticker, "Price": f"${current}", "Discount": f"-{discount:.1f}%", "P/E": f"{pe:.1f}", "Sector": info.get('sector', 'N/A')})
        except Exception:
            continue
    return pd.DataFrame(opportunities)

def calculate_dcf(fcf, shares, growth, discount, terminal_growth=0.03):
    if shares == 0 or fcf == 0: return 0
    future_cash_flows = [fcf * ((1 + growth) ** i) / ((1 + discount) ** i) for i in range(1, 6)]
    terminal_val = (fcf * ((1 + growth) ** 5) * (1 + terminal_growth)) / (discount - terminal_growth)
    return round((sum(future_cash_flows) + (terminal_val / ((1 + discount) ** 5))) / shares, 2)

def optimize_portfolio(tickers, strategy, target_return=None):
    """Compute optimal portfolio allocation using pypfopt."""
    prices = yf.download(tickers, period="1y", progress=False)['Close']
    if prices.empty:
        return None, None
    mu = expected_returns.mean_historical_return(prices)
    S = risk_models.sample_cov(prices)
    ef = EfficientFrontier(mu, S)
    if strategy == "Max Sharpe":
        ef.max_sharpe()
    elif strategy == "Min Volatility":
        ef.min_volatility()
    elif strategy == "Target Return":
        ef.efficient_return(target_return)
    weights = ef.clean_weights()
    performance = ef.portfolio_performance()
    return weights, performance

# --- 3b. PORTFOLIO UI HELPERS ---

# Brand-consistent color palette for Plotly charts
BRAND_COLORS = [
    "#C5A059", "#7C9BB5", "#5C8A6E", "#B57C7C",
    "#9B7CB5", "#B5A57C", "#7CB5B0", "#A07C9B",
]

# Base Plotly layout applied to every chart
PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#F5F5F5", family="Inter, sans-serif", size=12),
    legend=dict(font=dict(color="#AAAAAA", size=11), bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=0, b=0, l=0, r=0),
    height=300,
)

def _kpi_card(label: str, value: str, delta: str = None, delta_positive: bool = True) -> str:
    """Return an HTML string for a branded KPI card (PORT-01)."""
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
  <div style="color:#F5F5F5;font-size:26px;font-weight:600;
              font-variant-numeric:lining-nums tabular-nums;line-height:1.1;">{value}</div>
  {delta_html}
</div>"""

# --- 4. TABS INTERFACE ---
tab_portfolio, tab_analysis, tab_optimizer = st.tabs(["📊 Portfolio War Room", "🔬 Analysis Lab", "⚙️ Portfolio Optimizer"])

# --- TAB 1: PORTFOLIO ---
with tab_portfolio:
    st.subheader("HGB Capital | Live Holdings")
    try:
        raw_df = conn.read(worksheet="Portfolio", ttl=5)
        if raw_df is not None and not raw_df.empty:
            df_rich, total_equity, total_pl = get_portfolio_performance(raw_df)
            
            # PORT-01: Branded KPI cards
            pl_pct = f"{(total_pl / total_equity) * 100:.2f}%" if pd.notna(total_equity) and total_equity > 0 else "0%"
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(_kpi_card("Total Equity", f"${total_equity:,.2f}"), unsafe_allow_html=True)
            with c2:
                st.markdown(_kpi_card("Unrealized P&L", f"${total_pl:,.2f}", delta=pl_pct, delta_positive=total_pl >= 0), unsafe_allow_html=True)
            with c3:
                st.markdown(_kpi_card("Active Positions", str(len(df_rich))), unsafe_allow_html=True)
            st.caption("Prices reflect previous close via yfinance · Add a CASH row (Shares = dollar balance) to include money market in total")
            st.divider()

            # PORT-02: Brand-themed Plotly charts
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.write("**Holdings (By Size)**")
                fig1 = px.pie(df_rich, values='Market Value', names='Ticker', hole=0.4,
                              color_discrete_sequence=BRAND_COLORS)
                fig1.update_layout(**PLOTLY_DARK_LAYOUT)
                fig1.update_traces(textfont_color="#F5F5F5")
                st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
            with col_chart2:
                st.write("**Risk Breakdown (By Sector)**")
                fig2 = px.pie(df_rich, values='Market Value', names='Sector', hole=0.4,
                              color_discrete_sequence=BRAND_COLORS)
                fig2.update_layout(**PLOTLY_DARK_LAYOUT)
                fig2.update_traces(textfont_color="#F5F5F5")
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            # PORT-03: Dark-themed holdings dataframe
            st.write("**Detailed View**")
            cols = ['Ticker', 'Sector', 'Shares', 'Cost', 'Current Price', 'Market Value', 'Return (%)']
            styled_df = (
                df_rich[cols].style
                .format({"Cost": "${:.2f}", "Current Price": "${:.2f}", "Market Value": "${:,.2f}", "Return (%)": "{:.1f}%"})
                .set_properties(**{"background-color": "#111111", "color": "#F5F5F5", "border-color": "#2A2A2A"})
                .set_table_styles([
                    {"selector": "th", "props": [
                        ("background-color", "#0A0A0A"), ("color", "#9E804B"),
                        ("font-size", "11px"), ("text-transform", "uppercase"),
                        ("letter-spacing", "0.06em"), ("border-color", "#2A2A2A"),
                    ]},
                    {"selector": "tr:nth-child(even) td", "props": [("background-color", "#161616")]},
                ])
            )
            st.dataframe(styled_df, use_container_width=True)

            # Watchlist
            st.divider()
            st.subheader("🎯 Watchlist Targets")
            try:
                df_watch = conn.read(worksheet="Watchlist", ttl=5)
                if not df_watch.empty: st.dataframe(df_watch.sort_index(ascending=False), use_container_width=True, hide_index=True)
            except Exception as e:
                st.caption(f"Watchlist unavailable: {e}")
        else: st.info("Portfolio is empty. Add positions to Google Sheets.")
    except Exception as e: st.warning(f"Sync Error: {e}")
    
    if st.button("Refresh Portfolio"): st.cache_data.clear(); st.rerun()

# --- TAB 2: ANALYSIS LAB ---
with tab_analysis:
    with st.expander("📡 Market Radar (Scan for Opportunities)", expanded=False):
        if st.button("Scan Market"):
            with st.spinner("Scanning Titans..."):
                opps = scan_market_opportunities()
                if not opps.empty: st.dataframe(opps, use_container_width=True)
                else: st.info("No obvious discounts found.")

    st.subheader("Deep Dive Analysis")
    col_input, col_assumptions = st.columns([1, 2])
    with col_input: ticker_input = st.text_input("Enter Ticker (e.g. NVDA)").upper()
    
    if ticker_input:
        data = get_financial_data(ticker_input)
        if data:
            # 1. VALUATION
            smart_discount = max(0.06, min(0.042 + (data['Beta'] * 0.055), 0.15))
            with col_assumptions:
                growth = st.slider(f"Growth (Analyst: {data['Analyst_Growth']:.1%})", 0.0, 0.30, float(data['Analyst_Growth']), 0.01)
                discount = st.slider(f"Discount (Beta: {data['Beta']})", 0.05, 0.20, float(smart_discount), 0.01)
            
            intrinsic_value = calculate_dcf(data['FCF'], data['Shares'], growth, discount)
            upside = ((intrinsic_value - data['Price']) / data['Price']) * 100
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Market Price", f"${data['Price']}")
            m2.metric("Fair Value", f"${intrinsic_value}", delta=f"{upside:.1f}%")
            m3.metric("Free Cash Flow", f"${data['FCF']/1e9:.2f} B")
            
            # 2. CHARTS & NEWS
            tab_financials, tab_news = st.tabs(["📈 Financials", "📰 News Feed"])
            
            with tab_financials:
                if not data['History'].empty:
                    years = st.slider("Select time scope (years)", min_value=1, max_value=4, value=4, step=1)
                    history_filtered = data['History'].tail(years)
                    st.write(f"**Performance Trend ({years}yr)**")
                    st.bar_chart(history_filtered, color=["#2E86C1", "#28B463"])
                else:
                    st.caption("No historical data available.")
                    
            with tab_news:
                st.write(f"**Latest News for {data['Name']}**")
                if data['News']:
                    for news_item in data['News']:
                        content = news_item.get('content', {})
                        title = content.get('title')
                        if not title: continue
                        link = content.get('canonicalUrl', {}).get('url', '#')
                        publisher = content.get('provider', {}).get('displayName', 'Unknown')
                        pub_date_str = content.get('pubDate', '')
                        try:
                            pub_dt = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                            pub_formatted = pub_dt.astimezone().strftime('%Y-%m-%d %H:%M')
                        except Exception:
                            pub_formatted = pub_date_str
                        st.markdown(f"**[{title}]({link})**")
                        st.caption(f"Source: {publisher} | {pub_formatted}")
                        st.divider()
                else:
                    st.caption("No recent news available.")

            # 3. ACTION
            notes = st.text_area("Investment Thesis", height=100)
            if st.button(f"Add {ticker_input} to Watchlist"):
                new_row = pd.DataFrame([{"Ticker": ticker_input, "Price_At_Add": data['Price'], "Added_By": user, "Notes": notes, "Status": "Watching"}])
                try:
                    curr = conn.read(worksheet="Watchlist")
                    conn.update(worksheet="Watchlist", data=pd.concat([curr, new_row], ignore_index=True))
                    st.success("Synced!")
                except Exception as e:
                    st.error(f"Error syncing to Sheets: {e}")

# --- TAB 3: PORTFOLIO OPTIMIZER ---
with tab_optimizer:
    st.subheader("Portfolio Optimizer")
    st.caption("Compute optimal allocations using Mean-Variance Optimization (pypfopt)")

    # Pre-populate tickers from Portfolio sheet if available
    default_tickers = ""
    try:
        portfolio_df = conn.read(worksheet="Portfolio", ttl=5)
        if portfolio_df is not None and not portfolio_df.empty and 'Ticker' in portfolio_df.columns:
            default_tickers = "\n".join(portfolio_df['Ticker'].dropna().unique().tolist())
    except Exception:
        pass

    opt_col1, opt_col2 = st.columns([1, 2])
    with opt_col1:
        tickers_text = st.text_area("Tickers (one per line)", value=default_tickers, height=200)
        strategy = st.radio("Strategy", ["Max Sharpe", "Min Volatility", "Target Return"])
        target_ret = None
        if strategy == "Target Return":
            target_ret = st.slider("Target Annual Return", 0.0, 0.50, 0.10, 0.01, format="%.0f%%")
        run_opt = st.button("Optimize")

    with opt_col2:
        if run_opt:
            ticker_list = [t.strip().upper() for t in tickers_text.strip().splitlines() if t.strip()]
            if len(ticker_list) < 2:
                st.warning("Enter at least 2 tickers.")
            else:
                with st.spinner("Optimizing..."):
                    try:
                        weights, perf = optimize_portfolio(ticker_list, strategy, target_ret)
                        if weights is None:
                            st.error("Could not download price data for the given tickers.")
                        else:
                            exp_ret, vol, sharpe = perf
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Expected Return", f"{exp_ret:.2%}")
                            m2.metric("Volatility", f"{vol:.2%}")
                            m3.metric("Sharpe Ratio", f"{sharpe:.2f}")

                            # Filter to non-zero weights
                            alloc = {k: v for k, v in weights.items() if v > 0}
                            alloc_df = pd.DataFrame({"Ticker": list(alloc.keys()), "Weight": list(alloc.values())})
                            alloc_df = alloc_df.sort_values("Weight", ascending=True)

                            fig = px.bar(alloc_df, x="Weight", y="Ticker", orientation="h",
                                         text=alloc_df["Weight"].apply(lambda w: f"{w:.1%}"))
                            fig.update_layout(xaxis_tickformat=".0%", margin=dict(t=10, b=10), height=max(300, len(alloc_df) * 35))
                            st.plotly_chart(fig, use_container_width=True)

                            st.dataframe(
                                alloc_df.sort_values("Weight", ascending=False).style.format({"Weight": "{:.2%}"}),
                                use_container_width=True, hide_index=True
                            )
                    except Exception as e:
                        st.error(f"Optimization failed: {e}")