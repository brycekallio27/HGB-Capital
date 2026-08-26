"""
photizo.allocation — risk-aware asset allocation engine.

Builds portfolios across equities, bonds, and sector ETFs using mean-variance
optimization (MPT) with sleeve-level constraints. Designed for HGB Capital's
"Balanced Growth" mandate but supports Aggressive / Conservative profiles too.

Core idea:
  • Universe = equity sleeves (tech / healthcare / infra / broad ETFs / picks)
              + bond sleeves (Treasuries / IG corporates / TIPS)
  • Each sleeve has a target weight band (min, max).
  • MPT optimizer maximises Sharpe ratio inside those bands.
  • Output includes risk-adjusted score and bond/equity split for sanity.

This module is pure Python — no Streamlit imports — so the math is testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns, risk_models
from pypfopt.exceptions import OptimizationError


# ---------------------------------------------------------------------------
# Default sleeve universes
# ---------------------------------------------------------------------------
SLEEVE_UNIVERSE = {
    "tech": {
        "label": "Technology",
        "tickers": ["XLK", "QQQ", "VGT", "SMH"],
        "asset_class": "equity",
    },
    "healthcare": {
        "label": "Healthcare",
        "tickers": ["XLV", "IBB", "VHT"],
        "asset_class": "equity",
    },
    "infrastructure": {
        "label": "Infrastructure",
        "tickers": ["PAVE", "IFRA", "IGF"],
        "asset_class": "equity",
    },
    "broad_etfs": {
        "label": "Broad-Market ETFs",
        "tickers": ["VTI", "SPY", "VXUS"],
        "asset_class": "equity",
    },
    "treasuries": {
        "label": "US Treasuries",
        "tickers": ["TLT", "IEF", "SHY"],
        "asset_class": "bond",
    },
    "ig_corporates": {
        "label": "Investment-Grade Corporates",
        "tickers": ["LQD", "VCIT"],
        "asset_class": "bond",
    },
    "tips": {
        "label": "TIPS (Inflation-Protected)",
        "tickers": ["TIP", "SCHP"],
        "asset_class": "bond",
    },
}


# ---------------------------------------------------------------------------
# Risk profiles → sleeve constraints (min%, max%)
# ---------------------------------------------------------------------------
@dataclass
class SleeveConstraint:
    min_weight: float
    max_weight: float


@dataclass
class RiskProfile:
    name: str
    description: str
    target_return: float           # annual
    target_vol_ceiling: float      # annual
    sleeve_caps: dict[str, SleeveConstraint] = field(default_factory=dict)


PROFILES: dict[str, RiskProfile] = {
    "balanced": RiskProfile(
        name="Balanced Growth",
        description=(
            "Diversified across equities and bonds. Targets ~9% return / "
            "<14% volatility. Aims to beat the S&P risk-adjusted, not "
            "absolute."
        ),
        target_return=0.09,
        target_vol_ceiling=0.14,
        sleeve_caps={
            "tech":           SleeveConstraint(0.10, 0.30),
            "healthcare":     SleeveConstraint(0.05, 0.20),
            "infrastructure": SleeveConstraint(0.05, 0.20),
            "broad_etfs":     SleeveConstraint(0.10, 0.35),
            "treasuries":     SleeveConstraint(0.05, 0.20),
            "ig_corporates":  SleeveConstraint(0.05, 0.15),
            "tips":           SleeveConstraint(0.03, 0.10),
        },
    ),
    "aggressive": RiskProfile(
        name="Aggressive Growth",
        description=(
            "Equity-heavy. Targets ~12% return, willing to tolerate ~18% "
            "volatility. Bond sleeve kept small for opportunistic hedging."
        ),
        target_return=0.12,
        target_vol_ceiling=0.20,
        sleeve_caps={
            "tech":           SleeveConstraint(0.20, 0.45),
            "healthcare":     SleeveConstraint(0.05, 0.20),
            "infrastructure": SleeveConstraint(0.05, 0.20),
            "broad_etfs":     SleeveConstraint(0.10, 0.40),
            "treasuries":     SleeveConstraint(0.00, 0.10),
            "ig_corporates":  SleeveConstraint(0.00, 0.10),
            "tips":           SleeveConstraint(0.00, 0.05),
        },
    ),
    "conservative": RiskProfile(
        name="Conservative Income",
        description=(
            "Bond-heavy with a moderate equity sleeve. Targets ~6% return "
            "with <9% volatility. Designed for capital preservation."
        ),
        target_return=0.06,
        target_vol_ceiling=0.09,
        sleeve_caps={
            "tech":           SleeveConstraint(0.00, 0.15),
            "healthcare":     SleeveConstraint(0.00, 0.10),
            "infrastructure": SleeveConstraint(0.00, 0.10),
            "broad_etfs":     SleeveConstraint(0.05, 0.25),
            "treasuries":     SleeveConstraint(0.20, 0.45),
            "ig_corporates":  SleeveConstraint(0.10, 0.25),
            "tips":           SleeveConstraint(0.05, 0.20),
        },
    ),
}


# ---------------------------------------------------------------------------
# Asset class breakdown
# ---------------------------------------------------------------------------
def asset_class_breakdown(weights: dict[str, float]) -> dict[str, float]:
    """Sum weights into equity / bond / other buckets."""
    ac = {"equity": 0.0, "bond": 0.0, "other": 0.0}
    ticker_to_class: dict[str, str] = {}
    for sleeve in SLEEVE_UNIVERSE.values():
        for t in sleeve["tickers"]:
            ticker_to_class[t] = sleeve["asset_class"]
    for ticker, w in weights.items():
        cls = ticker_to_class.get(ticker, "other")
        ac[cls] += float(w)
    return ac


def sleeve_breakdown(weights: dict[str, float]) -> dict[str, float]:
    """Sum ticker weights up to sleeve weights."""
    ticker_to_sleeve: dict[str, str] = {}
    for sk, sleeve in SLEEVE_UNIVERSE.items():
        for t in sleeve["tickers"]:
            ticker_to_sleeve[t] = sk
    out: dict[str, float] = {}
    for ticker, w in weights.items():
        s = ticker_to_sleeve.get(ticker)
        if s is not None:
            out[s] = out.get(s, 0.0) + float(w)
    return out


# ---------------------------------------------------------------------------
# Risk-adjusted score
# ---------------------------------------------------------------------------
def risk_adjusted_score(
    expected_return: float,
    volatility: float,
    sp500_return: float = 0.10,
    sp500_vol: float = 0.16,
) -> dict:
    """Compute a HGB-house score: Sharpe + S&P-relative info ratio.

    Returns {sharpe, info_ratio, label}.
    `label` is a one-word grade for the partners to glance at.
    """
    sharpe = expected_return / volatility if volatility > 0 else 0.0
    sp_sharpe = sp500_return / sp500_vol if sp500_vol > 0 else 0.0
    info = (expected_return - sp500_return) / volatility if volatility > 0 else 0.0
    if sharpe >= sp_sharpe + 0.10:
        label = "Beats S&P"
    elif sharpe >= sp_sharpe - 0.05:
        label = "In Line"
    else:
        label = "Lags S&P"
    return {"sharpe": sharpe, "info_ratio": info, "label": label}


# ---------------------------------------------------------------------------
# Optimizer with sleeve constraints
# ---------------------------------------------------------------------------
def _build_sleeve_constraint(ef, ticker_list, sleeve_key, bound, sleeve_universe):
    """Add a sleeve weight bound to an EfficientFrontier instance."""
    selector = np.array(
        [1.0 if t in sleeve_universe[sleeve_key]["tickers"] else 0.0
         for t in ticker_list]
    )
    if selector.sum() == 0:
        return  # sleeve has no tickers in the universe
    if bound[0] is not None:
        ef.add_constraint(lambda w, sel=selector, lb=bound[0]: sel @ w >= lb)
    if bound[1] is not None:
        ef.add_constraint(lambda w, sel=selector, ub=bound[1]: sel @ w <= ub)


def optimize_allocation(
    prices: pd.DataFrame,
    profile_key: str = "balanced",
    custom_caps: Optional[dict[str, SleeveConstraint]] = None,
) -> dict:
    """Run a sleeve-constrained MPT optimization on the price panel.

    `prices` is a DataFrame of adjusted close prices, columns = tickers.
    Returns a dict with weights, performance, sleeve breakdown, asset-class
    breakdown, and risk-adjusted score.
    """
    if profile_key not in PROFILES:
        raise ValueError(f"Unknown profile: {profile_key}")
    profile = PROFILES[profile_key]
    caps = custom_caps if custom_caps is not None else profile.sleeve_caps

    if prices.empty or prices.shape[1] < 2:
        raise OptimizationError("Need at least 2 tickers with price data.")

    mu = expected_returns.mean_historical_return(prices)
    S = risk_models.sample_cov(prices)
    ticker_list = list(prices.columns)
    ef = EfficientFrontier(mu, S, weight_bounds=(0.0, 1.0))

    # Apply per-sleeve weight constraints
    for sleeve_key, sc in caps.items():
        if sleeve_key not in SLEEVE_UNIVERSE:
            continue
        _build_sleeve_constraint(
            ef, ticker_list, sleeve_key,
            (sc.min_weight, sc.max_weight),
            SLEEVE_UNIVERSE,
        )

    # Try max Sharpe with constraints; fall back to min vol if infeasible
    try:
        ef.max_sharpe()
    except Exception:
        ef = EfficientFrontier(mu, S, weight_bounds=(0.0, 1.0))
        for sleeve_key, sc in caps.items():
            if sleeve_key not in SLEEVE_UNIVERSE:
                continue
            _build_sleeve_constraint(
                ef, ticker_list, sleeve_key,
                (sc.min_weight, sc.max_weight),
                SLEEVE_UNIVERSE,
            )
        ef.min_volatility()

    weights = ef.clean_weights()
    exp_ret, vol, sharpe = ef.portfolio_performance()
    score = risk_adjusted_score(exp_ret, vol)
    return {
        "profile": profile,
        "weights": dict(weights),
        "expected_return": float(exp_ret),
        "volatility": float(vol),
        "sharpe": float(sharpe),
        "asset_class_breakdown": asset_class_breakdown(weights),
        "sleeve_breakdown": sleeve_breakdown(weights),
        "score": score,
    }


def universe_tickers(extra: Optional[list[str]] = None) -> list[str]:
    """Default investable universe across all sleeves, plus optional extras."""
    out: list[str] = []
    for s in SLEEVE_UNIVERSE.values():
        out.extend(s["tickers"])
    if extra:
        for t in extra:
            t = t.strip().upper()
            if t and t not in out:
                out.append(t)
    return out


# ---------------------------------------------------------------------------
# Compare current portfolio to target
# ---------------------------------------------------------------------------
def rebalance_recommendation(
    current_weights: dict[str, float],
    target_weights: dict[str, float],
    total_equity: float,
    threshold: float = 0.01,
) -> pd.DataFrame:
    """Build a buy/sell delta vs target weights.

    Returns a DataFrame: Ticker, Current Weight, Target Weight, Delta Weight,
    Action, Dollar Amount.
    """
    all_tickers = sorted(set(current_weights) | set(target_weights))
    rows = []
    for t in all_tickers:
        cw = float(current_weights.get(t, 0.0))
        tw = float(target_weights.get(t, 0.0))
        delta = tw - cw
        if abs(delta) < threshold:
            action = "Hold"
        elif delta > 0:
            action = "Buy"
        else:
            action = "Sell"
        rows.append({
            "Ticker": t,
            "Current Weight": cw,
            "Target Weight": tw,
            "Delta Weight": delta,
            "Action": action,
            "Dollar Amount": delta * total_equity,
        })
    df = pd.DataFrame(rows)
    return df.sort_values("Delta Weight", key=abs, ascending=False).reset_index(drop=True)
