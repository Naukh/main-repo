#!/usr/bin/env python3
"""
Create a new month CSV from the template.
Usage:
  python init_month.py --month 2025-08
"""
import argparse
import os
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--month", required=True, help="Month in YYYY-MM format (e.g. 2025-08)")
    parser.add_argument("-t", "--template", default="../templates/month_template.csv", help="Path to template CSV")
    parser.add_argument("-d", "--data-dir", default="../data", help="Directory to store month CSVs")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite if file exists")
    args = parser.parse_args()

    os.makedirs(args.data_dir, exist_ok=True)
    dest = os.path.join(args.data_dir, f"{args.month}.csv")
    if os.path.exists(dest) and not args.force:
        print(f"[!] {dest} already exists. Use --force to overwrite.")
        return

    try:
        shutil.copyfile(args.template, dest)
        print(f"[+] Created {dest} from template.")
    except Exception as e:
        print("Error creating month file:", e)

if __name__ == "__main__":
    main()
