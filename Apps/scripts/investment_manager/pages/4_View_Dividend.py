# pages/4_View_Dividends.py

import streamlit as st
import pandas as pd
from datetime import datetime
from data.db_utils import get_dividends, update_dividend_record, delete_dividend

st.set_page_config(page_title="Dividend History", layout="wide")
st.title("💰 Dividend History")

# ----------------------------
# Helpers
# ----------------------------
DISPLAY_COLS = ["id", "symbol", "num_shares", "amount_per_share", "tax", "gross_amount", "net_amount", "currency", "date"]

def load_dividends_df():
    rows = get_dividends()
    if not rows:
        return pd.DataFrame(columns=DISPLAY_COLS)
    df = pd.DataFrame(rows)
    # Ensure all expected columns exist
    for c in DISPLAY_COLS:
        if c not in df.columns:
            df[c] = None
    # Numeric conversion
    for c in ["num_shares", "amount_per_share", "tax", "gross_amount", "net_amount"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

def apply_filters(df):
    symbols = sorted(df["symbol"].dropna().unique())
    symbol_choice = st.selectbox("Filter by symbol", ["All"] + symbols, key="div_filter_symbol")
    if symbol_choice != "All":
        df = df[df["symbol"] == symbol_choice]

    min_date = df["date"].min() if not df["date"].isna().all() else pd.Timestamp("2000-01-01")
    max_date = df["date"].max() if not df["date"].isna().all() else pd.Timestamp("2100-01-01")
    col1, col2 = st.columns(2)
    start = col1.date_input("From", min_date.date(), key="div_filter_from")
    end = col2.date_input("To", max_date.date(), key="div_filter_to")
    df = df[(df["date"] >= pd.to_datetime(start)) & (df["date"] <= pd.to_datetime(end))]
    return df, symbol_choice

def totals_summary(df):
    st.metric("Total Gross Dividends", f"{df['gross_amount'].sum():,.2f}")
    st.metric("Total Net Dividends", f"{df['net_amount'].sum():,.2f}")
    st.metric("Total Tax Paid", f"{df['tax'].sum():,.2f}")
    if not df.empty:
        per_sym = df.groupby("symbol").agg(
            gross_amount=("gross_amount", "sum"),
            net_amount=("net_amount", "sum"),
            tax=("tax", "sum"),
            entries=("id", "count")
        ).reset_index().sort_values("net_amount", ascending=False)
        st.subheader("Per-symbol totals")
        st.dataframe(per_sym, width="stretch")
    else:
        st.info("No dividend records to summarize.")

def paginate_df(df, page_size=20):
    total_rows = len(df)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    if "div_page" not in st.session_state:
        st.session_state["div_page"] = 1

    col_prev, col_pageinfo, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("◀ Previous", key="div_prev") and st.session_state["div_page"] > 1:
            st.session_state["div_page"] -= 1
    with col_pageinfo:
        st.write(f"Page {st.session_state['div_page']} of {total_pages} — {total_rows} rows")
    with col_next:
        if st.button("Next ▶", key="div_next") and st.session_state["div_page"] < total_pages:
            st.session_state["div_page"] += 1

    start_idx = (st.session_state["div_page"] - 1) * page_size
    end_idx = start_idx + page_size
    return df.iloc[start_idx:end_idx].copy().reset_index(drop=True)

# ----------------------------
# Load & Filter
# ----------------------------
df_all = load_dividends_df()
if df_all.empty:
    st.info("No dividend records found.")
    st.stop()

with st.expander("🔍 Filters & Options", expanded=False):
    df_filtered, selected_symbol = apply_filters(df_all)

    sort_col = st.selectbox(
        "Sort by",
        options=list(df_filtered.columns),
        index=list(df_filtered.columns).index("date") if "date" in df_filtered.columns else 0,
        key="div_sort_col"
    )
    ascending = st.radio("Order", ["Descending", "Ascending"], horizontal=True, index=0, key="div_sort_order") == "Ascending"
    page_size = st.number_input("Rows per page", min_value=5, max_value=200, value=20, step=5, key="div_page_size")

df_filtered = df_filtered.sort_values(by=sort_col, ascending=ascending).reset_index(drop=True)

# ----------------------------
# Totals summary
# ----------------------------
st.subheader("📊 Totals Summary")
totals_summary(df_filtered)

# ----------------------------
# Download CSV
# ----------------------------
csv_export = df_filtered.copy()
csv_export["date"] = csv_export["date"].dt.strftime("%Y-%m-%d")
st.download_button("📥 Download filtered CSV", data=csv_export.to_csv(index=False), file_name="dividends_filtered.csv", mime="text/csv")

# ----------------------------
# Display paginated table
# ----------------------------
st.subheader("Dividend Records")
page_df = paginate_df(df_filtered)
display_df = page_df[DISPLAY_COLS].copy()
display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
st.dataframe(display_df, width="stretch")

# ----------------------------
# Inline Edit Section
# ----------------------------
st.subheader("✏️ Edit Dividend Entry (Inline)")
available_ids = df_filtered["id"].tolist()
if not available_ids:
    st.info("No entries available to edit.")
else:
    selected_id = st.selectbox("Select Dividend ID to edit", available_ids, key="div_edit_select")
    rec = df_all[df_all["id"] == selected_id].iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        edit_symbol = st.text_input("Symbol", value=rec["symbol"], key=f"edit_symbol_{selected_id}")
        edit_num_shares = st.number_input("Number of shares", min_value=0.0, value=float(rec["num_shares"]), step=0.01, key=f"edit_num_shares_{selected_id}")
    with col2:
        edit_amount = st.number_input("Amount per share", min_value=0.0, value=float(rec["amount_per_share"]), step=0.0001, key=f"edit_amount_{selected_id}")
        edit_tax = st.number_input("Tax", min_value=0.0, value=float(rec["tax"]), step=0.01, key=f"edit_tax_{selected_id}")
    with col3:
        edit_currency = st.text_input("Currency", value=rec.get("currency", ""), key=f"edit_currency_{selected_id}")
        default_date = rec["date"].date() if pd.notna(rec["date"]) else datetime.today().date()
        edit_date = st.date_input("Date", value=default_date, key=f"edit_date_{selected_id}")

    preview_gross = edit_num_shares * edit_amount
    preview_net = preview_gross - edit_tax
    st.info(f"Preview — Gross: {preview_gross:,.2f}  •  Net: {preview_net:,.2f}  •  Currency: {edit_currency}")

    col_u, col_d = st.columns(2)
    with col_u:
        if st.button("Save Changes", key=f"save_div_{selected_id}"):
            success = update_dividend_record(
                div_id=selected_id,
                num_shares=edit_num_shares,
                amount_per_share=edit_amount,
                tax=edit_tax,
                currency=edit_currency,
                date=str(edit_date)
            )
            if success:
                st.success(f"Dividend {selected_id} updated.")
                df_all = load_dividends_df()
                st.rerun()
            else:
                st.error("Update failed. Check logs.")

    with col_d:
        confirm_key = f"del_confirm_{selected_id}"
        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False

        st.session_state[confirm_key] = st.checkbox(f"Confirm delete dividend {selected_id}?", key=f"check_{selected_id}")

        if st.session_state[confirm_key] and st.button("Delete Entry", key=f"del_div_{selected_id}"):
            ok = delete_dividend(selected_id)
            if ok:
                st.success(f"Dividend {selected_id} deleted.")
                st.session_state["div_page"] = 1
                st.session_state[confirm_key] = False
                df_all = load_dividends_df()
                st.rerun()
            else:
                st.error("Delete failed. It may not exist anymore.")

# ----------------------------
# Optional: quick DB preview (admin)
# ----------------------------
with st.expander("⚙️ Raw DB preview (admin)", expanded=False):
    st.write("First 10 rows of dividends (raw):")
    st.dataframe(df_all.head(10), width="stretch")
