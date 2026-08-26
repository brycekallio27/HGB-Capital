# Project Photizo — Tasks

_HGB Capital investment dashboard. Streamlit + Python._
_For full project context, read CLAUDE.md in this folder before executing any task._

---

## Active

### 🐛 Bug Fixes (do these first — they affect data correctness)

- [x] ~~**Fix DataFrame mutation bug**~~ - In `app.py`, find `get_portfolio_performance()` and add `df = df.copy()` as the first line inside the function, before any mutations. This prevents `@st.cache_data` from returning stale/corrupt data across rerenders. Reference: CLAUDE.md line 57. **DONE 2026-03-12**

- [x] ~~**Fix NaN division-by-zero in P&L calc**~~ - In `app.py` around line 176, the P&L % calculation divides by `total_equity`. The current `if total_equity > 0` guard does not catch NaN. Replace with: `if total_equity and total_equity > 0 and not pd.isna(total_equity)`. Import pandas as pd if not already imported at that scope. **DONE 2026-03-12**

- [x] ~~**Replace all bare `except` clauses**~~ - In `app.py`, find all 8 bare `except:` blocks (lines ~39, 85, 106, 118, 135, 202, 280, 293). Replace each with `except Exception as e:` and add `st.warning(f"Error: {e}")` or a specific logged message so failures are visible instead of silently swallowed. **DONE 2026-03-12**

### 🔒 Security

- [x] ~~**Add input validation for ticker inputs**~~ - In `app.py`, find the two ticker input fields (lines ~220 and ~298). Add a validation function: `def validate_ticker(ticker: str) -> str:` that strips whitespace, uppercases, and checks against `re.match(r'^[A-Z]{1,5}$', ticker)`. Raise a `st.error()` and `st.stop()` on invalid input. Import `re` at the top of the file. **DONE 2026-03-12**

- [x] ~~**Sanitize watchlist notes for CSV injection**~~ - In `app.py`, find where watchlist notes are written to Google Sheets (~line 273). Prefix any note value starting with `=`, `+`, `-`, or `@` with a single quote `'` before writing to prevent CSV formula injection. **DONE 2026-03-12**

### ⚡ Performance

- [x] ~~**Parallelize portfolio HTTP calls**~~ - In `app.py`, refactor `get_portfolio_performance()` to fetch ticker data concurrently using `concurrent.futures.ThreadPoolExecutor`. Replace the sequential per-ticker loop with a `pool.map()` call. This reduces N blocking HTTP requests to ~1 round trip time. **DONE 2026-03-12**

- [x] ~~**Deduplicate Google Sheets reads**~~ - In `app.py`, the portfolio DataFrame is read twice (Tab 1 ~line 169, Tab 3 ~line 290). Extract a single `@st.cache_data(ttl=300)` function `get_portfolio_df()` that reads once, and call it in both tabs. **DONE 2026-03-12**

- [x] ~~**Pin all dependencies**~~ - In `requirements.txt`, pin every package to its current installed version. Run `pip freeze` in the venv to get exact versions. This prevents yfinance and other packages from silently breaking on upstream changes. **DONE 2026-03-12**

### 🎨 UI Redesign (v1.0 — do in order)

- [x] ~~**Phase 1A: Create `.streamlit/config.toml`**~~ - Following `.planning/phases/01-design-system-foundation/01-01-PLAN.md`. Create the config file with Inter font + dark base theme. Do not touch `app.py`. **DONE 2026-03-12**

- [x] ~~**Phase 1B: Add CSS injection to `app.py`**~~ - Following `.planning/phases/01-design-system-foundation/01-02-PLAN.md`. Add `DARK_CSS` and `LIGHT_CSS` string constants and an `inject_css()` function using `st.html()` (fallback: `st.markdown(unsafe_allow_html=True)`). **DONE 2026-03-12**

- [x] ~~**Phase 1C: Dark/light toggle + semantic P&L colors**~~ - Following `.planning/phases/01-design-system-foundation/01-03-PLAN.md`. Add sun/moon toggle in sidebar using `st.session_state`. Apply semantic green/red to P&L values. Also apply the `df.copy()` fix from the bug task above if not already done. **DONE 2026-03-12**

- [x] ~~**Phase 2: Global widget overrides**~~ - Style all buttons, tabs, inputs, and dataframes with the black/gold brand palette defined in CLAUDE.md. Use CSS injection from Phase 1B as the delivery mechanism. **DONE 2026-03-12**

- [x] ~~**Phase 3: Portfolio War Room redesign**~~ - Redesign the KPI metric cards (gold borders, large numerals) and apply `plotly_dark` base theme to all pie charts with gold accent colors. **DONE 2026-03-12**

- [x] ~~**Phase 4: Sidebar branding**~~ - Add HGB Capital header/logo text to the top of the sidebar in gold. Style the partner selector dropdown to match the brand. **DONE 2026-03-12**

- [x] ~~**Phase 5: Analysis Lab & Optimizer polish**~~ - Apply card layouts to DCF output, market scanner results, and optimizer output. Result cards should have gold borders and dark backgrounds. **DONE 2026-03-12**

---

## Active

### 🚀 Launch & Hosting (2026-08-25)

- [x] ~~**Real authentication (v2)**~~ - Clerk email/password + 2FA via `landing/`, JWT-verified server-side in `app.py`. PIN fallback removed entirely (was a security hole — real PINs were sitting in plaintext in `.streamlit/secrets.example.toml`). **DONE 2026-08-25**
- [x] ~~**Fix `requirements.txt` bad package name**~~ - `pypfopt>=1.5.0` isn't installable (that's the import name; PyPI package is `PyPortfolioOpt`). Would have broken the Streamlit Cloud deploy. **DONE 2026-08-25**
- [x] ~~**Dedupe CSS constants**~~ - `app.py` had its own inline `DARK_CSS`/`LIGHT_CSS` shadowing the imports from `photizo/ui.py`. Consolidated into `photizo/ui.py` as the single source. **DONE 2026-08-25**
- [x] ~~**Fix flaky allocation tests**~~ - Two tests compared floats with `==`, failing on rounding noise. Switched to `pytest.approx`. **DONE 2026-08-25**
- [ ] **Deploy landing/ to Netlify** - base directory `landing`, env vars from `landing/.env.local.example`.
- [ ] **Deploy app.py to Streamlit Community Cloud** - main file `app.py`, secrets from `.streamlit/secrets.example.toml` template. Enable viewer-restriction allowlist as defense-in-depth behind the Clerk gate.
- [ ] **Enable Clerk MFA (Required)** - dashboard toggle, not code.
- [ ] **Fix placeholder partner emails** - `hunter@email.com` / `grayson@email.com` in `secrets.toml` need real addresses (found candidates in the old example file: `huntstew23@gmail.com`, `graysonwitt27@gmail.com` — confirm before using).
- [ ] **Cross-wire URLs** - once both are deployed, set `[clerk].landing_url` in `secrets.toml` to the real Netlify URL, and `NEXT_PUBLIC_STREAMLIT_URL` in Netlify to the real Streamlit Cloud URL.

---

## Someday

- [ ] **Modularize `app.py`** - Split the 338-line monolith into modules: `data/`, `models/`, `ui/`. Deferred — out of scope for v1.
- [ ] **Add test coverage** - Unit tests for DCF calculations and portfolio math using pytest. Deferred — out of scope for v1.
- [ ] **Handle negative FCF in DCF** - Display a warning when FCF is negative instead of showing a negative intrinsic value as if it were meaningful.
- [ ] **Decouple from Google Sheets** - Make Sheets optional; fall back to a local CSV so the app doesn't `st.stop()` on connection failure.

---

## Done

