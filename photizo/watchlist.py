"""
photizo.watchlist — per-partner watchlist with ownership enforcement.

Design rules:
  • Every row carries an `Added_By` column (the partner_key, e.g. "bryce").
  • Everyone can READ all rows.
  • A partner can EDIT or DELETE only the rows they themselves added.
  • A partner can STAR rows added by anyone — stars are stored in a separate
    `Stars` column as a comma-separated list of partner_keys, so each partner
    can independently star a row without overwriting another partner's star.

This module is pure data manipulation on pandas DataFrames — no Streamlit
imports — so the ownership logic is fully unit-testable.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd


# Canonical column order. Existing sheets that don't have all columns yet are
# auto-upgraded by `normalize_watchlist`.
WATCHLIST_COLUMNS = [
    "Ticker",
    "Price_At_Add",
    "Added_By",       # partner_key — owner of the row
    "Added_At",       # ISO-8601 timestamp
    "Notes",
    "Status",         # Watching / Researching / Buy / Sell / Closed
    "Stars",          # comma-separated partner_keys who starred this row
]

LEGACY_OWNER_LABELS = {"", "partner a", "partner_a", "test", "demo"}


def normalize_watchlist(df: pd.DataFrame | None) -> pd.DataFrame:
    """Return a watchlist DataFrame with all canonical columns present.

    Adds any missing columns as empty strings. This lets us upgrade older
    sheets in-place without a hard migration.
    """
    if df is None:
        return pd.DataFrame(columns=WATCHLIST_COLUMNS)
    out = df.copy()
    for col in WATCHLIST_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    # Re-order so the canonical columns come first
    extras = [c for c in out.columns if c not in WATCHLIST_COLUMNS]
    return out[WATCHLIST_COLUMNS + extras]


def can_modify(row: pd.Series, partner_key: str) -> bool:
    """Return True iff `partner_key` is allowed to edit/delete this row."""
    owner = str(row.get("Added_By", "")).strip().lower()
    return owner == partner_key.strip().lower()


def is_legacy_owner(row: pd.Series, valid_partner_keys: Iterable[str]) -> bool:
    """Return True for old/test owners that are not real HGB partners."""
    owner = str(row.get("Added_By", "") or "").strip().lower()
    valid = {str(k).strip().lower() for k in valid_partner_keys}
    return owner in LEGACY_OWNER_LABELS or owner not in valid


def claim_legacy_rows(
    df: pd.DataFrame,
    *,
    row_indices: Iterable[int],
    partner_key: str,
    valid_partner_keys: Iterable[str],
) -> tuple[pd.DataFrame, int]:
    """Assign selected legacy/test rows to a real partner.

    Rows already owned by a valid partner are left untouched.
    """
    base = normalize_watchlist(df)
    claimed = 0
    key = partner_key.strip().lower()
    for idx in row_indices:
        if idx < 0 or idx >= len(base):
            continue
        if is_legacy_owner(base.iloc[idx], valid_partner_keys):
            base.at[idx, "Added_By"] = key
            claimed += 1
    return base, claimed


def is_starred_by(row: pd.Series, partner_key: str) -> bool:
    """Return True iff `partner_key` has starred this row."""
    raw = str(row.get("Stars", "") or "")
    starred_set = {s.strip().lower() for s in raw.split(",") if s.strip()}
    return partner_key.strip().lower() in starred_set


def toggle_star(row: pd.Series, partner_key: str) -> str:
    """Toggle a partner's star on a row. Returns the new Stars cell value."""
    raw = str(row.get("Stars", "") or "")
    starred_set = {s.strip().lower() for s in raw.split(",") if s.strip()}
    key = partner_key.strip().lower()
    if key in starred_set:
        starred_set.discard(key)
    else:
        starred_set.add(key)
    return ",".join(sorted(starred_set))


def add_row(
    df: pd.DataFrame,
    *,
    ticker: str,
    price_at_add: float,
    partner_key: str,
    added_at: str,
    notes: str = "",
    status: str = "Watching",
) -> pd.DataFrame:
    """Append a new watchlist row owned by `partner_key`.

    Sanitizes notes against CSV injection by prefixing dangerous leading chars.
    """
    safe_notes = notes or ""
    if safe_notes and safe_notes[0] in ("=", "+", "-", "@"):
        safe_notes = "'" + safe_notes
    new = pd.DataFrame([{
        "Ticker": ticker.strip().upper(),
        "Price_At_Add": float(price_at_add) if price_at_add is not None else 0.0,
        "Added_By": partner_key.strip().lower(),
        "Added_At": added_at,
        "Notes": safe_notes,
        "Status": status,
        "Stars": "",
    }])
    base = normalize_watchlist(df)
    return pd.concat([base, new], ignore_index=True)


def update_row(
    df: pd.DataFrame,
    *,
    row_index: int,
    partner_key: str,
    updates: dict,
) -> tuple[pd.DataFrame, bool, str]:
    """Apply updates to a row only if `partner_key` owns it.

    Returns (new_df, success, message). Star changes are routed through this
    function with `updates={"_star_toggle": True}` and bypass ownership.
    """
    base = normalize_watchlist(df)
    if row_index < 0 or row_index >= len(base):
        return base, False, "Row not found."

    is_star_toggle = updates.get("_star_toggle") is True

    if not is_star_toggle and not can_modify(base.iloc[row_index], partner_key):
        return base, False, "You can only edit your own watchlist entries."

    if is_star_toggle:
        base.at[row_index, "Stars"] = toggle_star(
            base.iloc[row_index], partner_key
        )
        return base, True, "Star toggled."

    # Sanitize Notes against CSV injection
    if "Notes" in updates and updates["Notes"]:
        n = updates["Notes"]
        if n[0] in ("=", "+", "-", "@"):
            updates["Notes"] = "'" + n

    for k, v in updates.items():
        if k in WATCHLIST_COLUMNS and k not in ("Added_By",):
            base.at[row_index, k] = v
    return base, True, "Updated."


def delete_row(
    df: pd.DataFrame,
    *,
    row_index: int,
    partner_key: str,
) -> tuple[pd.DataFrame, bool, str]:
    """Delete a row only if `partner_key` owns it."""
    base = normalize_watchlist(df)
    if row_index < 0 or row_index >= len(base):
        return base, False, "Row not found."
    if not can_modify(base.iloc[row_index], partner_key):
        return base, False, "You can only delete your own watchlist entries."
    new = base.drop(base.index[row_index]).reset_index(drop=True)
    return new, True, "Deleted."


def annotate_for_display(
    df: pd.DataFrame,
    partner_key: str,
    partner_name_lookup: dict,
) -> pd.DataFrame:
    """Add display-only columns: Owner (display name) + You? + ★."""
    base = normalize_watchlist(df).copy()
    valid_keys = set(partner_name_lookup.keys())
    base["Owner"] = base["Added_By"].map(
        lambda k: (
            partner_name_lookup.get(str(k).lower(), str(k))
            if str(k).lower() in valid_keys
            else f"Legacy: {k or 'Unassigned'}"
        )
    )
    base["You?"] = base["Added_By"].map(
        lambda k: "✓" if str(k).lower() == partner_key.lower() else ""
    )
    base["★"] = base.apply(
        lambda r: "★" if is_starred_by(r, partner_key) else "", axis=1
    )
    return base


def filter_starred_by(df: pd.DataFrame, partner_key: str) -> pd.DataFrame:
    """Return only rows starred by `partner_key`."""
    base = normalize_watchlist(df)
    if base.empty:
        return base
    mask = base.apply(lambda r: is_starred_by(r, partner_key), axis=1)
    return base[mask].reset_index(drop=True)


def filter_owned_by(df: pd.DataFrame, partner_key: str) -> pd.DataFrame:
    """Return only rows owned by `partner_key`."""
    base = normalize_watchlist(df)
    if base.empty:
        return base
    mask = base["Added_By"].str.lower() == partner_key.lower()
    return base[mask].reset_index(drop=True)


def summary_counts(df: pd.DataFrame, partner_keys: Iterable[str]) -> dict:
    """Return per-partner counts: {partner_key: {'owned': N, 'starred': M}}."""
    base = normalize_watchlist(df)
    out: dict = {}
    for k in partner_keys:
        out[k] = {
            "owned": int((base["Added_By"].str.lower() == k.lower()).sum()),
            "starred": int(base.apply(lambda r: is_starred_by(r, k), axis=1).sum()),
        }
    return out
