"""
photizo.radar — thesis-driven market radar helpers.

The radar starts from a theme/anchor/company thesis and builds a candidate
universe that partners can filter before running live yfinance checks.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class RadarTheme:
    label: str
    description: str
    tickers: tuple[str, ...]


RADAR_THEMES: dict[str, RadarTheme] = {
    "ai_compute": RadarTheme(
        label="AI Compute / NVIDIA Ecosystem",
        description="Semiconductors, foundries, memory, equipment, networking, and AI infrastructure.",
        tickers=("NVDA", "TSM", "ASML", "AMAT", "LRCX", "KLAC", "AVGO", "AMD", "MU", "MRVL", "SMH", "QQQ"),
    ),
    "glp1": RadarTheme(
        label="GLP-1 / Metabolic Health",
        description="Large-cap obesity/diabetes leaders, challengers, suppliers, and healthcare ETFs.",
        tickers=("LLY", "NVO", "AMGN", "PFE", "MRK", "REGN", "VRTX", "VKTX", "GPCR", "XLV", "IBB"),
    ),
    "infrastructure": RadarTheme(
        label="Infrastructure / Electrification",
        description="Grid, industrial automation, engineering, construction materials, and infrastructure ETFs.",
        tickers=("PAVE", "IFRA", "IGF", "ETN", "EMR", "URI", "CAT", "VMC", "MLM", "J", "GEV", "XLI"),
    ),
    "healthcare_quality": RadarTheme(
        label="Healthcare Quality",
        description="Profitable healthcare leaders, medtech, insurers, and defensive healthcare ETFs.",
        tickers=("UNH", "JNJ", "ABT", "TMO", "ISRG", "SYK", "DHR", "BSX", "XLV", "VHT"),
    ),
    "broad_etfs": RadarTheme(
        label="ETF Core / Risk Balancers",
        description="Broad market, international, sector, Treasury, corporate bond, and TIPS funds.",
        tickers=("SPY", "VTI", "QQQ", "VXUS", "XLK", "XLV", "PAVE", "TLT", "IEF", "SHY", "LQD", "TIP"),
    ),
}


ANCHOR_RELATED: dict[str, tuple[str, ...]] = {
    "NVDA": ("TSM", "ASML", "AMAT", "LRCX", "KLAC", "AVGO", "AMD", "MU", "MRVL", "SMH"),
    "LLY": ("NVO", "AMGN", "PFE", "MRK", "REGN", "VRTX", "VKTX", "GPCR", "XLV", "IBB"),
    "NVO": ("LLY", "AMGN", "PFE", "MRK", "VKTX", "GPCR", "XLV", "IBB"),
    "TSM": ("NVDA", "ASML", "AMAT", "LRCX", "KLAC", "AVGO", "AMD", "SMH"),
}


def parse_ticker_list(raw: str) -> list[str]:
    """Parse comma/newline/space separated tickers into uppercase uniques."""
    if not raw:
        return []
    normalized = raw.replace(",", "\n").replace(" ", "\n")
    out: list[str] = []
    for token in normalized.splitlines():
        ticker = token.strip().upper()
        if ticker and ticker not in out:
            out.append(ticker)
    return out


def build_radar_universe(
    *,
    theme_keys: list[str],
    anchor_ticker: str = "",
    custom_tickers: list[str] | None = None,
) -> list[str]:
    """Build a deduplicated candidate universe from themes, anchor, and custom ideas."""
    out: list[str] = []

    for key in theme_keys:
        theme = RADAR_THEMES.get(key)
        if not theme:
            continue
        out.extend(theme.tickers)

    anchor = anchor_ticker.strip().upper()
    if anchor:
        out.append(anchor)
        out.extend(ANCHOR_RELATED.get(anchor, ()))

    if custom_tickers:
        out.extend(t.strip().upper() for t in custom_tickers if t.strip())

    deduped: list[str] = []
    for ticker in out:
        if ticker and ticker not in deduped:
            deduped.append(ticker)
    return deduped


def _passes_sector_filter(sector: str, selected_sectors: list[str]) -> bool:
    if not selected_sectors:
        return True
    return sector in selected_sectors


def _coerce_float(value) -> float | None:
    """Best-effort conversion to float. Returns None on any failure.

    yfinance occasionally returns non-numeric values like 'Infinity', '',
    or string-formatted numbers for fields like trailingPE / marketCap.
    """
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    # Reject inf / nan — Styler can't format these cleanly anyway
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def scan_radar_candidates(
    tickers: list[str],
    *,
    min_discount_pct: float = 0.0,
    max_pe: float | None = None,
    min_growth_pct: float | None = None,
    selected_sectors: list[str] | None = None,
    max_results: int = 25,
) -> pd.DataFrame:
    """Fetch yfinance metadata and rank candidates against partner filters."""
    selected_sectors = selected_sectors or []
    rows = []

    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            continue

        price = _coerce_float(
            info.get("currentPrice") or info.get("regularMarketPrice")
        )
        high_52 = _coerce_float(info.get("fiftyTwoWeekHigh")) or 0.0
        pe = _coerce_float(info.get("trailingPE"))
        forward_pe = _coerce_float(info.get("forwardPE"))
        growth = _coerce_float(info.get("earningsGrowth"))
        sector = info.get("sector") or "ETF / Fund"
        name = info.get("shortName") or info.get("longName") or ticker
        beta = _coerce_float(info.get("beta"))
        market_cap = _coerce_float(info.get("marketCap"))

        if not price:
            continue

        discount = ((high_52 - price) / high_52 * 100) if high_52 else 0.0
        pe_for_filter = pe if pe is not None else forward_pe
        growth_pct = growth * 100 if growth is not None else None

        if discount < min_discount_pct:
            continue
        if max_pe is not None and pe_for_filter is not None and pe_for_filter > max_pe:
            continue
        if min_growth_pct is not None and growth_pct is not None and growth_pct < min_growth_pct:
            continue
        if not _passes_sector_filter(sector, selected_sectors):
            continue

        value_score = 0.0
        value_score += min(max(discount, 0), 50) * 1.2
        if pe_for_filter and pe_for_filter > 0:
            value_score += max(0, 35 - min(pe_for_filter, 35))
        if growth_pct:
            value_score += min(max(growth_pct, -20), 40) * 0.6
        if beta and beta > 1.5:
            value_score -= (beta - 1.5) * 8

        rows.append({
            "Ticker": ticker,
            "Company": name,
            "Sector": sector,
            "Price": price,
            "52W Discount": discount,
            "P/E": pe,
            "Forward P/E": forward_pe,
            "Earnings Growth": growth_pct,
            "Beta": beta,
            "Market Cap": market_cap,
            "Radar Score": value_score,
        })

    if not rows:
        return pd.DataFrame(columns=[
            "Ticker", "Company", "Sector", "Price", "52W Discount", "P/E",
            "Forward P/E", "Earnings Growth", "Beta", "Market Cap", "Radar Score",
        ])

    return (
        pd.DataFrame(rows)
        .sort_values("Radar Score", ascending=False)
        .head(max_results)
        .reset_index(drop=True)
    )
