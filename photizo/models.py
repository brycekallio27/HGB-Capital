"""
photizo.models — financial models and data-fetching helpers.

Pure financial functions live in photizo.finance (no Streamlit dependency).
This module re-exports them for convenience and adds the Streamlit/yfinance
data-fetching functions that require @st.cache_data.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import streamlit as st
import yfinance as yf
from pypfopt import EfficientFrontier, expected_returns, risk_models

# Re-export pure functions from photizo.finance so callers can import from either
from photizo.finance import calculate_dcf, smart_discount_rate, validate_ticker  # noqa: F401


# ---------------------------------------------------------------------------
# Data-fetching functions — require yfinance + Streamlit cache
# ---------------------------------------------------------------------------

# Cash / money-market tickers priced at $1.00 — never passed to yfinance.
CASH_TICKERS = {"CASH", "MMKT", "SPAXX", "FDRXX", "FDIC", "FCASH", "CORE"}


@st.cache_data(ttl=300)
def get_portfolio_performance(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame | None, float, float]:
    """Enrich a raw portfolio DataFrame with market prices, sectors, and P&L.

    Returns:
        (enriched_df, total_equity, total_unrealized_pl)
        or (None, 0, 0) on failure.
    """
    df = df.copy()
    if df.empty:
        return None, 0.0, 0.0

    tickers = df["Ticker"].tolist()
    if not tickers:
        return None, 0.0, 0.0

    cash_mask = df["Ticker"].str.upper().isin(CASH_TICKERS)
    equity_tickers = df[~cash_mask]["Ticker"].tolist()

    df.loc[cash_mask, "Current Price"] = 1.00
    df.loc[cash_mask, "Sector"] = "Cash"

    if equity_tickers:
        try:
            close_data = yf.download(equity_tickers, period="1d", progress=False)["Close"]
        except Exception:
            return df, 0.0, 0.0

        if close_data.empty:
            return df, 0.0, 0.0

        if isinstance(close_data, pd.Series):
            close_data = close_data.to_frame(name=equity_tickers[0])

        current_prices = close_data.iloc[-1]
        df.loc[~cash_mask, "Current Price"] = (
            df.loc[~cash_mask, "Ticker"].map(current_prices)
        )

        def _get_sector(ticker: str) -> str:
            try:
                return yf.Ticker(ticker).info.get("sector", "Unknown")
            except Exception:
                return "Unknown"

        with ThreadPoolExecutor(max_workers=5) as executor:
            sector_map = dict(
                zip(equity_tickers, executor.map(_get_sector, equity_tickers))
            )

        df.loc[~cash_mask, "Sector"] = df.loc[~cash_mask, "Ticker"].map(sector_map)

    df["Market Value"] = df["Shares"] * df["Current Price"]
    if "Cost" not in df.columns:
        df["Cost"] = 0
    df["Total Cost"] = df["Shares"] * df["Cost"]
    df["Unrealized Gain ($)"] = df["Market Value"] - df["Total Cost"]
    df["Return (%)"] = df.apply(
        lambda x: (
            (x["Market Value"] - x["Total Cost"]) / x["Total Cost"] * 100
            if x["Total Cost"] > 0
            else 0
        ),
        axis=1,
    )

    total_equity = float(df["Market Value"].fillna(0).sum())
    total_pl = float(df["Unrealized Gain ($)"].fillna(0).sum())
    return df, total_equity, total_pl


@st.cache_data(ttl=300)
def get_financial_data(ticker: str) -> dict | None:
    """Fetch DCF inputs, financial history, and news for a given ticker.

    Returns a dict with keys: Price, Shares, Beta, FCF, Analyst_Growth,
    Raw_Analyst_Growth, Name, History (DataFrame), News (list).
    Returns None on any failure.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        cashflow = stock.cashflow

        if cashflow.empty:
            return None

        try:
            fcf = cashflow.loc["Free Cash Flow"].iloc[0]
        except KeyError:
            try:
                ocf = cashflow.loc["Operating Cash Flow"].iloc[0]
                capex = cashflow.loc["Capital Expenditure"].iloc[0]
                fcf = ocf + capex
            except KeyError:
                fcf = 0

        raw_analyst_growth = info.get("earningsGrowth", 0.10)
        if raw_analyst_growth is None:
            raw_analyst_growth = 0.08
        analyst_growth = max(0.02, min(raw_analyst_growth, 0.20))

        fin = stock.financials
        history = pd.DataFrame()
        if not fin.empty:
            transposed = fin.T.sort_index(ascending=True)
            if (
                "Total Revenue" in transposed.columns
                and "Net Income" in transposed.columns
            ):
                history["Revenue ($B)"] = transposed["Total Revenue"] / 1e9
                history["Net Income ($B)"] = transposed["Net Income"] / 1e9
                history.index = history.index.strftime("%Y")

        news: list = []
        try:
            news = stock.news[:3]
        except Exception:
            pass

        return {
            "Price": info.get("currentPrice", 0),
            "Shares": info.get("sharesOutstanding", 0),
            "Beta": info.get("beta", 1.0),
            "FCF": fcf,
            "Analyst_Growth": analyst_growth,
            "Raw_Analyst_Growth": raw_analyst_growth,
            "Name": info.get("shortName", ticker),
            "History": history,
            "News": news,
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def scan_market_opportunities() -> pd.DataFrame:
    """Scan 15 blue-chip tickers for >10 % discounts from 52-week high or P/E < 25."""
    watchlist_titans = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META",
        "JPM", "V", "JNJ", "PFE", "KO", "PEP", "XOM", "CVX",
    ]
    opportunities = []
    for ticker in watchlist_titans:
        try:
            info = yf.Ticker(ticker).info
            current = info.get("currentPrice", 0)
            high_52 = info.get("fiftyTwoWeekHigh", 0)
            pe = info.get("trailingPE", 999)
            if current > 0 and high_52 > 0:
                discount = ((high_52 - current) / high_52) * 100
                if discount > 10 or (0 < pe < 25):
                    opportunities.append({
                        "Ticker": ticker,
                        "Price": f"${current}",
                        "Discount": f"-{discount:.1f}%",
                        "P/E": f"{pe:.1f}",
                        "Sector": info.get("sector", "N/A"),
                    })
        except Exception:
            continue
    return pd.DataFrame(opportunities)


def optimize_portfolio(
    tickers: list[str],
    strategy: str,
    target_return: float | None = None,
) -> tuple[dict | None, tuple | None]:
    """Compute optimal portfolio allocation using pypfopt.

    Returns:
        (weights_dict, performance_tuple) or (None, None) on failure.
    """
    prices = yf.download(tickers, period="1y", progress=False)["Close"]
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
