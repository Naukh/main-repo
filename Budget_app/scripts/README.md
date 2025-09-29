# Budget Tracker (CSV + Python)

This is a simple budget tracking system built in **Python** using plain **CSV files** (no Excel required).  
It replaces a workflow where each month has its own worksheet in Excel and a summary script collects the totals.

## 📂 Project Structure
Budget_app/
├─ data/ # monthly CSV files (e.g. 2025-08.csv)
├─ templates/ # reusable templates
│ └─ month_template.csv # starting template for new month
├─ scripts/ # main Python scripts
│ ├─ init_month.py
│ ├─ add_transaction.py
│ └─ summarize.py
├─ outputs/ # generated summaries and charts
└─ notebooks/ # optional (playground in Jupyter)

## ⚙️ Setup
1. Create a virtual environment:
```
   python -m venv env
   source env/bin/activate          # Linux / macOS
   .\env\Scripts\Activate.ps1       # Windows
```

2. Install requirements:

```
pip install pandas matplotlib
```

3. (Optional) Install Jyputer:

```
pip install jupyter
```

## Scripts:
1. [init_month.py](./init_month.py):
Create a new CSV file for a month, based on the template.
```
python scripts/init_month.py --month 2025-08
```
This will copy *templates/month_template.csv* into *data/2025-08.csv*.
Use `--force` to overwrite if the file already exists.

2. [add_transactions.py](./add_transaction.py):
Append a budget line or an expense line to a monthly CSV.
# Add an expense
```
python scripts/add_transaction.py --month 2025-08 --date 2025-08-05 --category Groceries --description "Weekly shop" --actual 52.30
```

# Add a budget line
``
python scripts/add_transaction.py --month 2025-08 --entrytype budget --category Utilities --description "Estimated utilities" --budgeted 150
```

If you don’t specify `--entrytype`, the script decides based on whether `--actual` or `--budgeted` is provided.

3. [summarize.py](./summarize.py):
Read all monthly CSVs, aggregate budgets and expenses, and produce summaries.
```
python scripts/summarize.py --data-dir ../data --output-dir ../outputs
```

*Outputs*:
summary_by_category.csv — totals by month & category
summary_by_category.html — same as an HTML table
monthly_totals.png — chart comparing budgeted vs actual per month

✅ Safety Tips

Always use ISO date format (YYYY-MM-DD) to avoid confusion.

Don’t forget index=False when saving with pandas — otherwise you’ll get an extra column of numbers.

Keep your categories consistent. A typo like Grocries will create a separate category. Later you can add a categories.json to validate inputs.

Back up the data/ folder regularly — it’s the single source of truth.

## 🏋️ Exercises (Learning by Doing)

Run the workflow:

Create 2–3 months with init_month.py.

Add some budget and expense rows.

Run summarize.py and open the outputs.

Check correctness:
Open outputs/summary_by_category.csv and verify the numbers by hand.

Add Subcategory support:
Modify summarize.py to group by month, Category, Subcategory.

Filter summaries:
Extend summarize.py to accept --category Groceries and plot a trend just for groceries.

Category validation:
Create a templates/categories.json with allowed categories and modify add_transaction.py to warn if someone enters a new/typo category.

HTML report:
Extend summarize.py to generate a richer HTML report with charts embedded.

## 🚀 Next Steps

Once you’re comfortable with this CSV-based system:

Option 3 → turn this into an interactive GUI or dashboard with [Streamli](https://streamlit.io/)
Option 4 → build a web app (Flask/Django or React) for access from phone and browser.
Option 2 → migrate to SQLite instead of CSV for stronger data integrity and simpler queries.