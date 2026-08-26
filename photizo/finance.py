"""
photizo.finance — Pure financial calculation functions.

No Streamlit, no yfinance, no network I/O.  Fully unit-testable.
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# DCF valuation
# ---------------------------------------------------------------------------

def calculate_dcf(
    fcf: float,
    shares: float,
    growth: float,
    discount: float,
    terminal_growth: float = 0.03,
) -> float:
    """Compute a 5-year DCF intrinsic value per share.

    Args:
        fcf:            Free cash flow (most recent year, dollars).
        shares:         Shares outstanding.
        growth:         Annual FCF growth rate (e.g. 0.12 for 12 %).
        discount:       Discount / hurdle rate (e.g. 0.10 for 10 %).
        terminal_growth: Perpetuity growth rate after year 5 (default 3 %).

    Returns:
        Intrinsic value per share (float), or 0.0 if inputs are invalid.
    """
    if shares == 0 or fcf == 0:
        return 0.0
    future_cash_flows = [
        fcf * ((1 + growth) ** i) / ((1 + discount) ** i)
        for i in range(1, 6)
    ]
    terminal_val = (
        fcf * ((1 + growth) ** 5) * (1 + terminal_growth)
    ) / (discount - terminal_growth)
    intrinsic = (
        sum(future_cash_flows) + terminal_val / ((1 + discount) ** 5)
    ) / shares
    return round(intrinsic, 2)


def smart_discount_rate(beta: float) -> float:
    """Derive a beta-adjusted discount rate clamped to [6 %, 15 %].

    Formula: base 4.2 % + beta × 5.5 %.
    """
    return float(max(0.06, min(0.042 + beta * 0.055, 0.15)))


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def validate_ticker(ticker: str) -> str:
    """Sanitize a ticker string: strip, uppercase, validate A-Z (1-5 chars).

    Raises:
        ValueError: if the ticker fails format validation.
    """
    ticker = ticker.strip().upper()
    if not re.match(r"^[A-Z]{1,5}$", ticker):
        raise ValueError(
            f"Invalid ticker '{ticker}'. Expected 1-5 uppercase letters (e.g. AAPL)."
        )
    return ticker
