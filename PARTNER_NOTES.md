# HGB Capital · Project Photizo — Partner Notes

_Last updated: 2026-08-25_

This doc explains what changed in the two big upgrades and how each of us
(Bryce, Hunter, Grayson) should think about using the platform now.

---

## 1. Authentication & shared watchlist

### How auth works now

- Sign-in is real email/password (+ two-factor) through **Clerk**, not a
  shared PIN. You land on the HGB portal page first, sign in there, and get
  redirected into the dashboard already authenticated — there's no separate
  login step inside the dashboard itself.
- Each of us signs in with our own email. The dashboard verifies Clerk's
  session token server-side and matches it against our `[partners.*].email`
  entries in `secrets.toml` — no partner can impersonate another, and there
  is no PIN fallback of any kind anymore (it was removed entirely; it's not
  hidden behind a flag, the code is gone).
- If you ever get locked out, it's a Clerk-side password reset / 2FA
  recovery, same as any normal account — there's no separate "app password"
  to remember.

### How the team watchlist works now

The watchlist is shared but ownership is enforced per row.

- Everyone can **see** every entry.
- Only the **original adder** can edit or delete their own row. The check
  is in `photizo/watchlist.py → can_modify()`.
- Anyone can **star** any row independently. Stars are stored per-partner
  in a comma-separated `Stars` column so we don't overwrite each other.
- The display shows an **Owner** column with each partner's display name
  and a `You?` ✓ column so you can spot your own entries at a glance.

### Legacy "Partner A" cleanup

Old test rows owned by `Partner A` (or any non-HGB owner) are tagged as
`Legacy: …` in the UI. In the **Team Watchlist** workspace you'll see two
admin buttons whenever legacy rows exist:

- **Claim Legacy Entries** — assigns them to whoever is signed in.
- **Delete Legacy Entries** — removes the test rows.

This is intentionally separate from the normal ownership rules so we
could clean up the test data without breaking the rule that one partner
cannot delete another's real entries.

---

## 2. Analytics revamp — from "gimmicky" to decision-driven

The old Portfolio Optimizer tab was generic Mean-Variance with three
strategy buttons (Max Sharpe / Min Vol / Target Return) and no bond
exposure. That has been replaced.

### The new Allocation Dashboard

Workspace: **Allocation Dashboard** (top nav).

**Mandates** — three preset risk profiles defined in
`photizo/allocation.py`:

| Profile | Target Return | Vol Ceiling | Equity Lean | Bond Lean |
|---|---|---|---|---|
| Balanced Growth (default) | ~9% | <14% | 60-75% | 25-40% |
| Aggressive Growth | ~12% | <20% | 85-100% | 0-15% |
| Conservative Income | ~6% | <9% | 25-50% | 50-75% |

**Sleeves** — every profile has min/max weight caps per sleeve so the
optimizer can't dump 100% into one ETF. The investable universe:

- **Equities**: Tech (XLK, QQQ, VGT, SMH), Healthcare (XLV, IBB, VHT),
  Infrastructure (PAVE, IFRA, IGF), Broad ETFs (VTI, SPY, VXUS).
- **Bonds**: US Treasuries (TLT, IEF, SHY), IG Corporates (LQD, VCIT),
  TIPS (TIP, SCHP).

You can also drop in any extra tickers we want to consider (e.g.
positions already in the portfolio) and they get blended in.

**What you see after running it**:

1. **KPI strip** — Expected Return, Volatility, Sharpe (with a one-word
   "Beats S&P / In Line / Lags S&P" badge), and the **Bond Sleeve %**.
2. **Allocation chart** — horizontal weights, gold-themed.
3. **Asset Mix** + **Sleeve Exposure** tables — confirm the equity/bond
   split and where the exposure is concentrated.
4. **Rebalance Delta vs Current Portfolio** — buy/sell column with
   dollar amounts based on current equity, so we know exactly what
   trades close the gap.
5. **News Cross-Check** — per-ticker sentiment label (positive/neutral/
   negative) computed from the same yfinance + Google News + SEC EDGAR
   feed used elsewhere in the app, with any **Risk Flags** (lawsuit,
   investigation, SEC probe, downgrade, etc.) called out by name. This
   is the news cross-reference layer Bryce asked for.

### Bonds — finally first-class

The portfolio data model now treats bond ETFs as a separate **asset
class**, not an afterthought. `asset_class_breakdown()` reports the
exact equity/bond split, every profile has a bond sleeve cap, and the
News Cross-Check works for bond ETFs the same way it works for stocks.

### Thesis-driven Market Radar (Analysis Lab)

Separate from the Allocation Dashboard but worth flagging: the **Market
Radar** in the Analysis Lab is now a thesis-driven filter, not a flat
blue-chip scan. Themes include AI Compute / NVIDIA Ecosystem, GLP-1 /
Metabolic Health, Infrastructure / Electrification, Healthcare Quality,
and ETF Core / Risk Balancers. You can also drop in an **anchor
ticker** (e.g. NVDA pulls in TSM, ASML, AMAT, AVGO, AMD, MU, etc.) and
add custom names. Filters: sector, 52-week discount, max P/E, min
earnings growth. Any radar candidate can be added to the team watchlist
in one click, with the thesis note pre-filled.

### Recent bug fix — Market Radar Styler crash

The radar table was crashing with `ValueError: Unknown format code 'f'
for object of type 'str'` because yfinance sometimes returns
non-numeric junk (e.g. `"Infinity"`, `None`) for fields like P/E and
market cap. Fixed at two layers:

- `photizo/radar.py` — every numeric field from yfinance now goes
  through `_coerce_float()` which returns `None` for any non-finite or
  unparseable value.
- `app.py` — before styling, all numeric columns get
  `pd.to_numeric(errors="coerce")` so anything that slipped through
  becomes `NaN` and `na_rep="--"` renders it cleanly.

---

## How to run locally

The dashboard alone won't let you sign in locally anymore — it only
accepts a verified Clerk token, and Clerk tokens come from the landing app.
Run both:

```
cd "/Users/brycekallio/Documents/Claude Cowork/Coding/HGB Capital"
./venv/bin/python -m streamlit run app.py          # localhost:8501

cd landing
npm run dev                                         # localhost:3000
```

Sign in at `localhost:3000`, which redirects you into the dashboard
already authenticated. Default workspace is Portfolio War Room. Top nav
stays put across reruns (we replaced `st.tabs` with a session-backed
`st.radio` because clicks inside Market Radar were bouncing back to the
Portfolio War Room tab).

---

## Open follow-ups

These aren't done yet — flagged here so we don't lose them:

- **Sentiment lexicon** is a finance-flavored keyword list, not a real
  model. It's fast and zero-dependency but it will miss nuance. If we
  want better signal, the natural next step is to wire in a hosted
  model (Anthropic / OpenAI) called from `photizo/sentiment.py`.
- **News cross-check coverage** is capped at 8 tickers per run to keep
  the page responsive. Bump `max_tickers` in
  `allocation_news_summary()` if we want full coverage.
- **Bond pricing**: the optimizer uses 2y of yfinance price history
  for all assets, including bond ETFs. For Treasuries this is fine,
  but if we ever want true duration-aware bond modeling, we'd need to
  add a yield-curve-driven module rather than rely on price returns.
- **Test coverage**: only `photizo/watchlist.py` and `photizo/radar.py`
  have any tests. Adding tests for `allocation.py` (especially the
  sleeve constraint solver) would be high-value before we trust it
  with real allocations.
