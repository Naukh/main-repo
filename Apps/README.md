# Apps (CSV + Python)

This is a simple apps for tracking budget and mortgage system built in **Python** using plain **CSV files** (no Excel required).  
It replaces a workflow where each month has its own worksheet in Excel and a summary script collects the totals.

## 📂 Project Structure
Apps/
├─ data/ # monthly CSV files (e.g. 2025-08.csv)
├─ templates/ # reusable templates
│ └─ month_template.csv # starting template for new month
├─ scripts/ # main Python scripts
│ ├─ init_month.py
│ └─ summarize.py
│ └─ mortgage_calculation.py
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

2. [summarize_budget](./scripts/summarize_budget.py):
Read all monthly CSV [files](./data/Monthly_budget_file/), aggregate budgets and expenses, and produce summaries.
```
python scripts/summarize_budget.py --data-dir ../data --output-dir ../outputs
```

*Outputs*:
summary_monthly_budget.csv — totals by month & category
summary_monthly_budget.html — same as an HTML table

3. [mortgage_calculator](./scripts/mortgage_calculation.py)
Read the data file for mortgage payment history [Mortgage_payments](./data/Mortgage_data_file/Mortgage_payments.csv) and creates a forecast for mortgage payments based on future contributions.

✅ Safety Tips

Always use ISO date format (YYYY-MM-DD) to avoid confusion.

Don’t forget index=False when saving with pandas — otherwise you’ll get an extra column of numbers.

Keep your categories consistent. A typo like Grocries will create a separate category. Later you can add a categories.json to validate inputs.

Back up the data/ folder regularly — it’s the single source of truth.

## 🚀 Next Steps

Once you’re comfortable with this CSV-based system:

Option 3 → turn this into an interactive GUI or dashboard with [Streamli](https://streamlit.io/)
Option 4 → build a web app (Flask/Django or React) for access from phone and browser.
Option 2 → migrate to SQLite instead of CSV for stronger data integrity and simpler queries.

## Budget using DB SQlite
`streamlit run .\budget_manager.py`
