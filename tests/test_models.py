"""
tests/test_models.py — Unit tests for pure financial model functions.

Run with:  pytest tests/
"""
import pytest
from photizo.finance import calculate_dcf, smart_discount_rate, validate_ticker


# ---------------------------------------------------------------------------
# calculate_dcf
# ---------------------------------------------------------------------------

class TestCalculateDcf:
    def test_zero_shares_returns_zero(self):
        assert calculate_dcf(fcf=1_000_000, shares=0, growth=0.10, discount=0.10) == 0.0

    def test_zero_fcf_returns_zero(self):
        assert calculate_dcf(fcf=0, shares=1_000_000, growth=0.10, discount=0.10) == 0.0

    def test_positive_fcf_returns_positive(self):
        result = calculate_dcf(fcf=5_000_000_000, shares=1_000_000_000, growth=0.10, discount=0.10)
        assert result > 0

    def test_higher_growth_means_higher_value(self):
        base = calculate_dcf(fcf=1e9, shares=1e8, growth=0.05, discount=0.10)
        high = calculate_dcf(fcf=1e9, shares=1e8, growth=0.15, discount=0.10)
        assert high > base

    def test_higher_discount_means_lower_value(self):
        low_d = calculate_dcf(fcf=1e9, shares=1e8, growth=0.10, discount=0.08)
        high_d = calculate_dcf(fcf=1e9, shares=1e8, growth=0.10, discount=0.15)
        assert low_d > high_d

    def test_returns_float(self):
        result = calculate_dcf(fcf=1e9, shares=1e8, growth=0.10, discount=0.10)
        assert isinstance(result, float)

    def test_custom_terminal_growth(self):
        default = calculate_dcf(fcf=1e9, shares=1e8, growth=0.10, discount=0.10)
        higher_tg = calculate_dcf(fcf=1e9, shares=1e8, growth=0.10, discount=0.10, terminal_growth=0.05)
        assert higher_tg > default

    def test_known_value(self):
        # Single-share, 0 % growth, 10 % discount, 3 % terminal growth:
        # FCF = 1, shares = 1 → verify result is a reasonable positive number
        result = calculate_dcf(fcf=1.0, shares=1.0, growth=0.0, discount=0.10, terminal_growth=0.03)
        assert result > 0
        # With 0% growth and 10% discount, the terminal value dominates
        # Terminal = 1 * 1.03 / (0.10 - 0.03) = 14.71...
        # Discounted 5 years: 14.71 / 1.10^5 ≈ 9.13
        assert 8.0 < result < 20.0


# ---------------------------------------------------------------------------
# smart_discount_rate
# ---------------------------------------------------------------------------

class TestSmartDiscountRate:
    def test_low_beta_clamped_to_floor(self):
        # Very low beta should give floor of 6 %
        assert smart_discount_rate(0.0) == pytest.approx(0.06)

    def test_high_beta_clamped_to_ceiling(self):
        # Very high beta should give ceiling of 15 %
        assert smart_discount_rate(10.0) == pytest.approx(0.15)

    def test_beta_one_in_range(self):
        rate = smart_discount_rate(1.0)
        assert 0.06 <= rate <= 0.15

    def test_higher_beta_higher_rate(self):
        low = smart_discount_rate(0.5)
        high = smart_discount_rate(2.0)
        assert high > low

    def test_returns_float(self):
        assert isinstance(smart_discount_rate(1.0), float)


# ---------------------------------------------------------------------------
# validate_ticker
# ---------------------------------------------------------------------------

class TestValidateTicker:
    def test_valid_ticker_uppercased(self):
        assert validate_ticker("aapl") == "AAPL"

    def test_valid_ticker_already_upper(self):
        assert validate_ticker("MSFT") == "MSFT"

    def test_strips_whitespace(self):
        assert validate_ticker("  NVDA  ") == "NVDA"

    def test_single_letter_valid(self):
        assert validate_ticker("V") == "V"

    def test_five_letters_valid(self):
        assert validate_ticker("GOOGL") == "GOOGL"

    def test_six_letters_raises(self):
        with pytest.raises(ValueError):
            validate_ticker("TOOLNG")

    def test_numbers_raise(self):
        with pytest.raises(ValueError):
            validate_ticker("BRK.B")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            validate_ticker("")

    def test_special_chars_raise(self):
        with pytest.raises(ValueError):
            validate_ticker("AA!")
