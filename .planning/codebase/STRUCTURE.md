# Codebase Structure

**Analysis Date:** 2026-02-18

## Directory Layout

```
Project Photizo/
├── app.py                          # Entire application — entry point, models, UI
├── requirements.txt                # Python dependencies
├── .gitignore                      # Excludes venv, secrets, credentials, .DS_Store
├── .streamlit/
│   └── secrets.toml                # Streamlit secrets (Google Sheets credentials) — gitignored
├── .planning/
│   └── codebase/                   # GSD codebase analysis documents
├── venv/                           # Python virtual environment — gitignored
├── get-shit-done/                  # Git submodule: GSD CLI tooling
└── ui-ux-pro-max-skill/            # Git submodule: UI/UX Claude skill
```

## Directory Purposes

**Root:**
- Purpose: Contains the entire application in a single file
- Key files: `app.py`, `requirements.txt`

**`.streamlit/`:**
- Purpose: Streamlit configuration and secrets
- Contains: `secrets.toml` with Google Sheets service account credentials and spreadsheet URL
- Note: Gitignored — must be provisioned manually on each deployment environment

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents used by planning and execution agents
- Contains: ARCHITECTURE.md, STRUCTURE.md, and other analysis files
- Generated: Yes (by GSD map-codebase)
- Committed: Yes

**`venv/`:**
- Purpose: Python 3.9 virtual environment
- Generated: Yes
- Committed: No (gitignored)

**`get-shit-done/`:**
- Purpose: Git submodule containing the GSD (Get Shit Done) CLI and agent framework
- Committed: Yes (as submodule reference)

**`ui-ux-pro-max-skill/`:**
- Purpose: Git submodule containing a Claude UI/UX skill with templates and CLI tooling
- Committed: Yes (as submodule reference)

## Key File Locations

**Entry Points:**
- `app.py`: The single entry point — run with `streamlit run app.py`

**Configuration:**
- `requirements.txt`: All Python package dependencies
- `.streamlit/secrets.toml`: Google Sheets connection credentials (gitignored)
- `.gitignore`: Excludes venv, secrets, credentials JSON, build artifacts, IDE files

**Core Logic:**
- `app.py` lines 29–67: `get_portfolio_performance()` — live price enrichment
- `app.py` lines 70–118: `get_financial_data()` — DCF data aggregation
- `app.py` lines 121–136: `scan_market_opportunities()` — market scanner
- `app.py` lines 138–142: `calculate_dcf()` — pure DCF model
- `app.py` lines 144–160: `optimize_portfolio()` — mean-variance optimization

**UI Sections:**
- `app.py` lines 166–206: Tab 1 — Portfolio War Room
- `app.py` lines 209–280: Tab 2 — Analysis Lab
- `app.py` lines 283–337: Tab 3 — Portfolio Optimizer

## Naming Conventions

**Files:**
- Lowercase with underscores: `app.py`, `requirements.txt`
- Only one source file exists; no multi-file naming pattern to establish

**Functions:**
- `snake_case` for all function names: `get_portfolio_performance`, `calculate_dcf`, `optimize_portfolio`
- `get_` prefix for data-fetching functions, no prefix for pure computation

**Variables:**
- `snake_case` throughout: `total_equity`, `ticker_input`, `alloc_df`
- DataFrames suffixed with `_df`: `raw_df`, `df_rich`, `alloc_df`
- Column names use title case with spaces: `'Market Value'`, `'Current Price'`, `'Unrealized Gain ($)'`

**Streamlit Widgets:**
- Named by purpose: `ticker_input`, `tickers_text`, `strategy`, `target_ret`

## Where to Add New Code

**New financial model or data function:**
- Add to `app.py` in the "THE BRAIN" section (lines 27–160), before the tabs interface
- Decorate with `@st.cache_data(ttl=300)` if the function calls external APIs

**New UI tab:**
- Add a new tab name to the `st.tabs([...])` call at line 163
- Add a corresponding `with tab_xxx:` block after line 337

**New configuration or secret:**
- Add the key to `.streamlit/secrets.toml` (not committed)
- Document the required key name in README or setup instructions

**Utility/helper logic:**
- Currently no separate utilities file; add pure functions inline in `app.py` above the tabs section
- If the project grows beyond one file, create `utils/` directory for shared helpers

## Special Directories

**`.streamlit/`:**
- Purpose: Streamlit runtime configuration
- `secrets.toml` holds the Google Sheets URL and service account JSON key
- Generated: No (manually created)
- Committed: No (gitignored by `.gitignore`)

**`venv/`:**
- Purpose: Isolated Python 3.9 environment with all packages from `requirements.txt`
- Activate with: `source venv/bin/activate`
- Generated: Yes (`python -m venv venv && pip install -r requirements.txt`)
- Committed: No

---

*Structure analysis: 2026-02-18*
