# 💰 Budget Manager (Streamlit App)

A lightweight, modular personal budgeting application built with **Streamlit** and **SQLite**.  
This tool allows you to record, edit, categorize, summarize, and analyze expenses and income.

---

## 📂 Project Structure
```
budget_manager/
│
├── app.py # Main application entry point
│
├── db/
│ └── budget.db # SQLite database (auto-connected)
│
├── pages/
│ ├── add_entry.py # Add new expense/income entries
│ ├── view_edit.py # Edit & delete rows using table editor
│ ├── summary.py # Summary tables and totals
│
├── components/
│ └── quit_button.py # Admin-only Quit + Restart controls
│
└── README.md # This file
```

Each module is self-contained so the app remains maintainable and easy to extend.

---

## ✨ Features

### ➕ Add Entry
- Add expenses or income
- Create new categories or subcategories dynamically
- Store budgeted vs actual amounts
- Optional notes and account fields

### 📋 View / Edit Entries
- Filter by month, category, subcategory, entry type
- Inline spreadsheet-style editing
- Bulk editing supported
- Delete selected rows
- Uses SQLite as persistent storage

### 📈 Summary
- Monthly totals (income, expenses, net balance)
- Category totals
- Ideal for quick financial overview

### 🔐 Admin Controls (Sidebar)
- Password-protected danger zone
- Quit Streamlit server
- Restart Streamlit server
- Hidden automatically on mobile devices to prevent accidental taps

---

## 🚀 How to Run the App

### 1. Install dependencies
```
pip install streamlit pandas
```
### 2. Start the application

Run the following in the terminal inside the budget_manager/ directory:
```
streamlit run app.py
```

### 3. Access in a browser

Streamlit will print a URL similar to:
```
Local URL: http://localhost:8501
```

### 4. 📱 Using on Mobile (Android/iPhone)

You can access the app on your phone if both devices are on the same Wi-Fi network.

#### Step 1 — Find your computer’s local IP

Windows:
`ipconfig`
looks something like this `IPv4 Address. . . . . . . . . . . : 192.168.1.42`

#### Step 2 — Run Streamlitwith external access enabled:
```
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

#### Step 3 — Open the app on your phone:
In your mobile browser enter:
```
http://<your-ip-address>:8501
```
example `http://192.168.1.42:8501`


## 🛠 Troubleshooting
App reachable on computer but not mobile?

Ensure phone and PC are on the same Wi-Fi network

Temporarily disable firewall or allow Python/Streamlit through it

Try another port:
```
streamlit run app.py --server.port 9000
```

# Online app
The App is deployed online using Streamlit Community Cloud. The git account is already link and app can be accessed by
```
https://naukh-budget-app.streamlit.app/
```