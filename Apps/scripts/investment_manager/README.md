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
│   ├── 7_Add_Index_Fund.py     # To add index funds both growth and income
│   └── 8_Reports.py           # Charts & analytics (allocation, gain/loss)
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
Generate reports