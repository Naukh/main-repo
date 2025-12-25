# pages/2_Update_Stock.py

import streamlit as st
from data.db_utils import  (
    get_holdings,
    update_holding_symbol_currency,
    get_transactions,
    update_transaction_symbol,
    get_dividends,
    update_dividend_symbol,
    delete_holding
)

st.title("📝 Update Stock")

# --- Load holdings ---
holdings = get_holdings()
if not holdings:
    st.info("No stocks to update. Add holdings first.")
    st.stop()

# Select holding to update
symbols = [h["symbol"] for h in holdings]
selected_symbol = st.selectbox("Select stock to update", symbols)
holding = next(h for h in holdings if h["symbol"] == selected_symbol)

st.subheader(f"Update {selected_symbol}")

# --- Edit fields ---
with st.form("update_stock_form"):
    new_symbol = st.text_input("Symbol", value=holding["symbol"])
    new_currency = st.selectbox(
        "Currency",
        ["PKR", "SEK", "USD", "EUR"],
        index=["PKR", "SEK", "USD", "EUR"].index(holding.get("currency", "USD"))
    )
    new_asset_type = st.selectbox(
        "Asset Type",
        ["stock", "index_fund"],
        index=["stock", "index_fund"].index(holding.get("asset_type", "stock"))
    )
    fund_type_options = ["", "growth", "income"]
    current_fund_type = holding.get("fund_type") or ""  # fallback if None or missing
    if current_fund_type not in fund_type_options:
        current_fund_type = ""  # default to empty if DB has invalid value

    new_fund_type = st.selectbox(
        "Fund Type (for index funds only)",
        fund_type_options,
        index=fund_type_options.index(current_fund_type)
    )
    new_notes = st.text_area("Notes / Comments (optional)", value=holding.get("notes", ""))

    submitted = st.form_submit_button("Update Stock")
    if submitted:
        # --- Update holding in DB ---
        success_holding = update_holding_symbol_currency(
            holding_id=holding["id"],
            new_symbol=new_symbol,
            new_currency=new_currency,
            notes=new_notes,
            asset_type=new_asset_type,
            fund_type=new_fund_type
        )

        # Update all transactions with this symbol
        txs = get_transactions()
        txs_to_update = [t for t in txs if t["symbol"] == selected_symbol]
        tx_success = True
        for tx in txs_to_update:
            if not update_transaction_symbol(tx["id"], new_symbol):
                tx_success = False

        # Update all dividends with this symbol
        divs = get_dividends(selected_symbol)
        div_success = True
        for div in divs:
            if not update_dividend_symbol(div["id"], new_symbol):
                div_success = False

        if success_holding and tx_success and div_success:
            st.success(f"Stock '{selected_symbol}' updated to '{new_symbol}' with currency {new_currency}.")
            st.rerun()
        else:
            st.error("Failed to update all records. Check logs for details.")


# Delete a holding/fund
st.subheader("Remove Stock/Fund from Portfolio")

# List of symbols for selection
symbols_for_delete = [h["symbol"] for h in holdings]
selected_to_delete = st.selectbox("Select symbol to remove", symbols_for_delete)

# Preview selected holding
holding_to_preview = next(h for h in holdings if h["symbol"] == selected_to_delete)
st.write("### Selected Holding Details")
preview_data = {
    "Attribute": ["Symbol", "Asset Type", "Fund Type", "Currency", "Notes", "Current Price"],
    "Value": [
        str(holding_to_preview.get("symbol", "")),
        str(holding_to_preview.get("asset_type", "stock")),
        str(holding_to_preview.get("fund_type", "")),
        str(holding_to_preview.get("currency", "")),
        str(holding_to_preview.get("notes", "")),
        f"{holding_to_preview.get('current_price', 0.0):,.2f}",
    ]
}

st.table(preview_data)

# --- Confirmation checkbox ---
confirm_delete = st.checkbox(f"Confirm deletion of {selected_to_delete}")

# Delete button (only active if checkbox is checked)
if confirm_delete:
    if st.button(f"Delete {selected_to_delete} from portfolio"):
        if delete_holding(selected_to_delete):
            st.success(f"{selected_to_delete} removed successfully!")
            st.rerun()
        else:
            st.error("Failed to remove holding.")

