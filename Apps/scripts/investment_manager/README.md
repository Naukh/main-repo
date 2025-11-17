# 💰 Investment Manager (Streamlit App)
---

## 📂 Project Structure
```
investment_manager/
│
├── app.py                     # Main Streamlit app entry point
│
├── data/
│   └── portfolio.db           # SQLite DB to store holdings (auto-connected)
│   └── db_utils.db            # To create DB
│
├── pages/
│   ├── 1_Add_Stock.py         # Add new stock to portfolio
│   ├── 2_Update_Stock.py      # Update stock holdings
│   ├── 3_Add_Dividend.py      # Add dividend payouts
│   ├── 4_View_Dividend.py     # View dividend payouts history
│   ├── 5_Add_Transaction.py   # Buy / sell stock holdings
│   ├── 6_Portfolio_Overview.py# Overview table: stocks, value, P/L
│   └── 7_Reports.py           # Charts & analytics (allocation, gain/loss)
│
├── components/
│   ├── quit_button.py          # Optional: admin-only Quit / Restart
│   └── stock_table.py          # Optional reusable Streamlit table for portfolio
│
├── utils/
│   ├── fetch_prices.py         # Functions to fetch stock prices from yfinance
│   └── calculations.py         # Functions for total value, gain/loss, allocations
│
└── README.md                   # Documentation
```

## Next up
Next suggestions (I can implement for you)

pages/2_Update_Stock.py for sells / editing transactions (I can provide).

pages/3_Add_Dividend.py to add dividends using db_utils.add_dividend.

utils/fetch_prices.py — integrate yfinance or another source to auto-fill price_map.

Add small unit tests for calculations.py (I can scaffold pytest tests).

Add a small migration helper if you later want to import old holdings into transactions.

If you want, I can now:

produce pages/2_Update_Stock.py and pages/3_Add_Dividend.py, or

create quick_init.py file for you to run, or

scaffold utils/fetch_prices.py to auto-fill prices.

## Updated next stage
Want Me to Continue?

To proceed cleanly, I suggest:

✔ Step 1 — I generate the new calculations.py

Containing:

compute_current_shares(symbol)

compute_cost_basis(symbol)

compute_weighted_avg_price(symbol)

compute_total_dividends(symbol)

compute_unrealized_pl(symbol, market_price)

compute_realized_pl(symbol)

✔ Step 2 — We update Portfolio_Overview.py to use calculations

Rewrite overview to be 100% transaction-driven.

✔ Step 3 — Rewrite Add_Dividend.py to be consistent

Use clean logic.

✔ Step 4 — Add sanity checks

(duplicate symbols, bad input, mismatched currencies)

❓ What would you like me to do next?
Option A — Generate the entire new calculations.py
Option B — Rewrite Portfolio_Overview.py first
Option C — Rewrite Add_Dividend.py
Option D — Show you the architecture diagram summarizing everything

Which option?