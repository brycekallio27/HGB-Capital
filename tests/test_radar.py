from photizo.radar import build_radar_universe, parse_ticker_list


def test_parse_ticker_list_accepts_commas_spaces_and_newlines():
    assert parse_ticker_list("nvda, tsm\nASML  nvda") == ["NVDA", "TSM", "ASML"]


def test_build_radar_universe_adds_anchor_related_names_once():
    universe = build_radar_universe(
        theme_keys=["ai_compute"],
        anchor_ticker="NVDA",
        custom_tickers=["TSM", "LLY"],
    )

    assert "NVDA" in universe
    assert "TSM" in universe
    assert "ASML" in universe
    assert "LLY" in universe
    assert universe.count("TSM") == 1


def test_build_radar_universe_supports_glp1_theme():
    universe = build_radar_universe(theme_keys=["glp1"])

    assert "LLY" in universe
    assert "NVO" in universe
    assert "XLV" in universe
