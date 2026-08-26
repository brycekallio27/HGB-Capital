import pytest

from photizo.allocation import (
    asset_class_breakdown,
    rebalance_recommendation,
    risk_adjusted_score,
    sleeve_breakdown,
    universe_tickers,
)


def test_universe_includes_bond_sleeves_and_extra_tickers_once():
    tickers = universe_tickers(["AAPL", "QQQ"])

    assert "TLT" in tickers
    assert "LQD" in tickers
    assert "TIP" in tickers
    assert "AAPL" in tickers
    assert tickers.count("QQQ") == 1


def test_asset_and_sleeve_breakdowns_classify_bonds_and_equities():
    weights = {"QQQ": 0.40, "XLV": 0.20, "TLT": 0.25, "LQD": 0.15}

    asset_mix = asset_class_breakdown(weights)
    sleeve_mix = sleeve_breakdown(weights)

    assert asset_mix["equity"] == pytest.approx(0.60)
    assert asset_mix["bond"] == pytest.approx(0.40)
    assert sleeve_mix["tech"] == pytest.approx(0.40)
    assert sleeve_mix["treasuries"] == pytest.approx(0.25)
    assert sleeve_mix["ig_corporates"] == pytest.approx(0.15)


def test_rebalance_recommendation_outputs_buy_sell_hold_actions():
    df = rebalance_recommendation(
        current_weights={"QQQ": 0.70, "TLT": 0.30},
        target_weights={"QQQ": 0.50, "TLT": 0.35, "XLV": 0.15},
        total_equity=100_000,
        threshold=0.01,
    )
    actions = dict(zip(df["Ticker"], df["Action"]))
    dollars = dict(zip(df["Ticker"], df["Dollar Amount"]))

    assert actions["QQQ"] == "Sell"
    assert actions["TLT"] == "Buy"
    assert actions["XLV"] == "Buy"
    assert dollars["QQQ"] == pytest.approx(-20_000)
    assert dollars["XLV"] == pytest.approx(15_000)


def test_risk_adjusted_score_labels_relative_to_sp500():
    strong = risk_adjusted_score(0.12, 0.12)
    weak = risk_adjusted_score(0.04, 0.12)

    assert strong["label"] == "Beats S&P"
    assert weak["label"] == "Lags S&P"
