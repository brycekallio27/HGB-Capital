# Technology Stack

**Analysis Date:** 2026-02-18

## Languages

**Primary:**
- Python 3.9.6 - All application logic, data processing, UI

**Secondary:**
- TOML - Configuration (`.streamlit/secrets.toml`, Streamlit config)

## Runtime

**Environment:**
- Python 3.9.6 (CPython, Apple Clang 17.0.0)

**Package Manager:**
- pip (26.0)
- Lockfile: None (only `requirements.txt` without pinned versions)

**Virtual Environment:**
- `venv/` - Standard Python venv at project root

## Frameworks

**Core:**
- Streamlit 1.50.0 - Full-stack web UI framework; drives all pages, tabs, widgets, state, caching

**Build/Dev:**
- No build step required - run directly via `streamlit run app.py`

## Key Dependencies

**UI & Visualization:**
- plotly 5.24.1 - Interactive charts (pie charts, bar charts via `plotly.express`)
- pydeck 0.9.1 - Geospatial visualization (installed, not used in `app.py` currently)
- altair 5.5.0 - Declarative charts (Streamlit dependency)
- pillow 11.3.0 - Image handling (Streamlit dependency)

**Data:**
- pandas 2.3.3 - Core dataframe operations throughout `app.py`
- numpy 2.0.2 - Numerical computation (`import numpy as np` in `app.py`)
- pyarrow 21.0.0 - Columnar data format (pandas/Streamlit dependency)

**Finance:**
- yfinance 1.1.0 - Yahoo Finance market data: stock prices, fundamentals, news, cash flow
- pyportfolioopt 1.5.6 (pypfopt) - Mean-Variance portfolio optimization; Efficient Frontier, risk models, expected returns
- scipy 1.13.1 - Scientific computing (pypfopt dependency)
- cvxpy 1.7.5 - Convex optimization solver (pypfopt dependency)

**Google Sheets Integration:**
- st-gsheets-connection 0.1.0 - Streamlit native connector for Google Sheets
- gspread 5.12.4 - Google Sheets Python API client
- gspread-pandas 3.3.0 - Pandas integration for gspread
- gspread-dataframe 4.0.0 - DataFrame read/write for gspread
- google-auth 2.48.0 - Google OAuth2 authentication
- google-auth-oauthlib 1.2.4 - OAuth2 flow for Google APIs

**Networking:**
- requests 2.32.5 - HTTP client
- curl-cffi 0.13.0 - cURL bindings (yfinance dependency for browser impersonation)
- cryptography 46.0.4 - Cryptographic primitives

**Storage/DB (installed, not used in app.py):**
- duckdb 1.4.4 - Embedded analytical database
- peewee 3.19.0 - Lightweight ORM

## Configuration

**Environment:**
- Secrets stored in `.streamlit/secrets.toml` (never commit this file)
- Required: Google Sheets service account credentials (JSON key) and sheet URL
- Streamlit reads secrets automatically from `.streamlit/secrets.toml` at runtime

**Run Command:**
```bash
streamlit run app.py
```

**Caching:**
- `@st.cache_data(ttl=300)` used on `get_portfolio_performance`, `get_financial_data`, `scan_market_opportunities`
- Cache cleared on "Refresh Portfolio" button click via `st.cache_data.clear()`

## Platform Requirements

**Development:**
- Python 3.9+
- Active internet connection (yfinance requires Yahoo Finance API access)
- Google Cloud service account with Sheets API enabled

**Production:**
- Compatible with Streamlit Community Cloud (reads secrets from platform secrets manager)
- No containerization config present (no Dockerfile, docker-compose.yml)
- `requirements.txt` present but without pinned versions - may cause version drift

---

*Stack analysis: 2026-02-18*
