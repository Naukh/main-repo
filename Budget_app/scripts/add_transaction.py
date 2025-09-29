#!/usr/bin/env python3
"""
Add a budget or expense row to a month CSV.

Examples:
  # add an expense
  python add_transaction.py --month 2025-08 --date 2025-08-05 --category Groceries --description "Milk" --actual 4.5

  # add a budget line
  python add_transaction.py --month 2025-08 --entrytype budget --category Groceries --description "Monthly groceries" --budgeted 400
"""
import argparse
import os
import pandas as pd
from datetime import datetime

COLUMNS = [
    "EntryType","Date","Category","Subcategory",
    "Description","Budgeted","Actual","Income","Account","Notes"
]


def ensure_file(path):
    if not os.path.exists(path):
        # create a file with header
        pd.DataFrame(columns=COLUMNS).to_csv(path, index=False)
        print(f"[i] Created new month file: {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--month", required=True, help="YYYY-MM")
    parser.add_argument("-e", "--entrytype", choices=["budget","expense","income"], default=None, help="Type of entry")
    parser.add_argument("-t", "--date", help="YYYY-MM-DD (for expenses). Defaults to today for expenses.")
    parser.add_argument("-c", "--category", required=True)
    parser.add_argument("-s", "--subcategory", default="")
    parser.add_argument("-desc", "--description", default="")
    parser.add_argument("-b", "--budgeted", type=float, default=None)
    parser.add_argument("-a", "--actual", type=float, default=None)
    parser.add_argument("-acc", "--account", default="")
    parser.add_argument("-n", "--notes", default="")
    parser.add_argument("-d", "--data-dir", default="../data")
    args = parser.parse_args()

    path = os.path.join(args.data_dir, f"{args.month}.csv")
    os.makedirs(args.data_dir, exist_ok=True)
    ensure_file(path)

    # Decide entry type if not provided
    entrytype = args.entrytype
    if entrytype is None:
        if args.budgeted is not None and args.actual is None:
            entrytype = "budget"
        elif args.income is not None:
            entrytype = "income"
        else:
            entrytype = "expense"


    date_val = args.date or (datetime.today().strftime("%Y-%m-%d") if entrytype == "expense" else "")

    new_row = {
    "EntryType": entrytype,
    "Date": date_val,
    "Category": args.category,
    "Subcategory": args.subcategory,
    "Description": args.description,
    "Budgeted": args.budgeted if args.budgeted is not None else "",
    "Actual": args.actual if args.actual is not None else "",
    "Account": args.account,
    "Notes": args.notes
    }

    # Read CSV with encoding fallback
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp1252")

    # Append row safely
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[+] Appended row to {path}")

if __name__ == "__main__":
    main()
