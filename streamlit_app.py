import streamlit as st
import hashlib
from database import init_db, add_transaction, add_dividend, get_transactions, get_dividends, reset_database
from data_fetcher import fetch_current_price, fetch_company_info, fetch_dividends
from portfolio_engine import weight_avg_cost, unrealized_pl, dividend_income, total_return

# Initialize DB
init_db()

# Password gate (optional, can be removed if you rely on Streamlit secrets)
def check_password():
    def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()
    if "password_correct" not in st.session_state:
        st.subheader("🔐 App access")
        pw = st.text_input("Password", type="password")
        if st.button("Enter"):
            if _hash(pw) == st.secrets.get("app_password_hash", ""):
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        return False
    return True

if not check_password():
    st.stop()

st.set_page_config(page_title="HK Stock Tracker", layout="wide")
st.title("📈 Hong Kong Stock Portfolio Tracker")

menu = st.sidebar.selectbox(
    "Menu",
    ["Portfolio", "Add Transaction", "Add Dividend", "Fetch Dividends", "Reset DB"]
)

if menu == "Portfolio":
    st.header("Your Portfolio")
    txs = get_transactions()
    if not txs:
        st.info("No transactions recorded yet.")
    else:
        # Group by stock
        from collections import defaultdict
        holdings = defaultdict(int)
        for tx in txs:
            holdings[tx[1]] += tx[4]  # quantity
        data = []
        for stock_code, shares in holdings.items():
            price = fetch_current_price(stock_code)
            avg_cost = weight_avg_cost([tx for tx in txs if tx[1]==stock_code])
            market_val = shares * price
            cost_basis = shares * avg_cost
            pl = market_val - cost_basis
            pl_pct = (pl / cost_basis * 100) if cost_basis != 0 else 0
            data.append({
                "Stock": stock_code,
                "Shares": shares,
                "Avg Cost": f"{avg_cost:.2f}",
                "Current Price": f"{price:.2f}",
                "Market Value": f"{market_val:.2f}",
                "P&L": f"{pl:.2f}",
                "P&L %": f"{pl_pct:.2f}%"
            })
        st.dataframe(data)
        # Summary
        total_invest = sum(tx[4]*tx[5] + tx[6] for tx in txs)
        total_market = sum(fetch_current_price(tx[1])*tx[4] for tx in txs)
        total_pl = total_market - total_invest
        st.subheader("Summary")
        st.write(f"Total Invested: HK${total_invest:,.2f}")
        st.write(f"Total Market Value: HK${total_market:,.2f}")
        st.write(f"Total P&L: HK${total_pl:,.2f} ({total_pl/total_invest*100 if total_invest else 0:.2f}%)")

elif menu == "Add Transaction":
    st.header("Add New Transaction")
    with st.form("tx_form"):
        stock_code = st.text_input("Stock Code (e.g., 0700.HK)").upper()
        if stock_code:
            info = fetch_company_info(stock_code)
            default_name = info["company_name"]
        else:
            default_name = ""
        company_name = st.text_input("Company Name", value=default_name)
        tx_date = st.date_input("Transaction Date")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Price per Share (HK$)", min_value=0.0, step=0.01, format="%.2f")
        fees = st.number_input("Fees (HK$)", min_value=0.0, step=0.01, format="%.2f")
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            if not stock_code or quantity <= 0 or price < 0:
                st.error("Please fill in all fields correctly.")
            else:
                add_transaction(
                    stock_code,
                    company_name,
                    tx_date.isoformat(),
                    int(quantity),
                    float(price),
                    float(fees)
                )
                st.success("Transaction added!")
                st.rerun()

elif menu == "Add Dividend":
    st.header("Add Dividend Record")
    with st.form("div_form"):
        stock_code = st.text_input("Stock Code (e.g., 0005.HK)").upper()
        record_date = st.date_input("Record Date")
        payment_date = st.date_input("Payment Date (optional)", value=None)
        div_per_share = st.number_input("Dividend per Share (HK$)", min_value=0.0, step=0.001, format="%.3f")
        submitted = st.form_submit_button("Add Dividend")
        if submitted:
            if not stock_code or div_per_share < 0:
                st.error("Invalid input.")
            else:
                add_dividend(
                    stock_code,
                    record_date.isoformat(),
                    payment_date.isoformat() if payment_date else None,
                    float(div_per_share)
                )
                st.success("Dividend record added!")
                st.rerun()

elif menu == "Fetch Dividends":
    st.header("Fetch Dividends from Yahoo Finance")
    stock_code = st.text_input("Stock Code (e.g., 0700.HK)").upper()
    years = st.number_input("Years Back", min_value=1, max_value=10, value=5, step=1)
    if st.button("Fetch"):
        divs = fetch_dividends(stock_code, int(years))
        if divs:
            st.write(f"Found {len(divs)} dividend records:")
            for d in divs:
                st.write(f"- {d[0]}: HK${d[1]:.3f} per share")
        else:
            st.warning("No dividend data found.")

elif menu == "Reset DB":
    st.header("⚠️ Reset Database")
    st.warning("This will delete all transactions and dividends.")
    if st.button("Yes, reset everything"):
        reset_database()
        st.success("Database reset.")
        st.rerun()
