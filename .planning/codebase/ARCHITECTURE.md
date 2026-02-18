# Architecture

**Analysis Date:** 2026-02-18

## Pattern Overview

**Overall:** Single-file monolithic Streamlit application

**Key Characteristics:**
- All logic — data fetching, financial modeling, UI rendering — lives in `app.py`
- No separate modules, services, or layers; functions are defined at the top and consumed inline
- Streamlit's reactive execution model means the entire script re-runs on each user interaction
- Data layer is Google Sheets (via `st.connection`), not a traditional database
- External market data is fetched live from Yahoo Finance (`yfinance`) with 5-minute caching

## Layers

**Data Connection Layer:**
- Purpose: Connect to Google Sheets as the portfolio database
- Location: `app.py` lines 14–19
- Contains: `st.connection("gsheets", type=GSheetsConnection)` setup
- Depends on: `.streamlit/secrets.toml` for credentials
- Used by: Tab 1 (portfolio read), Tab 2 (watchlist read/write)

**Financial Model Layer:**
- Purpose: Fetch live market data and compute investment metrics
- Location: `app.py` lines 27–160 (all decorated with `@st.cache_data(ttl=300)` or plain functions)
- Contains: `get_portfolio_performance()`, `get_financial_data()`, `scan_market_opportunities()`, `calculate_dcf()`, `optimize_portfolio()`
- Depends on: `yfinance`, `pypfopt`, `pandas`, `numpy`
- Used by: All three tab sections

**UI / Presentation Layer:**
- Purpose: Render all user-facing components
- Location: `app.py` lines 162–337
- Contains: Three Streamlit tabs — Portfolio War Room, Analysis Lab, Portfolio Optimizer
- Depends on: Financial model functions, `plotly.express` for charts
- Used by: End user via browser

## Data Flow

**Portfolio View Flow:**

1. User opens app; Streamlit runs `app.py` top-to-bottom
2. `conn.read(worksheet="Portfolio", ttl=5)` fetches raw holdings from Google Sheets
3. `get_portfolio_performance(df)` calls `yf.download()` to fetch live prices and `yf.Ticker().info` for sector data
4. Computed metrics (Market Value, Unrealized Gain, Return) are rendered as metrics, pie charts, and a styled dataframe

**DCF Analysis Flow:**

1. User enters ticker in Analysis Lab tab
2. `get_financial_data(ticker)` fetches cash flow, financials, and news from Yahoo Finance
3. `calculate_dcf()` computes intrinsic value using user-adjusted growth/discount sliders
4. Results displayed as metric columns plus financial history bar chart and news feed

**Portfolio Optimization Flow:**

1. User provides tickers (auto-populated from Portfolio sheet) and selects strategy
2. `optimize_portfolio()` calls `yf.download()` for 1 year of price history
3. `pypfopt.EfficientFrontier` computes optimal weights (Max Sharpe / Min Volatility / Target Return)
4. Results rendered as horizontal bar chart and allocation dataframe

**Watchlist Write Flow:**

1. User enters investment thesis notes and clicks "Add to Watchlist"
2. App reads current Watchlist sheet, appends new row, calls `conn.update()` to write back

**State Management:**
- `@st.cache_data(ttl=300)` caches all expensive Yahoo Finance calls for 5 minutes
- Google Sheets reads use `ttl=5` (5 seconds) for near-real-time sync
- No persistent in-memory state beyond Streamlit's built-in session; each rerun re-executes the script
- User clears cache via "Refresh Portfolio" button which calls `st.cache_data.clear()`

## Key Abstractions

**`get_portfolio_performance(df)`:**
- Purpose: Enriches a raw holdings DataFrame with live prices, sector, and P&L metrics
- File: `app.py` lines 29–67
- Pattern: Takes raw Google Sheets DataFrame, returns enriched DataFrame + scalar totals

**`get_financial_data(ticker)`:**
- Purpose: Aggregates all data needed for DCF analysis into a single dict
- File: `app.py` lines 70–118
- Pattern: Returns typed dict with keys `Price`, `FCF`, `Beta`, `Analyst_Growth`, `History`, `News`, or `None` on failure

**`calculate_dcf(fcf, shares, growth, discount, terminal_growth)`:**
- Purpose: Pure function implementing 5-year DCF with terminal value
- File: `app.py` lines 138–142
- Pattern: Pure computation, no side effects, no caching

**`optimize_portfolio(tickers, strategy, target_return)`:**
- Purpose: Wraps `pypfopt.EfficientFrontier` for three optimization strategies
- File: `app.py` lines 144–160
- Pattern: Returns `(weights_dict, performance_tuple)` or `(None, None)` on failure

## Entry Points

**Application Entry Point:**
- Location: `app.py` (root of project)
- Triggers: `streamlit run app.py`
- Responsibilities: Page config, database connection, function definitions, tab rendering

## Error Handling

**Strategy:** Broad `try/except` with silent fallbacks or `st.warning/st.error` display

**Patterns:**
- Data fetch failures return `None`, empty DataFrame, or zero-value scalars
- Sheet connection failure calls `st.stop()` to halt app render
- Most inner exceptions use bare `except:` (no exception type) and continue silently
- User-visible errors shown via `st.error()`, `st.warning()`, `st.caption()`

## Cross-Cutting Concerns

**Logging:** None — all feedback is surfaced through Streamlit UI components, no file or structured logging
**Validation:** Minimal — ticker input is uppercased; numeric guards (e.g., `shares == 0`) exist in financial functions
**Authentication:** Soft multi-user via sidebar selectbox (`Partner A / B / C`); no real auth or session isolation

---

*Architecture analysis: 2026-02-18*
