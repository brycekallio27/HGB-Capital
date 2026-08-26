# Codebase Concerns

**Analysis Date:** 2026-08-25 (supersedes 2026-02-18 audit — most of that
audit's findings are fixed; see `TASKS.md` for what and when)

## Still True

**`app.py` is large (~1,500 lines) despite the `photizo/` split:**
- Issue: Financial logic and CSS moved into `photizo/*.py` modules, but `app.py` itself still carries auth-gate wiring, all four workspace tabs' UI assembly, and page-level state — it grew rather than shrank as features were added (allocation dashboard, watchlist, radar, Clerk auth).
- Fix approach: If it keeps growing, split per-workspace rendering into `photizo/ui_*.py` modules the way `watchlist.py`/`allocation.py` already own their domain logic.

**`sentiment.py` has zero test coverage:**
- Issue: Keyword-based sentiment scoring feeds the News Cross-Check risk flags partners see — untested despite being decision-relevant.
- Fix approach: Unit tests for `score_news_items()` covering the risk-flag keyword list (lawsuit, investigation, SEC probe, downgrade) and neutral/no-match cases.

**Sentiment is a keyword lexicon, not a model:**
- Issue: Fast and zero-dependency, but will miss nuance and can false-positive on keyword coincidence.
- Fix approach: Wire a hosted model (Anthropic/OpenAI) into `photizo/sentiment.py` if signal quality becomes a problem in practice. Documented as an open follow-up in `PARTNER_NOTES.md`.

**Google Sheets as single point of failure:**
- Issue: `st.connection("gsheets", ...)` failure calls `st.stop()` immediately — the whole app goes down even for tabs that don't need Sheets (e.g. Analysis Lab's market scanner).
- Fix approach: Catch the connection error gracefully; let Sheets-independent tabs still render.

**yfinance is an unofficial scraper:**
- Issue: Not an official API; breaks without notice on Yahoo layout changes. No sentinel/health check exists to detect breakage early.
- Fix approach: A lightweight startup check against a known ticker (e.g. confirm `AAPL` returns expected fields) would surface breakage faster than silent empty data.

**DCF doesn't warn on negative FCF:**
- Issue: Growth companies with negative free cash flow produce a negative "intrinsic value" displayed as if meaningful, no warning shown.
- Fix approach: Explicit check + `st.warning()` when FCF < 0.

**PyPortfolioOpt dependency risk:**
- Issue: Relatively niche library (import name `pypfopt`, PyPI package `PyPortfolioOpt` — this mismatch already caused a broken `requirements.txt`, fixed 2026-08-25). Requires `scikit-learn` transitively; API can shift between versions.
- Fix approach: Version-pin exactly; consider a from-scratch numpy mean-variance implementation if the dependency becomes a recurring source of breakage.

## Fixed Since Last Audit (2026-02-18 → 2026-08-25)

Bare `except` clauses, DataFrame mutation-in-place, division-by-zero on NaN, ticker input validation, watchlist CSV-injection sanitization, sequential per-ticker HTTP calls (now parallelized), duplicate Google Sheets reads, unpinned dependencies, and the "no real auth" gap (fake partner selectbox → Clerk email/password + 2FA) are all resolved. See `TASKS.md` for the full done log.

## Scaling Limits (unchanged)

**Google Sheets as database:** fine under ~1,000 rows; no indexing, no transactions. Migration path if it becomes a bottleneck: SQLite locally / Supabase hosted for transaction history or multi-portfolio tracking.

---

*Concerns audit: 2026-08-25*
