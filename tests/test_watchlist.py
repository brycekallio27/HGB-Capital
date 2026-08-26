import pandas as pd

from photizo.watchlist import (
    add_row,
    annotate_for_display,
    claim_legacy_rows,
    delete_row,
    filter_starred_by,
    is_legacy_owner,
    normalize_watchlist,
    summary_counts,
    update_row,
)


def test_add_row_records_owner_and_sanitizes_notes():
    df = add_row(
        normalize_watchlist(None),
        ticker="aapl",
        price_at_add=100,
        partner_key="bryce",
        added_at="2026-05-06T00:00:00Z",
        notes="=IMPORTXML()",
    )

    assert df.loc[0, "Ticker"] == "AAPL"
    assert df.loc[0, "Added_By"] == "bryce"
    assert df.loc[0, "Notes"] == "'=IMPORTXML()"


def test_partner_cannot_edit_or_delete_another_partners_row():
    df = add_row(
        normalize_watchlist(None),
        ticker="MSFT",
        price_at_add=200,
        partner_key="alex",
        added_at="2026-05-06T00:00:00Z",
    )

    edited, ok, msg = update_row(
        df,
        row_index=0,
        partner_key="bryce",
        updates={"Status": "Buy"},
    )
    assert ok is False
    assert edited.loc[0, "Status"] == "Watching"
    assert "own" in msg

    deleted, ok, msg = delete_row(df, row_index=0, partner_key="bryce")
    assert ok is False
    assert len(deleted) == 1
    assert "own" in msg


def test_partner_can_star_another_partners_row_without_taking_ownership():
    df = add_row(
        pd.DataFrame(),
        ticker="PAVE",
        price_at_add=40,
        partner_key="alex",
        added_at="2026-05-06T00:00:00Z",
    )

    starred, ok, _ = update_row(
        df,
        row_index=0,
        partner_key="bryce",
        updates={"_star_toggle": True},
    )

    assert ok is True
    assert starred.loc[0, "Added_By"] == "alex"
    assert starred.loc[0, "Stars"] == "bryce"
    assert len(filter_starred_by(starred, "bryce")) == 1


def test_display_annotations_and_summary_counts_are_partner_specific():
    df = normalize_watchlist(None)
    df = add_row(df, ticker="XLV", price_at_add=100, partner_key="bryce", added_at="now")
    df = add_row(df, ticker="TLT", price_at_add=90, partner_key="alex", added_at="now")
    df, _, _ = update_row(df, row_index=1, partner_key="bryce", updates={"_star_toggle": True})

    display = annotate_for_display(df, "bryce", {"bryce": "Bryce", "alex": "Alex"})
    counts = summary_counts(df, ["bryce", "alex"])

    assert display.loc[0, "Owner"] == "Bryce"
    assert display.loc[0, "You?"] == "✓"
    assert display.loc[1, "★"] == "★"
    assert counts["bryce"] == {"owned": 1, "starred": 1}
    assert counts["alex"] == {"owned": 1, "starred": 0}


def test_legacy_partner_a_rows_can_be_claimed_by_real_partner():
    df = normalize_watchlist(pd.DataFrame([{
        "Ticker": "AAPL",
        "Price_At_Add": 100,
        "Added_By": "Partner A",
        "Added_At": "now",
        "Notes": "",
        "Status": "Watching",
        "Stars": "",
    }]))

    assert is_legacy_owner(df.iloc[0], ["bryce", "hunter", "grayson"]) is True

    claimed_df, claimed = claim_legacy_rows(
        df,
        row_indices=[0],
        partner_key="bryce",
        valid_partner_keys=["bryce", "hunter", "grayson"],
    )

    assert claimed == 1
    assert claimed_df.loc[0, "Added_By"] == "bryce"


def test_claim_legacy_rows_does_not_take_real_partner_rows():
    df = add_row(
        normalize_watchlist(None),
        ticker="MSFT",
        price_at_add=200,
        partner_key="hunter",
        added_at="now",
    )

    claimed_df, claimed = claim_legacy_rows(
        df,
        row_indices=[0],
        partner_key="bryce",
        valid_partner_keys=["bryce", "hunter", "grayson"],
    )

    assert claimed == 0
    assert claimed_df.loc[0, "Added_By"] == "hunter"
