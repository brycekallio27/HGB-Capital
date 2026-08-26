from __future__ import annotations
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from pypfopt import EfficientFrontier, expected_returns, risk_models

# photizo modules — financial logic, CSS, and UI helpers live here
from photizo.allocation import (
    PROFILES,
    SLEEVE_UNIVERSE,
    optimize_allocation,
    rebalance_recommendation,
    universe_tickers,
)
from photizo.models import (
    get_portfolio_performance,
    get_financial_data,
    scan_market_opportunities,
    calculate_dcf,
    optimize_portfolio,
    smart_discount_rate,
)
from photizo.radar import (
    RADAR_THEMES,
    build_radar_universe,
    parse_ticker_list,
    scan_radar_candidates,
)
from photizo.ui import (
    BRAND_COLORS,
    PLOTLY_DARK_LAYOUT,
    inject_css,
    kpi_card as _kpi_card,
    alloc_breakdown as _alloc_breakdown,
)
from photizo.sentiment import score_news_items
from photizo.watchlist import (
    WATCHLIST_COLUMNS,
    add_row,
    annotate_for_display,
    claim_legacy_rows,
    delete_row,
    is_legacy_owner,
    normalize_watchlist,
    summary_counts,
    update_row,
)

def _verify_clerk_token(token: str) -> dict | None:
    """Verify a Clerk session JWT and return claims on success."""
    if not token:
        return None
    try:
        from jwt import PyJWKClient, decode as jwt_decode

        clerk_cfg = st.secrets.get("clerk", {})
        jwks_url = clerk_cfg.get("jwks_url", "")
        issuer = clerk_cfg.get("issuer", None)
        if not jwks_url:
            return None

        signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key
        options = {"verify_aud": False}
        kwargs = {"algorithms": ["RS256"], "options": options}
        if issuer:
            kwargs["issuer"] = issuer
        else:
            options["verify_iss"] = False
        return jwt_decode(token, signing_key, **kwargs)
    except Exception:
        return None


def _partner_session_from_claims(claims: dict) -> dict | None:
    """Map verified Clerk claims to an HGB partner session."""
    email = str(
        claims.get("email")
        or claims.get("email_address")
        or claims.get("primary_email_address")
        or ""
    ).strip().lower()
    if not email:
        return None

    partners: dict = dict(st.secrets.get("partners", {}))
    for key, partner in partners.items():
        partner_email = str(partner.get("email", "")).strip().lower()
        if partner_email == email:
            return {
                "key": str(key).lower(),
                "name": partner.get("name", key),
                "email": email,
            }
    return None

# ---------------------------------------------------------------------------
# Ticker Input Validation
# ---------------------------------------------------------------------------
def validate_ticker(ticker: str) -> str:
    """Validate and sanitize ticker input.
    Strips whitespace, uppercases, and checks against allowed format (1-5 uppercase letters).
    Raises st.error() and st.stop() on invalid input.
    """
    ticker = ticker.strip().upper()
    if not re.match(r'^[A-Z]{1,5}$', ticker):
        st.error("Invalid ticker. Enter 1-5 uppercase letters (e.g., AAPL, MSFT).")
        st.stop()
    return ticker

# --- PAGE SETUP ---
st.set_page_config(page_title="Project Photizo", layout="wide")


# Initialize theme session state (dark is brand default)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Inject CSS immediately — must happen before any UI element renders
inject_css(st.session_state.dark_mode)

# ---------------------------------------------------------------------------
# AUTH GATE — must run before any dashboard content renders
# ---------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.clerk_user = {"key": "", "name": "", "email": ""}

_clerk_token = st.query_params.get("clerk_token")
if _clerk_token and not st.session_state.authenticated:
    _claims = _verify_clerk_token(_clerk_token)
    _partner_session = _partner_session_from_claims(_claims or {})
    if _partner_session:
        st.session_state.authenticated = True
        st.session_state.clerk_user = _partner_session
        st.query_params.clear()
        st.rerun()
    else:
        st.query_params.clear()
        st.error("Clerk sign-in succeeded, but this email is not configured as an HGB partner.")
        st.stop()

if not st.session_state.authenticated:
    _landing_url = st.secrets.get("clerk", {}).get("landing_url", "http://localhost:3000")
    # --- Centered HGB header ---
    st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;
            padding:60px 0 32px 0;text-align:center;">
  <div style="color:#C5A059;font-size:42px;font-weight:700;
              letter-spacing:0.1em;line-height:1;">HGB</div>
  <div style="color:#9E804B;font-size:11px;letter-spacing:0.2em;
              text-transform:uppercase;margin-top:4px;">Capital Management</div>
  <div style="color:#9E804B;font-size:13px;letter-spacing:0.04em;
              margin-top:12px;">Partner Portal · Private Access</div>
</div>
""", unsafe_allow_html=True)
    st.markdown(
        f"""
<div style="text-align:center;margin:-10px 0 24px 0;">
  <a href="{_landing_url}"
     style="display:inline-block;padding:11px 28px;background:#C5A059;color:#0A0A0A;
            font-weight:600;font-size:13px;letter-spacing:0.04em;border-radius:6px;
            text-decoration:none;">
    Sign In With Clerk →
  </a>
</div>
""",
        unsafe_allow_html=True,
    )

    # --- Detective animation strip ---
    st.html("""
<style>
@keyframes hgb-det-walk {
  0%   { transform: translateX(-200px); }
  100% { transform: translateX(calc(100vw + 200px)); }
}
@keyframes hgb-leg-l {
  0%, 100% { transform: rotate(-26deg); }
  50%       { transform: rotate(26deg); }
}
@keyframes hgb-leg-r {
  0%, 100% { transform: rotate(26deg); }
  50%       { transform: rotate(-26deg); }
}
@keyframes hgb-arm-l {
  0%, 100% { transform: rotate(14deg); }
  50%       { transform: rotate(-14deg); }
}
@keyframes hgb-sym-float {
  0%, 100% { transform: translateY(0px); opacity: 0.65; }
  50%       { transform: translateY(-11px); opacity: 0.95; }
}
@keyframes hgb-sym-glow {
  0%, 100% { filter: drop-shadow(0 0 4px rgba(197,160,89,0.4)); }
  50%       { filter: drop-shadow(0 0 14px rgba(197,160,89,0.85)) drop-shadow(0 0 30px rgba(197,160,89,0.3)); }
}
@keyframes hgb-mag-sway {
  0%, 100% { transform: rotate(-6deg); }
  50%       { transform: rotate(8deg); }
}
@keyframes hgb-candle-glow {
  0%, 100% { opacity: 0.6; }
  50%       { opacity: 1; }
}
.hgb-detective-wrap {
  position: absolute;
  bottom: 0px;
  left: 0;
  animation: hgb-det-walk 15s linear infinite;
}
.hgb-leg-l {
  transform-box: fill-box;
  transform-origin: top center;
  animation: hgb-leg-l 0.6s ease-in-out infinite;
}
.hgb-leg-r {
  transform-box: fill-box;
  transform-origin: top center;
  animation: hgb-leg-r 0.6s ease-in-out 0.3s infinite;
}
.hgb-arm-l {
  transform-box: fill-box;
  transform-origin: top center;
  animation: hgb-arm-l 0.6s ease-in-out 0.15s infinite;
}
.hgb-mag-group {
  transform-box: fill-box;
  transform-origin: 84px 48px;
  animation: hgb-mag-sway 2.8s ease-in-out infinite;
}
.hgb-symbol-wrap {
  position: absolute;
  animation: hgb-sym-float 3.2s ease-in-out infinite,
             hgb-sym-glow  3.2s ease-in-out infinite;
}
.hgb-candle-svg {
  position: absolute;
  animation: hgb-sym-float 3.2s ease-in-out 1.3s infinite,
             hgb-candle-glow 3.2s ease-in-out 1.3s infinite;
}
</style>

<div style="position:relative;width:100%;height:155px;overflow:hidden;
            margin-bottom:8px;margin-top:-8px;">

  <!-- Floating stock symbols -->
  <span class="hgb-symbol-wrap"
        style="left:11%;bottom:52px;font-size:32px;font-weight:700;
               color:#C5A059;font-family:Georgia,serif;
               animation-delay:0s,0s;">$</span>

  <span class="hgb-symbol-wrap"
        style="left:27%;bottom:68px;font-size:26px;font-weight:700;
               color:#C5A059;font-family:Georgia,serif;
               animation-delay:0.6s,0.6s;">↑</span>

  <!-- Candlestick chart symbol -->
  <svg class="hgb-candle-svg"
       style="left:44%;bottom:36px;width:48px;height:62px;"
       viewBox="0 0 48 62" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- Candle 1 (bullish, tall) -->
    <line x1="12" y1="3" x2="12" y2="11" stroke="#C5A059" stroke-width="2" stroke-linecap="round"/>
    <rect x="6" y="11" width="12" height="28" rx="1.5" fill="#C5A059"/>
    <line x1="12" y1="39" x2="12" y2="48" stroke="#C5A059" stroke-width="2" stroke-linecap="round"/>
    <!-- Candle 2 (bearish, hollow) -->
    <line x1="36" y1="5" x2="36" y2="13" stroke="#9E804B" stroke-width="2" stroke-linecap="round"/>
    <rect x="30" y="13" width="12" height="22" rx="1.5" fill="none" stroke="#9E804B" stroke-width="1.8"/>
    <line x1="36" y1="35" x2="36" y2="44" stroke="#9E804B" stroke-width="2" stroke-linecap="round"/>
  </svg>

  <span class="hgb-symbol-wrap"
        style="left:61%;bottom:58px;font-size:28px;font-weight:700;
               color:#C5A059;font-family:Georgia,serif;
               animation-delay:1.9s,1.9s;">%</span>

  <span class="hgb-symbol-wrap"
        style="left:78%;bottom:46px;font-size:22px;font-weight:700;
               color:#9E804B;font-family:Georgia,serif;letter-spacing:-1px;
               animation-delay:2.7s,2.7s;">≈</span>

  <!-- Horizontal ground line -->
  <div style="position:absolute;bottom:1px;left:0;right:0;
              height:1px;background:linear-gradient(90deg,
              transparent 0%, rgba(197,160,89,0.18) 15%,
              rgba(197,160,89,0.18) 85%, transparent 100%);"></div>

  <!-- Detective SVG figure -->
  <svg class="hgb-detective-wrap"
       viewBox="0 0 130 158" width="94" height="120"
       fill="none" xmlns="http://www.w3.org/2000/svg">

    <!-- FEDORA HAT -->
    <ellipse cx="54" cy="18" rx="28" ry="8" fill="#9E804B"/>
    <path d="M 30 22 Q 30 1 54 1 Q 78 1 78 22 Z" fill="#9E804B"/>
    <rect x="30" y="18" width="48" height="4" rx="2" fill="#7A6238"/>
    <!-- Hat ribbon -->
    <rect x="30" y="17" width="48" height="2.5" rx="1.2" fill="#5C4B28"/>

    <!-- HEAD -->
    <circle cx="54" cy="38" r="15" fill="#C5A059"/>
    <!-- Profile ear -->
    <ellipse cx="67" cy="38" rx="3.5" ry="6" fill="#B08040"/>

    <!-- NECK -->
    <rect x="49" y="51" width="10" height="8" rx="3" fill="#C5A059"/>

    <!-- TRENCH COAT BODY -->
    <path d="M 26 56 L 16 116 L 40 116 L 54 88 L 68 116 L 92 116 L 82 56 Z"
          fill="#C5A059"/>
    <!-- Coat shading / lapels -->
    <path d="M 54 56 L 40 72 L 54 68 L 68 72 Z" fill="#B08040"/>
    <!-- Center button line -->
    <line x1="54" y1="70" x2="54" y2="116" stroke="#B08040" stroke-width="1.5"/>
    <!-- Belt -->
    <rect x="22" y="86" width="60" height="6" rx="3" fill="#B08040"/>
    <rect x="49" y="84" width="10" height="10" rx="2.5" fill="#9E804B"/>

    <!-- LEFT ARM (swings with walk) -->
    <g class="hgb-arm-l">
      <rect x="12" y="58" width="12" height="44" rx="5.5" fill="#C5A059"/>
      <circle cx="18" cy="104" r="6.5" fill="#C5A059"/>
    </g>

    <!-- RIGHT ARM + MAGNIFYING GLASS -->
    <g class="hgb-mag-group">
      <!-- Arm angled up-right toward glass -->
      <rect x="82" y="52" width="12" height="38" rx="5.5" fill="#C5A059"
            transform="rotate(-32 88 52)"/>
      <!-- Magnifying glass loop -->
      <circle cx="102" cy="34" r="18" fill="none"
              stroke="#C5A059" stroke-width="3.2"/>
      <!-- Lens tint -->
      <circle cx="102" cy="34" r="15" fill="rgba(197,160,89,0.08)"/>
      <!-- Lens glint -->
      <path d="M 92 24 Q 96 20 100 24"
            stroke="rgba(197,160,89,0.55)" stroke-width="1.8"
            fill="none" stroke-linecap="round"/>
      <!-- Handle -->
      <line x1="115" y1="47" x2="127" y2="61"
            stroke="#C5A059" stroke-width="4.5" stroke-linecap="round"/>
    </g>

    <!-- LEFT LEG -->
    <g class="hgb-leg-l">
      <rect x="30" y="114" width="15" height="42" rx="6.5" fill="#B08040"/>
      <ellipse cx="37" cy="156" rx="12" ry="5.5" fill="#7A5A18"/>
    </g>

    <!-- RIGHT LEG -->
    <g class="hgb-leg-r">
      <rect x="59" y="114" width="15" height="42" rx="6.5" fill="#B08040"/>
      <ellipse cx="67" cy="156" rx="12" ry="5.5" fill="#7A5A18"/>
    </g>

  </svg>

</div>
""")

    st.markdown(
        "<div style='text-align:center;color:#2A2A2A;font-size:11px;margin-top:32px;'>"
        "HGB Capital Management · Confidential</div>",
        unsafe_allow_html=True,
    )
    st.stop()

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

# SBAR-01: HGB Capital wordmark
st.sidebar.markdown("""
<div style="padding:12px 4px 20px 4px;border-bottom:1px solid #2A2A2A;margin-bottom:20px;">
  <div style="color:#C5A059;font-size:22px;font-weight:700;letter-spacing:0.06em;
              line-height:1.1;font-family:Inter,sans-serif;">HGB</div>
  <div style="color:#9E804B;font-size:10px;letter-spacing:0.18em;
              text-transform:uppercase;margin-top:3px;">Capital Management</div>
</div>
""", unsafe_allow_html=True)

# SBAR-02: Partner session identity — now pulled from Clerk JWT
partner_key = st.session_state.clerk_user.get("key", "")
user = st.session_state.clerk_user.get("name", "Partner")
user_email = st.session_state.clerk_user.get("email", "")
st.sidebar.markdown(f"""
<div style="background:#111111;border:1px solid #2A2A2A;border-left:3px solid #C5A059;
            border-radius:6px;padding:10px 14px;margin:6px 0 12px 0;">
  <div style="color:#9E804B;font-size:10px;letter-spacing:0.12em;
              text-transform:uppercase;margin-bottom:4px;">Active Session</div>
  <div style="color:#C5A059;font-size:15px;font-weight:600;
              font-family:Inter,sans-serif;">{user}</div>
  <div style="color:#3A3A3A;font-size:10px;margin-top:3px;
              overflow:hidden;text-overflow:ellipsis;">{user_email}</div>
</div>
""", unsafe_allow_html=True)

def _sign_out():
    st.session_state.authenticated = False
    st.session_state.clerk_user = {"key": "", "name": "", "email": ""}

st.sidebar.button("Sign Out", on_click=_sign_out, use_container_width=True)

st.sidebar.divider()

_theme_icon = "🌙" if st.session_state.dark_mode else "☀️"
st.sidebar.button(
    _theme_icon,
    on_click=_toggle_theme,
    help="Toggle dark/light mode",
    key="theme_toggle",
)

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

        # Parallelize ticker info fetches using ThreadPoolExecutor
        def _get_sector(ticker):
            try:
                return yf.Ticker(ticker).info.get('sector', 'Unknown')
            except Exception:
                return 'Unknown'

        with ThreadPoolExecutor(max_workers=5) as executor:
            sector_map = dict(zip(equity_tickers, executor.map(_get_sector, equity_tickers)))

        df.loc[~cash_mask, 'Sector'] = df.loc[~cash_mask, 'Ticker'].map(sector_map)

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
def get_portfolio_df():
    """Fetch Portfolio DataFrame from Google Sheets once and cache it."""
    try:
        return conn.read(worksheet="Portfolio", ttl=5)
    except Exception:
        return None


def get_watchlist_df() -> pd.DataFrame:
    """Read and normalize the shared Watchlist worksheet."""
    try:
        return normalize_watchlist(conn.read(worksheet="Watchlist", ttl=5))
    except Exception:
        return normalize_watchlist(None)


def update_watchlist_df(df: pd.DataFrame) -> None:
    """Persist the canonical Watchlist schema to Google Sheets."""
    conn.update(worksheet="Watchlist", data=normalize_watchlist(df)[WATCHLIST_COLUMNS])


def partner_name_lookup() -> dict:
    """Build partner_key -> display name from Streamlit secrets."""
    partners = st.secrets.get("partners", {})
    return {str(k).lower(): v.get("name", k) for k, v in partners.items()}


@st.cache_data(ttl=300)
def get_allocation_prices(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Download two years of prices for the allocation decision engine."""
    prices = yf.download(list(tickers), period="2y", progress=False)["Close"]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])
    return prices.dropna(axis=1, how="all").ffill().dropna()


def current_portfolio_weights(df_rich: pd.DataFrame | None) -> dict[str, float]:
    """Convert enriched holdings to ticker weights for rebalance comparison."""
    if df_rich is None or df_rich.empty or "Market Value" not in df_rich.columns:
        return {}
    total = float(df_rich["Market Value"].fillna(0).sum())
    if total <= 0:
        return {}
    return {
        str(row["Ticker"]).upper(): float(row["Market Value"]) / total
        for _, row in df_rich.iterrows()
        if float(row.get("Market Value", 0) or 0) > 0
    }


def allocation_news_summary(tickers: list[str], max_tickers: int = 8) -> pd.DataFrame:
    """Cross-reference allocation candidates with available headline sentiment."""
    rows = []
    for ticker in tickers[:max_tickers]:
        data = get_financial_data(ticker)
        news = data.get("News", []) if data else []
        sentiment = score_news_items(news)
        rows.append({
            "Ticker": ticker,
            "Sentiment": sentiment["label"].replace("_", " ").title(),
            "Score": sentiment["score"],
            "Items": sentiment["n_items"],
            "Risk Flags": ", ".join(sentiment["risks"]) if sentiment["risks"] else "",
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=300)
def run_filtered_market_radar(
    tickers: tuple[str, ...],
    min_discount_pct: float,
    max_pe: float | None,
    min_growth_pct: float | None,
    selected_sectors: tuple[str, ...],
    max_results: int,
) -> pd.DataFrame:
    """Cached wrapper for the thesis-driven radar scan."""
    return scan_radar_candidates(
        list(tickers),
        min_discount_pct=min_discount_pct,
        max_pe=max_pe,
        min_growth_pct=min_growth_pct,
        selected_sectors=list(selected_sectors),
        max_results=max_results,
    )

# ---------------------------------------------------------------------------
# News aggregation helpers — Google News RSS + SEC EDGAR filings
# ---------------------------------------------------------------------------

def _fetch_google_news_rss(ticker: str, max_items: int = 5) -> list[dict]:
    """Pull recent headlines from Google News RSS for a given ticker symbol."""
    url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        items: list[dict] = []
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title", "").strip()
            if not title:
                continue
            link = item.findtext("link", "#").strip()
            pub_date = item.findtext("pubDate", "").strip()
            source_el = item.find("source")
            source = source_el.text.strip() if source_el is not None and source_el.text else "Google News"
            items.append({
                "title": title,
                "link": link,
                "publisher": source,
                "pub_date": pub_date,
                "source_type": "google_news",
            })
        return items
    except Exception:
        return []


def _fetch_sec_filings(ticker: str, max_items: int = 3) -> list[dict]:
    """Pull recent SEC 8-K filings for a ticker via EDGAR Atom feed."""
    url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&CIK={ticker}&type=8-K"
        f"&dateb=&owner=include&count={max_items}&search_text=&output=atom"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "HGB Capital research@hgbcapital.com"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read()
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(raw)
        items: list[dict] = []
        for entry in root.findall("atom:entry", ns)[:max_items]:
            title = entry.findtext("atom:title", "", ns).strip()
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "#") if link_el is not None else "#"
            updated = entry.findtext("atom:updated", "", ns).strip()
            items.append({
                "title": f"📋 SEC 8-K: {title}",
                "link": link,
                "publisher": "SEC EDGAR",
                "pub_date": updated,
                "source_type": "sec_edgar",
            })
        return items
    except Exception:
        return []


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
        
        raw_analyst_growth = info.get('earningsGrowth', 0.10)
        if raw_analyst_growth is None: raw_analyst_growth = 0.08
        analyst_growth = raw_analyst_growth
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

        # yfinance news — normalized to a common dict schema
        yf_news: list[dict] = []
        try:
            for item in stock.news[:4]:
                content = item.get("content", {})
                title = content.get("title", "")
                if not title:
                    continue
                link = content.get("canonicalUrl", {}).get("url", "#")
                publisher = content.get("provider", {}).get("displayName", "Yahoo Finance")
                pub_date = content.get("pubDate", "")
                yf_news.append({
                    "title": title,
                    "link": link,
                    "publisher": publisher,
                    "pub_date": pub_date,
                    "source_type": "yfinance",
                })
        except Exception:
            pass

        # Aggregate from all sources: yfinance + Google News + SEC EDGAR
        google_news = _fetch_google_news_rss(ticker, max_items=4)
        sec_filings = _fetch_sec_filings(ticker, max_items=2)
        aggregated_news = yf_news + google_news + sec_filings

        return {
            "Price": info.get('currentPrice', 0),
            "Shares": info.get('sharesOutstanding', 0),
            "Beta": info.get('beta', 1.0),
            "FCF": fcf,
            "Analyst_Growth": analyst_growth,
            "Raw_Analyst_Growth": raw_analyst_growth,
            "Name": info.get('shortName', ticker),
            "History": history,
            "News": aggregated_news,
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

def _kpi_card(label: str, value: str, delta: str = None, delta_positive: bool = True, value_color: str = "#F5F5F5") -> str:
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
  <div style="color:{value_color};font-size:26px;font-weight:600;
              font-variant-numeric:lining-nums tabular-nums;line-height:1.1;">{value}</div>
  {delta_html}
</div>"""

def _alloc_breakdown(weights_dict: dict) -> str:
    """Return HTML for a styled per-ticker allocation breakdown (ANLS-03)."""
    rows = ""
    for ticker, w in sorted(weights_dict.items(), key=lambda x: -x[1]):
        pct = w * 100
        bar_w = max(pct, 2)  # minimum bar width so tiny allocations still show
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

# --- 4. PERSISTENT WORKSPACE NAVIGATION ---
workspace_options = [
    "Portfolio War Room",
    "Analysis Lab",
    "Allocation Dashboard",
]
if "active_workspace" not in st.session_state:
    st.session_state.active_workspace = workspace_options[0]

active_workspace = st.radio(
    "Workspace",
    workspace_options,
    horizontal=True,
    key="active_workspace",
    label_visibility="collapsed",
)

# --- TAB 1: PORTFOLIO ---
if active_workspace == "Portfolio War Room":
    st.subheader("HGB Capital | Live Holdings")
    try:
        raw_df = get_portfolio_df()
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
            st.subheader("Team Watchlist")
            try:
                df_watch = get_watchlist_df()
                names = partner_name_lookup()
                counts = summary_counts(df_watch, names.keys())
                if counts:
                    count_cols = st.columns(min(len(counts), 4))
                    for idx, (member_key, member_counts) in enumerate(counts.items()):
                        with count_cols[idx % len(count_cols)]:
                            st.markdown(
                                _kpi_card(
                                    names.get(member_key, member_key),
                                    f"{member_counts['owned']} saved",
                                    delta=f"{member_counts['starred']} starred",
                                ),
                                unsafe_allow_html=True,
                            )

                if df_watch.empty:
                    st.caption("No shared watchlist entries yet.")
                else:
                    display_df = annotate_for_display(df_watch, partner_key, names)
                    display_df.insert(0, "Row", display_df.index)
                    visible_cols = [
                        "Row", "★", "Ticker", "Owner", "You?", "Price_At_Add",
                        "Status", "Notes", "Added_At",
                    ]
                    st.dataframe(
                        display_df[visible_cols].sort_values("Row", ascending=False),
                        use_container_width=True,
                        hide_index=True,
                    )

                    legacy_rows = [
                        int(i)
                        for i, row in df_watch.iterrows()
                        if is_legacy_owner(row, names.keys())
                    ]
                    if legacy_rows:
                        st.warning(
                            f"{len(legacy_rows)} legacy test watchlist entr"
                            f"{'y' if len(legacy_rows) == 1 else 'ies'} need an owner."
                        )
                        claim_col, delete_col = st.columns(2)
                        with claim_col:
                            if st.button("Claim Legacy Entries", use_container_width=True):
                                updated, claimed = claim_legacy_rows(
                                    df_watch,
                                    row_indices=legacy_rows,
                                    partner_key=partner_key,
                                    valid_partner_keys=names.keys(),
                                )
                                update_watchlist_df(updated)
                                st.cache_data.clear()
                                st.success(f"Claimed {claimed} legacy entries.")
                                st.rerun()
                        with delete_col:
                            if st.button("Delete Legacy Entries", use_container_width=True):
                                updated = df_watch.drop(df_watch.index[legacy_rows]).reset_index(drop=True)
                                update_watchlist_df(updated)
                                st.cache_data.clear()
                                st.success(f"Deleted {len(legacy_rows)} legacy entries.")
                                st.rerun()

                    st.caption("Everyone can view and star ideas. Only the partner who added an idea can edit or delete it.")
                    row_options = display_df["Row"].tolist()
                    selected_row = st.selectbox(
                        "Manage watchlist row",
                        options=row_options,
                        format_func=lambda i: f"{display_df.loc[i, 'Ticker']} · {display_df.loc[i, 'Owner']}",
                    )
                    selected = df_watch.iloc[int(selected_row)]
                    c_star, c_status, c_notes, c_delete = st.columns([1, 1, 2, 1])
                    with c_star:
                        if st.button("Toggle Star", key=f"star_{selected_row}"):
                            updated, ok, msg = update_row(
                                df_watch,
                                row_index=int(selected_row),
                                partner_key=partner_key,
                                updates={"_star_toggle": True},
                            )
                            if ok:
                                update_watchlist_df(updated)
                                st.cache_data.clear()
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with c_status:
                        new_status = st.selectbox(
                            "Status",
                            ["Watching", "Researching", "Buy", "Sell", "Closed"],
                            index=["Watching", "Researching", "Buy", "Sell", "Closed"].index(
                                selected.get("Status", "Watching")
                                if selected.get("Status", "Watching") in ["Watching", "Researching", "Buy", "Sell", "Closed"]
                                else "Watching"
                            ),
                            disabled=str(selected.get("Added_By", "")).lower() != partner_key.lower(),
                            key=f"status_{selected_row}",
                        )
                    with c_notes:
                        new_notes = st.text_input(
                            "Notes",
                            value=str(selected.get("Notes", "") or ""),
                            disabled=str(selected.get("Added_By", "")).lower() != partner_key.lower(),
                            key=f"notes_{selected_row}",
                        )
                    with c_delete:
                        st.write("")
                        st.write("")
                        save_edit = st.button("Save", key=f"save_{selected_row}")
                        delete_edit = st.button("Delete", key=f"delete_{selected_row}")

                    if save_edit:
                        updated, ok, msg = update_row(
                            df_watch,
                            row_index=int(selected_row),
                            partner_key=partner_key,
                            updates={"Status": new_status, "Notes": new_notes},
                        )
                        if ok:
                            update_watchlist_df(updated)
                            st.cache_data.clear()
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    if delete_edit:
                        updated, ok, msg = delete_row(
                            df_watch,
                            row_index=int(selected_row),
                            partner_key=partner_key,
                        )
                        if ok:
                            update_watchlist_df(updated)
                            st.cache_data.clear()
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            except Exception as e:
                st.caption(f"Watchlist unavailable: {e}")
        else: st.info("Portfolio is empty. Add positions to Google Sheets.")
    except Exception as e: st.warning(f"Sync Error: {e}")
    
    if st.button("Refresh Portfolio"): st.cache_data.clear(); st.rerun()

# --- TAB 2: ANALYSIS LAB ---
if active_workspace == "Analysis Lab":
    if "market_radar_expanded" not in st.session_state:
        st.session_state.market_radar_expanded = False
    if "market_radar_results" not in st.session_state:
        st.session_state.market_radar_results = None

    with st.expander(
        "Market Radar (Filtered Opportunity Scan)",
        expanded=st.session_state.market_radar_expanded,
    ):
        st.caption("Start with a thesis, anchor company, or theme, then filter candidates before adding ideas to the team watchlist.")

        radar_left, radar_right = st.columns([1, 1])
        with radar_left:
            selected_theme_keys = st.multiselect(
                "Investment themes",
                options=list(RADAR_THEMES.keys()),
                default=["ai_compute"],
                format_func=lambda k: RADAR_THEMES[k].label,
                help="Theme baskets include related companies and ETFs. You can combine themes.",
            )
            anchor_ticker = st.text_input(
                "Anchor ticker",
                placeholder="NVDA, LLY, TSM...",
                help="Use a large-cap anchor to pull in related ecosystem names.",
            ).strip().upper()
            custom_ticker_text = st.text_area(
                "Custom tickers",
                placeholder="One per line or comma-separated",
                height=88,
            )

        with radar_right:
            sector_filter = st.multiselect(
                "Sector filter",
                [
                    "Technology",
                    "Healthcare",
                    "Industrials",
                    "Communication Services",
                    "Consumer Cyclical",
                    "Financial Services",
                    "Energy",
                    "ETF / Fund",
                ],
            )
            min_discount_pct = st.slider(
                "Minimum discount from 52-week high",
                0,
                50,
                0,
                5,
                format="%d%%",
            )
            max_pe_enabled = st.checkbox("Filter by max P/E", value=False)
            max_pe = st.slider("Maximum P/E", 5, 80, 35, 5) if max_pe_enabled else None
            min_growth_enabled = st.checkbox("Filter by minimum earnings growth", value=False)
            min_growth_pct = st.slider("Minimum earnings growth", -25, 60, 0, 5, format="%d%%") if min_growth_enabled else None
            max_results = st.slider("Max results", 5, 40, 20, 5)

        custom_tickers = parse_ticker_list(custom_ticker_text)
        invalid_custom = [t for t in custom_tickers if not re.match(r"^[A-Z]{1,5}$", t)]
        if invalid_custom:
            st.warning(f"Skipping unsupported ticker format: {', '.join(invalid_custom)}")
        custom_tickers = [t for t in custom_tickers if re.match(r"^[A-Z]{1,5}$", t)]
        if anchor_ticker and not re.match(r"^[A-Z]{1,5}$", anchor_ticker):
            st.warning("Anchor ticker must be 1-5 letters. Ignoring anchor for this scan.")
            anchor_ticker = ""

        radar_universe = build_radar_universe(
            theme_keys=selected_theme_keys,
            anchor_ticker=anchor_ticker,
            custom_tickers=custom_tickers,
        )
        st.caption(f"Candidate universe: {len(radar_universe)} ticker(s) · {', '.join(radar_universe[:18])}{'...' if len(radar_universe) > 18 else ''}")

        if st.button("Scan Filtered Market", use_container_width=True):
            with st.spinner("Scanning Titans..."):
                st.session_state.market_radar_results = run_filtered_market_radar(
                    tuple(radar_universe),
                    float(min_discount_pct),
                    float(max_pe) if max_pe is not None else None,
                    float(min_growth_pct) if min_growth_pct is not None else None,
                    tuple(sector_filter),
                    int(max_results),
                )
                st.session_state.market_radar_expanded = True
                st.rerun()

        opps = st.session_state.market_radar_results
        if opps is not None:
            if not opps.empty:
                display_opps = opps.copy()

                # Coerce numeric columns — yfinance occasionally returns
                # non-numeric junk (e.g. "Infinity", None) which breaks the
                # Styler's {:.1f} formatter. errors="coerce" converts any
                # offending value to NaN so na_rep="--" handles it cleanly.
                _numeric_cols = [
                    "Price", "52W Discount", "P/E", "Forward P/E",
                    "Earnings Growth", "Beta", "Market Cap", "Radar Score",
                ]
                for _col in _numeric_cols:
                    if _col in display_opps.columns:
                        display_opps[_col] = pd.to_numeric(
                            display_opps[_col], errors="coerce"
                        )

                st.dataframe(
                    display_opps.style.format({
                        "Price": "${:.2f}",
                        "52W Discount": "{:.1f}%",
                        "P/E": "{:.1f}",
                        "Forward P/E": "{:.1f}",
                        "Earnings Growth": "{:.1f}%",
                        "Beta": "{:.2f}",
                        "Market Cap": "${:,.0f}",
                        "Radar Score": "{:.1f}",
                    }, na_rep="--"),
                    use_container_width=True,
                    hide_index=True,
                )

                selected_radar_ticker = st.selectbox(
                    "Add radar candidate to team watchlist",
                    options=display_opps["Ticker"].tolist(),
                    format_func=lambda t: f"{t} · {display_opps.loc[display_opps['Ticker'] == t, 'Company'].iloc[0]}",
                )
                radar_notes = st.text_input(
                    "Radar thesis note",
                    value=f"Radar thesis: {anchor_ticker or RADAR_THEMES[selected_theme_keys[0]].label if selected_theme_keys else 'custom scan'}",
                )
                if st.button("Add Radar Candidate", use_container_width=True):
                    row = display_opps.loc[display_opps["Ticker"] == selected_radar_ticker].iloc[0]
                    try:
                        curr = get_watchlist_df()
                        updated = add_row(
                            curr,
                            ticker=selected_radar_ticker,
                            price_at_add=float(row.get("Price", 0) or 0),
                            partner_key=partner_key,
                            added_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
                            notes=radar_notes,
                            status="Researching",
                        )
                        update_watchlist_df(updated)
                        st.cache_data.clear()
                        st.success(f"Added {selected_radar_ticker} to the team watchlist.")
                    except Exception as e:
                        st.error(f"Error syncing to Sheets: {e}")
            else:
                st.info("No candidates matched those filters. Try widening discount, P/E, growth, or sector filters.")

    # ANLS-01: Structured card layout for controls
    st.markdown("""
<div style="color:#C5A059;font-size:13px;font-weight:600;letter-spacing:0.06em;
            text-transform:uppercase;margin:8px 0 12px 0;padding-bottom:8px;
            border-bottom:1px solid #2A2A2A;">Deep Dive Analysis</div>
""", unsafe_allow_html=True)

    col_input, col_assumptions = st.columns([1, 2])
    with col_input:
        st.markdown('<div style="color:#9E804B;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">Ticker</div>', unsafe_allow_html=True)
        ticker_input = st.text_input("Ticker", label_visibility="collapsed", placeholder="e.g. NVDA").upper()

    if ticker_input:
        ticker_input = validate_ticker(ticker_input)
        data = get_financial_data(ticker_input)
        if data:
            # ANLS-01: Assumption sliders in labelled card
            smart_discount = max(0.06, min(0.042 + (data['Beta'] * 0.055), 0.15))
            with col_input:
                st.markdown(f'<div style="color:#9E804B;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;margin:16px 0 2px 0;">{data["Name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="color:#F5F5F5;font-size:20px;font-weight:600;font-variant-numeric:tabular-nums;">${data["Price"]}</div>', unsafe_allow_html=True)
            with col_assumptions:
                st.markdown('<div style="color:#9E804B;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;">Valuation Assumptions</div>', unsafe_allow_html=True)
                growth = st.slider(f"Growth Rate (Analyst est: {data['Analyst_Growth']:.1%})", 0.0, 0.30, float(data['Analyst_Growth']), 0.01)
                discount = st.slider(f"Discount Rate (Beta: {data['Beta']})", 0.05, 0.20, float(smart_discount), 0.01)

            intrinsic_value = calculate_dcf(data['FCF'], data['Shares'], growth, discount)
            upside = ((intrinsic_value - data['Price']) / data['Price']) * 100
            upside_color = "#16A34A" if upside >= 0 else "#DC2626"
            upside_arrow = "▲" if upside >= 0 else "▼"

            # FCF / growth health warnings
            if data['FCF'] < 0:
                st.warning(
                    f"⚠️ **Negative Free Cash Flow**: {data['Name']} reported "
                    f"negative FCF (${data['FCF']/1e9:.2f}B TTM). The DCF model projects "
                    f"this forward — treat the intrinsic value as highly speculative "
                    f"until FCF turns positive."
                )
            if data.get('Raw_Analyst_Growth', 0) < 0:
                st.info(
                    f"ℹ️ Analyst consensus growth is negative "
                    f"({data['Raw_Analyst_Growth']:.1%}). "
                    f"Growth rate has been floored at 2% for modeling purposes."
                )

            # ANLS-02: DCF result hero card + supporting KPI cards
            st.markdown(f"""
<div style="background:#111111;border:1px solid #2A2A2A;border-left:3px solid #C5A059;
            border-radius:6px;padding:20px 24px;margin:16px 0 8px 0;">
  <div style="color:#9E804B;font-size:10px;letter-spacing:0.12em;
              text-transform:uppercase;margin-bottom:8px;">DCF Intrinsic Value</div>
  <div style="color:#C5A059;font-size:40px;font-weight:700;
              font-variant-numeric:lining-nums tabular-nums;line-height:1.1;">${intrinsic_value:,.2f}</div>
  <div style="color:{upside_color};font-size:14px;margin-top:8px;font-weight:500;">
    {upside_arrow} {abs(upside):.1f}% vs ${data['Price']} market price
  </div>
</div>
""", unsafe_allow_html=True)

            k1, k2, k3 = st.columns(3)
            with k1:
                st.markdown(_kpi_card("Market Price", f"${data['Price']}"), unsafe_allow_html=True)
            with k2:
                fcf_val = data['FCF']
                fcf_display = f"-${abs(fcf_val)/1e9:.2f}B" if fcf_val < 0 else f"${fcf_val/1e9:.2f}B"
                fcf_color = "#DC2626" if fcf_val < 0 else "#F5F5F5"
                st.markdown(_kpi_card("Free Cash Flow", fcf_display, value_color=fcf_color), unsafe_allow_html=True)
            with k3:
                st.markdown(_kpi_card("Beta", f"{data['Beta']:.2f}"), unsafe_allow_html=True)

            # 2. CHARTS & NEWS
            tab_financials, tab_news = st.tabs(["📈 Financials", "📰 News Feed"])

            with tab_financials:
                if not data['History'].empty:
                    years = st.slider("Select time scope (years)", min_value=1, max_value=4, value=4, step=1)
                    history_filtered = data['History'].tail(years)
                    st.write(f"**Performance Trend ({years}yr)**")
                    st.bar_chart(history_filtered, color=["#C5A059", "#9E804B"])
                else:
                    st.caption("No historical data available.")

            with tab_news:
                # Source-type badge colours
                _SOURCE_BADGE = {
                    "yfinance":   ("📰", "#2A2A2A", "#C5A059"),
                    "google_news": ("🌐", "#1A2A1A", "#4ADE80"),
                    "sec_edgar":  ("🏛️", "#1A1A2A", "#818CF8"),
                }

                st.write(f"**Latest News for {data['Name']}**")
                st.caption(
                    f"Sources: Yahoo Finance · Google News · SEC EDGAR  |  "
                    f"{len(data['News'])} article(s) loaded"
                )

                if data['News']:
                    for news_item in data['News']:
                        title = news_item.get("title", "")
                        if not title:
                            continue
                        link = news_item.get("link", "#")
                        publisher = news_item.get("publisher", "Unknown")
                        pub_date_str = news_item.get("pub_date", "")
                        src_type = news_item.get("source_type", "yfinance")

                        # Format date — handles ISO-8601 and RFC-2822
                        pub_formatted = pub_date_str
                        for fmt in (
                            lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M"),
                            lambda s: datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d %H:%M"),
                            lambda s: datetime.strptime(s[:25], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d"),
                        ):
                            try:
                                pub_formatted = fmt(pub_date_str)
                                break
                            except Exception:
                                continue

                        icon, badge_bg, badge_fg = _SOURCE_BADGE.get(src_type, ("📰", "#2A2A2A", "#C5A059"))
                        st.markdown(
                            f'<span style="background:{badge_bg};color:{badge_fg};'
                            f'font-size:10px;padding:2px 7px;border-radius:4px;'
                            f'letter-spacing:0.06em;text-transform:uppercase;">'
                            f'{icon} {publisher}</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"**[{title}]({link})**")
                        st.caption(pub_formatted)
                        st.divider()
                else:
                    st.caption("No recent news available.")

            # 3. ACTION
            notes = st.text_area("Investment Thesis", height=100)
            if st.button(f"Add {ticker_input} to Watchlist"):
                try:
                    curr = get_watchlist_df()
                    updated = add_row(
                        curr,
                        ticker=ticker_input,
                        price_at_add=data["Price"],
                        partner_key=partner_key,
                        added_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        notes=notes,
                        status="Watching",
                    )
                    update_watchlist_df(updated)
                    st.cache_data.clear()
                    st.success("Synced!")
                except Exception as e:
                    st.error(f"Error syncing to Sheets: {e}")

# --- TAB 3: PORTFOLIO OPTIMIZER ---
if active_workspace == "Allocation Dashboard":
    st.subheader("Allocation Decision Dashboard")
    st.caption("Risk-aware allocation across tech, healthcare, infrastructure, broad ETFs, and bonds.")

    raw_portfolio = None
    rich_portfolio = None
    current_weights = {}
    total_equity_for_rebalance = 0.0
    try:
        raw_portfolio = get_portfolio_df()
        if raw_portfolio is not None and not raw_portfolio.empty:
            rich_portfolio, total_equity_for_rebalance, _ = get_portfolio_performance(raw_portfolio)
            current_weights = current_portfolio_weights(rich_portfolio)
    except Exception:
        pass

    opt_col1, opt_col2 = st.columns([1, 2])
    with opt_col1:
        profile_key = st.radio(
            "Mandate",
            list(PROFILES.keys()),
            format_func=lambda k: PROFILES[k].name,
        )
        include_current = st.checkbox("Include current portfolio tickers", value=True)
        extra_default = "\n".join(current_weights.keys()) if include_current else ""
        extra_tickers_text = st.text_area(
            "Additional tickers",
            value=extra_default,
            height=140,
            help="Optional single-name ideas to include alongside the sleeve ETF universe.",
        )
        selected_sleeves = st.multiselect(
            "Allocation sleeves",
            options=list(SLEEVE_UNIVERSE.keys()),
            default=list(SLEEVE_UNIVERSE.keys()),
            format_func=lambda k: SLEEVE_UNIVERSE[k]["label"],
        )
        run_opt = st.button("Run Allocation Model")

    with opt_col2:
        if run_opt:
            try:
                extra_tickers = [
                    validate_ticker(t)
                    for t in extra_tickers_text.replace(",", "\n").splitlines()
                    if t.strip()
                ]
                sleeve_tickers = []
                for sleeve_key in selected_sleeves:
                    sleeve_tickers.extend(SLEEVE_UNIVERSE[sleeve_key]["tickers"])
                ticker_list = sorted(set(universe_tickers(extra_tickers)) & set(sleeve_tickers + extra_tickers))
                if len(ticker_list) < 2:
                    st.warning("Select at least two investable tickers.")
                    st.stop()

                with st.spinner("Building allocation model..."):
                    prices = get_allocation_prices(tuple(ticker_list))
                    if prices.shape[1] < 2:
                        st.error("Could not download enough price history for the selected universe.")
                        st.stop()
                    result = optimize_allocation(prices, profile_key=profile_key)

                profile = result["profile"]
                weights = {k: v for k, v in result["weights"].items() if v > 0.001}
                score = result["score"]
                asset_mix = result["asset_class_breakdown"]

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(_kpi_card("Expected Return", f"{result['expected_return']:.2%}"), unsafe_allow_html=True)
                with m2:
                    st.markdown(_kpi_card("Volatility", f"{result['volatility']:.2%}"), unsafe_allow_html=True)
                with m3:
                    st.markdown(_kpi_card("Sharpe", f"{result['sharpe']:.2f}", delta=score["label"]), unsafe_allow_html=True)
                with m4:
                    st.markdown(_kpi_card("Bond Sleeve", f"{asset_mix.get('bond', 0):.1%}"), unsafe_allow_html=True)

                st.caption(profile.description)

                alloc_df = pd.DataFrame({
                    "Ticker": list(weights.keys()),
                    "Weight": list(weights.values()),
                }).sort_values("Weight", ascending=True)
                fig = px.bar(
                    alloc_df,
                    x="Weight",
                    y="Ticker",
                    orientation="h",
                    text=alloc_df["Weight"].apply(lambda w: f"{w:.1%}"),
                    color_discrete_sequence=["#C5A059"],
                )
                opt_layout = {
                    **PLOTLY_DARK_LAYOUT,
                    "height": max(300, len(alloc_df) * 34),
                    "margin": dict(t=10, b=10, l=10, r=10),
                }
                fig.update_layout(**opt_layout, xaxis_tickformat=".0%")
                fig.update_traces(textfont_color="#0A0A0A", textfont_size=11)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                mix_df = pd.DataFrame({
                    "Asset Class": [k.title() for k in asset_mix.keys()],
                    "Weight": list(asset_mix.values()),
                })
                sleeve_df = pd.DataFrame({
                    "Sleeve": [
                        SLEEVE_UNIVERSE.get(k, {}).get("label", k)
                        for k in result["sleeve_breakdown"].keys()
                    ],
                    "Weight": list(result["sleeve_breakdown"].values()),
                })
                mix_col, sleeve_col = st.columns(2)
                with mix_col:
                    st.write("**Asset Mix**")
                    st.dataframe(
                        mix_df.style.format({"Weight": "{:.1%}"}),
                        use_container_width=True,
                        hide_index=True,
                    )
                with sleeve_col:
                    st.write("**Sleeve Exposure**")
                    st.dataframe(
                        sleeve_df.style.format({"Weight": "{:.1%}"}),
                        use_container_width=True,
                        hide_index=True,
                    )

                if current_weights and total_equity_for_rebalance > 0:
                    st.write("**Rebalance Delta vs Current Portfolio**")
                    rebalance_df = rebalance_recommendation(
                        current_weights,
                        weights,
                        total_equity_for_rebalance,
                    )
                    st.dataframe(
                        rebalance_df.style.format({
                            "Current Weight": "{:.1%}",
                            "Target Weight": "{:.1%}",
                            "Delta Weight": "{:+.1%}",
                            "Dollar Amount": "${:+,.0f}",
                        }),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Add portfolio holdings to Google Sheets to see buy/sell rebalance deltas.")

                st.write("**News Cross-Check**")
                news_df = allocation_news_summary(
                    sorted(weights, key=weights.get, reverse=True),
                    max_tickers=8,
                )
                st.dataframe(
                    news_df.style.format({"Score": "{:+.2f}"}),
                    use_container_width=True,
                    hide_index=True,
                )
            except Exception as e:
                st.error(f"Allocation model failed: {e}")
