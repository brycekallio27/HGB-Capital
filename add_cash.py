"""
add_cash.py — One-time script to add a CASH row to the Portfolio sheet.

Run from the project directory:
    source venv/bin/activate
    python add_cash.py

This appends a single CASH row (Ticker=CASH, Shares=135.97, Cost=1.00)
using the same service account credentials the app already uses.
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import sys

# ── Config ────────────────────────────────────────────────────────────────────

SPREADSHEET_ID = "16-ycJs1kYQ7JfW1_XHkrXg-baD7M47GGLggigm8fOfE"
WORKSHEET_NAME = "Portfolio"

# The service account key lives in the project root (gitignored)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(SCRIPT_DIR, "financegmaildigestkey-12081659191d.json")

CASH_TICKER   = "CASH"
CASH_SHARES   = 135.97   # dollar balance = number of "shares" at $1.00 each
CASH_COST     = 1.00     # cost per share for a money-market / cash position

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # 1. Auth
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: Service account key not found at:\n  {KEY_FILE}")
        sys.exit(1)

    creds = Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)

    # 2. Open sheet
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)

    # 3. Read current data to detect column layout
    data = ws.get_all_values()
    if not data:
        print("ERROR: Portfolio sheet appears empty (no header row found).")
        sys.exit(1)

    headers = [h.strip() for h in data[0]]
    print(f"Detected columns ({len(headers)}): {headers}")

    # 4. Guard: skip if CASH row already exists
    for row in data[1:]:
        if row and row[0].strip().upper() == "CASH":
            print("CASH row already exists in the Portfolio sheet — nothing to do.")
            sys.exit(0)

    # 5. Build the new row, mapping values into the correct columns
    #    Falls back to appending [Ticker, Shares, Cost] if headers are unrecognised.
    ticker_col = next((i for i, h in enumerate(headers) if h.lower() == "ticker"), 0)
    shares_col = next((i for i, h in enumerate(headers) if h.lower() in ("shares", "quantity", "qty")), 1)
    cost_col   = next((i for i, h in enumerate(headers) if h.lower() in ("cost", "cost basis", "avg cost", "price")), 2)

    new_row = [""] * len(headers)
    new_row[ticker_col] = CASH_TICKER
    new_row[shares_col] = CASH_SHARES
    new_row[cost_col]   = CASH_COST

    print(f"\nAbout to append row:")
    for i, val in enumerate(new_row):
        if val != "":
            print(f"  Column {i} ({headers[i]}): {val}")

    # 6. Confirm before writing
    confirm = input("\nWrite this row to Google Sheets? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted — nothing was written.")
        sys.exit(0)

    ws.append_row(new_row, value_input_option="USER_ENTERED")
    print("\n✓ CASH row added successfully.")
    print("  Refresh the app (or wait ~5 min for cache to expire) to see it reflected.")

if __name__ == "__main__":
    main()
