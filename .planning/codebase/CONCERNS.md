# Codebase Concerns

**Analysis Date:** 2026-02-18

## Tech Debt

**Unpinned Dependencies:**
- Issue: `requirements.txt` lists all packages without version pins (e.g., `streamlit`, `yfinance`, `pypfopt`, `scikit-learn`)
- Files: `requirements.txt`
- Impact: Any upstream package release can silently break the app; yfinance in particular changes its API surface frequently
- Fix approach: Pin all packages with exact versions (`pip freeze > requirements.txt`) and adopt a lockfile strategy

**Bare `except` Clauses Throughout:**
- Issue: The entire codebase uses bare `except:` or `except Exception:` that swallow errors silently and return `None` or empty values with no logging
- Files: `app.py` lines 39, 85, 106, 118, 135, 202, 280, 293
- Impact: Failures are invisible to operators; root cause analysis is impossible; bugs can go undetected indefinitely
- Fix approach: Replace bare excepts with typed exception handlers (`except (yf.exceptions.YFException, KeyError) as e:`) and log or surface errors clearly

**Single Monolithic File:**
- Issue: All application logic (data fetching, financial calculations, UI rendering) is in a single 338-line `app.py` file
- Files: `app.py`
- Impact: As features grow, the file becomes unmanageable; functions cannot be tested in isolation; no separation of concerns
- Fix approach: Split into `data/` (yfinance fetching), `models/` (DCF, portfolio math), and `ui/` (tab rendering) modules

**No-Auth "Partner Login":**
- Issue: The partner selector on line 23 is a `st.sidebar.selectbox` with hardcoded strings (`"Partner A"`, `"Partner B"`, `"Partner C"`) — no actual authentication
- Files: `app.py` lines 23–24
- Impact: Any user who accesses the app can impersonate any partner; write operations to Google Sheets (Watchlist) are attributed to the selected fake identity
- Fix approach: Implement real authentication via Streamlit's auth features or Google OAuth before any multi-user deployment

**DataFrame Mutation In-Place:**
- Issue: `get_portfolio_performance` receives `df` and mutates it directly with new columns rather than working on a copy
- Files: `app.py` lines 52–65
- Impact: Cached function modifies its input argument, which can cause subtle state bugs on re-runs since Streamlit caches function inputs; data corruption may occur between sessions
- Fix approach: Add `df = df.copy()` at the start of `get_portfolio_performance`

## Known Bugs

**`@st.cache_data` with Mutable DataFrame Argument:**
- Symptoms: `get_portfolio_performance` is decorated with `@st.cache_data` but accepts a DataFrame parameter; Streamlit hashes DataFrames for cache keys, but since the function mutates its argument, cached results may reflect stale or incorrect column values after a partial refresh
- Files: `app.py` lines 28–67
- Trigger: Refresh Portfolio button clears cache, followed by any data change in Google Sheets
- Workaround: Currently, the "Refresh Portfolio" button on line 206 clears all cache with `st.cache_data.clear()` which is a blunt workaround

**Division by Zero in P&L Percentage:**
- Symptoms: The P&L delta metric on line 176 divides by `total_equity` without a prior zero-guard beyond the inline conditional — if `total_equity` evaluates to float `0.0` (not `0`), the condition `if total_equity > 0` will catch it, but if upstream data contains NaN the sum may produce NaN rather than 0
- Files: `app.py` line 176
- Trigger: Portfolio sheet with tickers that have no current price data
- Workaround: None explicit

**yfinance `ticker_objects` API Call Per Row:**
- Symptoms: `get_financial_data` calls `yf.Ticker(ticker).info` once per ticker in the portfolio on line 54 inside an `apply` call — each `.info` call is a blocking HTTP request
- Files: `app.py` lines 38, 53–55
- Trigger: Portfolio with more than ~5 holdings; each page load within the 5-minute TTL window causes N sequential HTTP calls
- Workaround: None; performance degrades linearly with portfolio size

## Security Considerations

**Secrets File Committed Risk:**
- Risk: `.streamlit/secrets.toml` is listed in `.gitignore`, but a misconfigured git operation could accidentally commit it along with Google Sheets credentials and any service account keys
- Files: `.gitignore` line 5, `.streamlit/secrets.toml` (existence noted, contents not read)
- Current mitigation: `.gitignore` entry is present
- Recommendations: Add a pre-commit hook that scans for secrets; use `git-secrets` or `detect-secrets`; document required environment variables separately instead of relying solely on `.gitignore`

**No Input Validation on Ticker Input:**
- Risk: The ticker text input on line 220 is passed directly to `yf.download()` and `yf.Ticker()` without sanitization; malformed input or injection attempts are passed to the yfinance library
- Files: `app.py` lines 220–223
- Current mitigation: yfinance itself is somewhat resilient; errors are caught by bare `except`
- Recommendations: Validate that ticker input matches a regex like `^[A-Z0-9.\-]{1,10}$` before passing to yfinance

**No Input Validation on Tickers Text Area (Optimizer):**
- Risk: The optimizer accepts multiline text from the user on line 298, splits on newlines, and passes each line directly to `yf.download()`
- Files: `app.py` lines 298–307
- Current mitigation: Bare `except Exception` wraps the call
- Recommendations: Same ticker validation regex; limit number of tickers to a sane maximum (e.g., 50)

**Watchlist Write Without Validation:**
- Risk: Adding to watchlist on line 274 writes user-provided text (`notes` text area) directly to Google Sheets without sanitization — any formula injection (e.g., `=CMD()` or `=IMPORTURL()`) in Notes field could execute in Google Sheets
- Files: `app.py` lines 273–280
- Current mitigation: None
- Recommendations: Strip leading `=`, `+`, `-`, `@` characters from user text before writing to Sheets (CSV injection prevention)

## Performance Bottlenecks

**Sequential Per-Ticker HTTP Calls for Sector Data:**
- Problem: Inside `get_portfolio_performance`, sector information is fetched by calling `.info` on individual `yf.Ticker` objects one at a time via `apply` on line 53
- Files: `app.py` lines 38, 53–55
- Cause: No batching; yfinance does not natively batch `.info` calls; each is a separate HTTP request
- Improvement path: Cache sector data with a longer TTL separately from price data; use `yf.download` batch for prices and a separate cached lookup for fundamentals

**Market Scanner Scans 15 Tickers Sequentially:**
- Problem: `scan_market_opportunities` loops over 15 hardcoded tickers (line 124) and calls `yf.Ticker(ticker).info` for each one sequentially
- Files: `app.py` lines 121–136
- Cause: No concurrency; each `.info` call takes ~1–2 seconds; full scan takes 15–30 seconds
- Improvement path: Use `concurrent.futures.ThreadPoolExecutor` to parallelize `.info` calls; or pre-fetch using `yf.download` for bulk price data

**Portfolio Data Read on Every Tab Render:**
- Problem: `conn.read(worksheet="Portfolio", ttl=5)` is called twice — once in Tab 1 (line 169) and once in Tab 3 (line 290) — with a 5-second TTL, meaning frequent re-reads
- Files: `app.py` lines 169, 290
- Cause: No shared data layer; each tab reads independently
- Improvement path: Read portfolio data once at the top of the script and pass it to tabs

## Fragile Areas

**yfinance API Stability:**
- Files: `app.py` lines 36–117
- Why fragile: yfinance is an unofficial scraper of Yahoo Finance; the API breaks regularly with Yahoo Finance layout changes; the project has no tests to detect breakage; bare `except` clauses mean the app silently returns empty/zero data when yfinance breaks
- Safe modification: Always test after yfinance version updates; consider adding a sentinel check that verifies a known ticker returns expected fields
- Test coverage: Zero — no tests exist anywhere in the project

**DCF Calculation with Zero/Negative FCF:**
- Files: `app.py` lines 138–142
- Why fragile: `calculate_dcf` guards against `shares == 0` and `fcf == 0` but does not guard against negative FCF, which is common for growth companies; negative FCF will produce a negative intrinsic value that is displayed as a negative dollar figure without any warning
- Safe modification: Add an explicit check and display a warning when FCF is negative
- Test coverage: Zero

**Google Sheets Connection as Single Point of Failure:**
- Files: `app.py` lines 15–19
- Why fragile: If the Google Sheets connection fails, `st.stop()` is called immediately, rendering the entire app inoperable — there is no fallback, read-from-cache, or degraded mode
- Safe modification: Catch the connection error gracefully and allow the Analysis Lab tab to function independently (it does not require Sheets)
- Test coverage: Zero

## Scaling Limits

**Single-File App Architecture:**
- Current capacity: Works for a single investment portfolio with ~20 positions
- Limit: Adding new features (multiple portfolios, transaction history, alerts) requires cramming more code into `app.py`
- Scaling path: Refactor into a multi-page Streamlit app using `pages/` directory convention; extract data and model layers into importable modules

**Google Sheets as Database:**
- Current capacity: Functional for small datasets (<1,000 rows)
- Limit: Sheets has a 10M cell limit; read/write speed degrades with data volume; no indexing, no relational queries, no transactions
- Scaling path: Migrate to a lightweight database (SQLite for local, Supabase for hosted) when transaction history or multi-portfolio tracking is needed

## Dependencies at Risk

**yfinance (Unofficial API):**
- Risk: Not an official Yahoo Finance API; Yahoo has historically blocked scrapers; library breaks without notice on Yahoo layout changes
- Impact: All price data, sector data, news, and financial statements become unavailable
- Migration plan: Consider using a paid financial data API (Polygon.io, Alpha Vantage, or Tiingo) with a proper API key as a fallback or primary source

**pypfopt:**
- Risk: Relatively niche library with limited maintenance activity; requires `scikit-learn` as a transitive dependency; API changes between versions can silently alter optimization results
- Impact: Portfolio Optimizer tab breaks
- Migration plan: Pin to a specific version; consider implementing basic mean-variance optimization directly using `numpy` to remove the dependency

## Missing Critical Features

**No Authentication:**
- Problem: The app has no real login system despite displaying "Partner Login" and allowing named writes to a shared spreadsheet
- Blocks: Safe multi-user use; audit trails for who added what to the Watchlist

**No Tests:**
- Problem: Zero test files exist in the project; no unit tests for `calculate_dcf`, `get_portfolio_performance`, or `optimize_portfolio`
- Blocks: Safe refactoring; confidence in financial calculation correctness; detecting yfinance API breaks

**No Error Logging:**
- Problem: All exceptions are silently swallowed by bare `except` blocks; there is no logging to file, console, or an observability service
- Blocks: Diagnosing production issues; understanding how often yfinance calls fail

## Test Coverage Gaps

**Financial Calculation Functions (Zero Coverage):**
- What's not tested: `calculate_dcf` with edge cases (negative FCF, zero shares, extreme growth rates); `get_portfolio_performance` column computation accuracy; `optimize_portfolio` strategy variants
- Files: `app.py` lines 138–160
- Risk: Incorrect financial calculations displayed to real investment partners without any validation
- Priority: High

**Data Fetching Functions (Zero Coverage):**
- What's not tested: `get_financial_data` response parsing; `scan_market_opportunities` filtering logic; handling of missing yfinance fields
- Files: `app.py` lines 69–136
- Risk: Silent breakage when yfinance changes its response structure
- Priority: High

**Google Sheets Integration (Zero Coverage):**
- What's not tested: `conn.read` / `conn.update` error paths; Watchlist write logic; portfolio data shape assumptions
- Files: `app.py` lines 15–19, 169, 277–279
- Risk: Data loss or corruption in the shared Sheets document goes undetected
- Priority: Medium

---

*Concerns audit: 2026-02-18*
