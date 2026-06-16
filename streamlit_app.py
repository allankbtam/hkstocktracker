#!/usr/bin/env python3
"""t('app_title') - Streamlit Dashboard"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import csv
import io

print("DEBUG: Script started")  # DEBUG

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_connection, init_database, reset_database, get_db_path,
    add_transaction, get_transactions, delete_transaction,
    add_dividend, get_dividends, delete_dividend
)
from data_fetcher import fetch_current_price, fetch_dividends, fetch_company_info
from portfolio_engine import get_portfolio_summary, round_currency, calculate_dividend_income



# ===== LANGUAGE SETUP =====
# Initialize language from query params or session state
if "lang" not in st.session_state:
    st.session_state.lang = "en"  # default

# Override with query param if present
try:
    lang_param = st.query_params.get("lang", None)
    if lang_param:
        lang_param = lang_param.upper()
        if lang_param == "EN":
            st.session_state.lang = "en"
        elif lang_param == "ZH-TW":
            st.session_state.lang = "zh-TW"
        # else keep the current session state (which is either default or previously set)
except:
    pass  # Ignore errors in getting query param

# Sync query params with session state (to keep URL updated)
try:
    current_lang = st.session_state.lang
    if "lang" not in st.query_params or st.query_params.get("lang") != current_lang:
        st.query_params["lang"] = current_lang
except:
    pass  # Ignore errors in setting query params
# Translation dictionary
translations = {
    'en': {
        # App title and sidebar
        'app_title': 'HK Stock Tracker',
        'portfolio_dashboard': 'Portfolio Dashboard',
        'add_transaction': 'Add Transaction',
        'add_dividend': 'Add Dividend',
        'view_data': 'View Data',
        'settings': 'Settings',
        'import_csv': 'Import CSV',
        'language': 'Language',
        'menu': 'Menu',
        'english': 'English',
        'traditional_chinese': 'Traditional Chinese',
        
        # Portfolio Dashboard
        'total_invested': 'Total Invested',
        'total_value': 'Total Value',
        'total_return': 'Total Return',
        'dividend_income': 'Dividend Income',
        'current_positions': 'Current Positions',
        'stock': 'Stock',
        'company': 'Company',
        'shares': 'Shares',
        'avg_cost': 'Avg Cost',
        'current_price': 'Current Price',
        'market_value': 'Market Value',
        'unrealized_pl': 'Unrealized P&L',
        'pl_percent': 'P&L %',
        'dividend_received': 'Dividend Received',
        'recent_transactions': 'Recent Transactions',
        'date': 'Date',
        'type': 'Type',
        'price': 'Price',
        'fees': 'Fees',
        'total': 'Total',
        'no_stocks': 'No stocks in portfolio. Add some transactions first.',
        'no_positions': 'No positions to display.',
        'no_transactions': 'No transactions recorded.',
        
        # Add Transaction
        'stock_code': 'Stock Code (e.g., 0700.HK)',
        'company_name': 'Company Name',
        'transaction_date': 'Transaction Date',
        'quantity': 'Quantity (shares)',
        'price_per_share': 'Price per Share (HKD)',
        'fees': 'Fees (HKD)',
        'fetch_company_name': '🔍 Fetch Company Name',
        'transaction_added': 'Transaction added successfully! ID: {}',
        'error_adding_transaction': 'Error adding transaction: {}',
        'please_fill_fields': 'Please fill in all required fields.',
        
        # Add Dividend
        'record_date': 'Record Date',
        'dividend_per_share': 'Dividend per Share (HKD)',
        'payment_date': 'Payment Date (optional)',
        'dividend_added': 'Dividend record added successfully! ID: {}',
        'error_adding_dividend': 'Error adding dividend: {}',
        'please_enter_stock_code': 'Please enter a stock code.',
        
        # View Data
        'all_transactions': 'All Transactions',
        'all_dividends': 'All Dividends',
        'download_transactions': 'Download Transactions as CSV',
        'download_dividends': 'Download Dividends as CSV',
        'no_transactions_found': 'No transactions found.',
        'no_dividends_found': 'No dividends found.',
        'created_at': 'Created At',
        'action': 'Action',
        'delete_tooltip': 'Delete this {}',
        'transaction_deleted': 'Transaction {} deleted.',
        'failed_to_delete_transaction': 'Failed to delete transaction {}.',
        'dividend_deleted': 'Dividend {} deleted.',
        'failed_to_delete_dividend': 'Failed to delete dividend {}.',
        
        # Settings
        'database_operations': 'Database Operations',
        'refresh_data': '🔄 Refresh Data',
        'clear_all_data': '🗑️ Clear All Data',
        'understand_clear': 'I understand this will delete all data',
        'all_data_cleared': 'All data cleared!',
        'about': 'About',
        'app_description': '''**HK Stock Tracker** v1.0.0

A portable, pure-Python application for tracking Hong Kong stock investments.

Features:
- Transaction tracking with cost basis calculation
- Dividend income tracking
- Real-time price fetching via yfinance
- Portfolio performance analytics
- Local SQLite database (no external dependencies)
- Cross-platform compatible (Windows, macOS, Linux)

Built with:
- Python 3.11+
- Streamlit for UI
- yfinance for market data
- SQLite for data storage
''',
        
        # Import CSV
        'import_csv_title': 'Import CSV',
        'import_instructions': 'Import your transaction or dividend records from a CSV file.',
        'select_data_type': 'Select data type to import',
        'transactions': 'Transactions',
        'dividends': 'Dividends',
        'expected_columns_tx': '**Expected CSV columns:**\\n- `date` (YYYY-MM-DD)\\n- `stock_code` (e.g., 0700.HK)\\n- `quantity` (integer, number of shares)\\n- `price_per_share` (numeric, HKD)\\n- `fees` (numeric, HKD, optional)',
        'expected_columns_div': '**Expected CSV columns:**\\n- `stock_code` (e.g., 0700.HK)\\n- `record_date` (YYYY-MM-DD)\\n- `dividend_per_share` (numeric, HKD per share)\\n- `payment_date` (YYYY-MM-DD, optional)',
        'download_sample_tx': 'Download Sample Transaction CSV',
        'download_sample_div': 'Download Sample Dividend CSV',
        'upload_tx': 'Upload your transaction CSV',
        'upload_div': 'Upload your dividend CSV',
        'import_tx': 'Import Transactions',
        'import_div': 'Import Dividends',
        'success_import': 'Successfully imported {} {}.',
        'failed_import_row': 'Failed to add {} {} on {}: {}',
        
        # Footer
        'disclaimer': '*Data is for informational purposes only. Not financial advice.*',
        
        # Error messages
        'error': 'Error',
        'success': 'Success',
        'warning': 'Warning',
        'info': 'Info'
    },
    'zh-TW': {
        # App title and sidebar
        'app_title': '香港股票追蹤器',
        'portfolio_dashboard': '投資組合儀表板',
        'add_transaction': '新增交易',
        'add_dividend': '新增股息',
        'view_data': '查看數據',
        'settings': '設置',
        'import_csv': '導入 CSV',
        'language': '語言',
        'menu': '選單',
        'english': 'English',
        'traditional_chinese': '繁體中文',
        
        # Portfolio Dashboard
        'total_invested': '總投資額',
        'total_value': '總市值',
        'total_return': '總回報',
        'dividend_income': '股息收入',
        'current_positions': '當前持倉',
        'stock': '股票',
        'company': '公司',
        'shares': '股數',
        'avg_cost': '平均成本',
        'current_price': '當前價格',
        'market_value': '市場價值',
        'unrealized_pl': '未實現損益',
        'pl_percent': '損益百分比',
        'dividend_received': '已收股息',
        'recent_transactions': '最近交易',
        'date': '日期',
        'type': '類型',
        'price': '價格',
        'fees': '手續費',
        'total': '總額',
        'no_stocks': '投資組合中沒有股票。請先添加一些交易。',
        'no_positions': '沒有持倉顯示。',
        'no_transactions': '沒有交易記錄。',
        
        # Add Transaction
        'stock_code': '股票代號 (例如：0700.HK)',
        'company_name': '公司名稱',
        'transaction_date': '交易日期',
        'quantity': '股數（股）',
        'price_per_share': '每股價格（港元）',
        'fees': '手續費（港元）',
        'fetch_company_name': '🔍 獲取公司名稱',
        'transaction_added': '交易添加成功！ID：{}',
        'error_adding_transaction': '添加交易時出錯：{}',
        'please_fill_fields': '請填寫所有必填字段。',
        
        # Add Dividend
        'record_date': '除息日',
        'dividend_per_share': '每股股息（港元）',
        'payment_date': '發放日期（可選）',
        'dividend_added': '股息記錄添加成功！ID：{}',
        'error_adding_dividend': '添加股息時出錯：{}',
        'please_enter_stock_code': '請輸入股票代號。',
        
        # View Data
        'all_transactions': '所有交易',
        'all_dividends': '所有股息',
        'download_transactions': '下載交易為 CSV',
        'download_dividends': '下載股息為 CSV',
        'no_transactions_found': '沒有找到交易。',
        'no_dividends_found': '沒有找到股息。',
        'created_at': '創建時間',
        'action': '操作',
        'delete_tooltip': '刪除此 {}',
        'transaction_deleted': '交易 {} 已刪除。',
        'failed_to_delete_transaction': '刪除交易 {} 失敗。',
        'dividend_deleted': '股息 {} 已刪除。',
        'failed_to_delete_dividend': '刪除股息 {} 失敗。',
        
        # Settings
        'database_operations': '資料庫操作',
        'refresh_data': '🔄 刷新數據',
        'clear_all_data': '🗑️ 清除所有數據',
        'understand_clear': '我了解這將刪除所有數據',
        'all_data_cleared': '所有數據已清除！',
        'about': '關於',
        'app_description': '''**香港股票追蹤器** v1.0.0

一個便携的純Python應用程式，用於追蹤香港股票投資。

功能：
- 交易追蹤並計算成本基礎
- 股息收入追蹤
- 透過 yfinance 獲取實時價格
- 投資組合績效分析
- 本地 SQLite 資料庫（無外部依賴）
- 跨平台相容（Windows, macOS, Linux）

建置於：
- Python 3.11+
- Streamlit 介面
- yfinance 市場數據
- SQLite 資料庫
''',
        
        # Import CSV
        'import_csv_title': '導入 CSV',
        'import_instructions': '從 CSV 檔案導入您的交易或股息記錄。',
        'select_data_type': '選擇要導入的數據類型',
        'transactions': '交易',
        'dividends': '股息',
        'expected_columns_tx': '**預期 CSV 欄位：**\\n- `date` (YYYY-MM-DD)\\n- `stock_code` (例如：0700.HK)\\n- `quantity` (整數，股數)\\n- `price_per_share` (數值，港元)\\n- `fees` (數值，港元，可選)',
        'expected_columns_div': '**預期 CSV 欄位：**\\n- `stock_code` (例如：0700.HK)\\n- `record_date` (YYYY-MM-DD)\\n- `dividend_per_share` (數值，港元／股)\\n- `payment_date` (YYYY-MM-DD，可選)',
        'download_sample_tx': '下載範例交易 CSV',
        'download_sample_div': '下載範例股息 CSV',
        'upload_tx': '上傳您的交易 CSV',
        'upload_div': '上傳您的股息 CSV',
        'import_tx': '導入交易',
        'import_div': '導入股息',
        'success_import': '成功導入 {} 筆 {}。',
        'failed_import_row': '導入 {} {} 時失敗（日期 {}）：{}',
        
        # Footer
        'disclaimer': '*數據僅供參考，不構成財務建議。*',
        
        # Error messages
        'error': '錯誤',
        'success': '成功',
        'warning': '警告',
        'info': '資訊'
    }
}

def t(key):
    """Get translation for the current language."""
    # Try to get the translation in the current language
    lang_dict = translations.get(st.session_state.lang, translations['en'])
    # If the key is not found in the current language, try English
    # If not found in English, return the key itself (as a fallback)
    return lang_dict.get(key, translations['en'].get(key, key))

# ===== END LANGUAGE SETUP =====

# Page configuration
st.set_page_config(page_title=t("app_title"), 
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Helper functions
def format_currency(amount):
    """Format amount as HKD currency"""
    return f"HKD {amount:,.2f}"

def format_percent(amount):
    """Format amount as percentage"""
    return f"{amount:+.2f}%"

def load_sample_data():
    """Load sample data for demonstration"""
    # Check if the database file exists
    if not get_db_path().exists():
        # Database file does not exist, initialize and load sample data
        init_database()
        # Add sample transactions
        add_transaction("0700.HK", "Tencent Holdings", "2024-01-15", 100, 350.00, 25.00)
        add_transaction("0700.HK", "Tencent Holdings", "2024-02-20", 50, 380.00, 15.00)
        add_transaction("9988.HK", "Alibaba Group", "2024-03-10", 200, 85.00, 20.00)
        add_transaction("0005.HK", "HSBC Holdings", "2024-01-20", 100, 75.00, 10.00)
        
        # Add sample dividends
        add_dividend("0700.HK", "2024-05-15", 1.50, "2024-06-01")
        add_dividend("9988.HK", "2024-06-20", 2.00, "2024-07-01")
        add_dividend("0005.HK", "2024-03-15", 0.50, "2024-04-01")

# Sidebar
st.sidebar.title("📈 " + t("app_title"))
st.sidebar.markdown("---")


# Language selector
st.sidebar.markdown("## " + t("language"))
language = st.sidebar.selectbox(
    t("language"),
    options=["en", "zh-TW"],
    format_func=lambda x: t("english") if x == "en" else t("traditional_chinese"),
    index=0 if st.session_state.lang == "en" else 1
)
if language != st.session_state.lang:
    st.session_state.lang = language
    # Update query params to reflect the language
    try:
        st.query_params["lang"] = language
    except:
        pass
    st.rerun()

# Menu options
menu = st.sidebar.selectbox(
    t("menu"),
    [t('portfolio_dashboard'), t('add_transaction'), t('add_dividend'), t('view_data'), t('settings'), t('import_csv_title')]
)
print(f"DEBUG: Menu selected: {menu}")  # DEBUG

# Load sample data on first run
if 'sample_loaded' not in st.session_state:
    load_sample_data()
    st.session_state.sample_loaded = True

def parse_transaction_csv(file):
    """Parse CSV file for transactions.
    Expected columns: date, stock_code, quantity, price_per_share, fees (optional).
    Company name is fetched automatically from the stock code.
    Returns list of dicts ready for add_transaction.
    """
    try:
        # Read file content
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
    except Exception:
        return None, "Unable to read file as UTF-8 text."
    # Use StringIO
    f_io = io.StringIO(content)
    reader = csv.DictReader(f_io)
    # Normalize column names (strip spaces, lower)
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames] if reader.fieldnames else []
    required = {'date', 'stock_code', 'quantity', 'price_per_share', 'fees'}
    if not required.issubset(set(reader.fieldnames)):
        missing = required - set(reader.fieldnames)
        return None, f"Missing required columns: {', '.join(missing)}"
    rows = []
    for i, row in enumerate(reader, start=2):  # start at line 2 (header line 1)
        try:
            # Strip whitespace
            date = row['date'].strip()
            stock_code = row['stock_code'].strip().upper()
            quantity_str = row['quantity'].strip()
            price_per_share_str = row['price_per_share'].strip()
            fees_str = row['fees'].strip()

            # Convert and validate
            if not quantity_str:
                raise ValueError("Quantity is required")
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            if not price_per_share_str:
                raise ValueError("Price per share is required")
            price_per_share = float(price_per_share_str)
            if price_per_share < 0:
                raise ValueError("Price per share cannot be negative")

            fees = float(fees_str) if fees_str else 0.0
            if fees < 0:
                raise ValueError("Fees cannot be negative")

            # Fetch company name from stock code
            info = fetch_company_info(stock_code)
            if info and info.get('long_name'):
                company_name = info['long_name']
            elif info and info.get('short_name'):
                company_name = info['short_name']
            else:
                company_name = ""  # fallback to empty string if not found

            # Basic validation for date (optional, we trust user)
            # Date format validation (optional, we trust user)
            rows.append({
                'stock_code': stock_code,
                'company_name': company_name,
                'transaction_date': date,
                'quantity': quantity,
                'price_per_share': price_per_share,
                'fees': fees
            })
        except Exception as e:
            return None, f"Error on line {i}: {e}"
    return rows, None
def parse_dividend_csv(file):
    """Parse CSV file for dividends.
    Expected columns: stock_code, record_date, dividend_per_share, payment_date (optional)
    Returns list of dicts ready for add_dividend.
    """
    try:
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
    except Exception:
        return None, "Unable to read file as UTF-8 text."
    f = io.StringIO(content)
    reader = csv.DictReader(f)
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames] if reader.fieldnames else []
    required = {'stock_code', 'record_date', 'dividend_per_share'}
    if not required.issubset(set(reader.fieldnames)):
        missing = required - set(reader.fieldnames)
        return None, f"Missing required columns: {', '.join(missing)}"
    rows = []
    for i, row in enumerate(reader, start=2):
        try:
            stock_code = row['stock_code'].strip().upper()
            record_date = row['record_date'].strip()
            dividend_per_share = float(row['dividend_per_share'])
            payment_date = row.get('payment_date', '').strip()
            if payment_date == '':
                payment_date = None
            if dividend_per_share < 0:
                raise ValueError("Dividend per share cannot be negative")
            rows.append({
                'stock_code': stock_code,
                'record_date': record_date,
                'dividend_per_share': dividend_per_share,
                'payment_date': payment_date
            })
        except Exception as e:
            return None, f"Error on line {i}: {e}"
    return rows, None

def get_sample_transaction_csv():
    """Generate a sample CSV for transactions."""
    header = ['date', 'stock_code', 'quantity', 'price_per_share', 'fees']
    rows = [
        ['2024-01-15', '0700.HK', 100, 350.00, 25.00],
        ['2024-02-20', '0700.HK', 50, 380.00, 15.00],
        ['2024-03-10', '9988.HK', 200, 85.00, 20.00],
        ['2024-01-20', '0005.HK', 100, 75.00, 10.00],
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue()

def get_sample_dividend_csv():
    """Generate a sample CSV for dividends."""
    header = ['stock_code', 'record_date', 'dividend_per_share', 'payment_date']
    rows = [
        ['0700.HK', '2024-05-15', 1.50, '2024-06-01'],
        ['9988.HK', '2024-06-20', 2.00, '2024-07-01'],
        ['0005.HK', '2024-03-15', 0.50, '2024-04-01'],
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue()

# Main content
if menu == t('portfolio_dashboard'):
    print("DEBUG: In t('portfolio_dashboard') block")  # DEBUG
    st.title("📊 " + t('portfolio_dashboard'))
    print("DEBUG: After st.title")  # DEBUG

    # Get current prices for all stocks in portfolio
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT stock_code FROM transactions WHERE stock_code IS NOT NULL")
        stocks = [row[0] for row in cursor.fetchall()]
    
    if not stocks:
        st.warning(t('no_stocks'))
    else:
        # Fetch current prices
        with st.spinner("Fetching current prices..."):
            current_prices = {}
            for stock in stocks:
                price_data = fetch_current_price(stock)
                if price_data:
                    current_prices[stock] = price_data.current_price
                else:
                    # Fallback to last known price or 0
                    current_prices[stock] = 0.0
        
        # Calculate portfolio summary
        summary = get_portfolio_summary(current_prices)
        
        # Display summary cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label=t('total_invested'),
                value=format_currency(summary.total_invested)
            )
        
        with col2:
            st.metric(
                label=t('total_value'),
                value=format_currency(summary.total_market_value)
            )
        
        with col3:
            st.metric(
                label=t('total_return'),
                value=format_currency(summary.total_return),
                delta=format_percent(summary.total_return_percent)
            )
        
        with col4:
            st.metric(
                label=t('dividend_income'),
                value=format_currency(summary.total_dividend_income)
            )
        
        st.markdown("---")
        
        # Positions table
        if summary.positions:
            st.subheader("📋 " + t('current_positions'))
            
            positions_data = []
            for pos in summary.positions:
                # Calculate dividend income for this stock (all time)
                dividends = calculate_dividend_income(pos.stock_code)
                total_dividend_received = sum(div.total_dividend for div in dividends)
                
                positions_data.append({
                    t('stock'): pos.stock_code,
                    t('company'): pos.company_name,
                    t('shares'): pos.total_shares,
                    t('avg_cost'): format_currency(pos.weighted_avg_cost),
                    t('current_price'): format_currency(pos.current_price),
                    t('market_value'): format_currency(pos.market_value),
                    t('unrealized_pl'): format_currency(pos.unrealized_pl),
                    t('pl_percent'): format_percent(pos.unrealized_pl_percent),
                    t('dividend_received'): format_currency(total_dividend_received)
                })
            
            df = pd.DataFrame(positions_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info(t('no_positions'))
        
        st.markdown("---")
        
        # Recent transactions
        st.subheader("📝 " + t('recent_transactions'))
        transactions = get_transactions()
        if transactions:
            tx_data = []
            for tx in transactions[-10:]:  # Last 10 transactions
                tx_data.append({
                    t('date'): tx["transaction_date"],
                    t('stock'): tx["stock_code"],
                    t('company'): tx["company_name"],
                    t('type'): "Buy",
                    t('shares'): tx["quantity"],
                    t('price'): format_currency(tx["price_per_share"]),
                    "Fees": format_currency(tx["fees"]),
                    t('total'): format_currency(tx["quantity"] * tx["price_per_share"] + tx["fees"])
                })
            
            df_tx = pd.DataFrame(tx_data)
            st.dataframe(df_tx, use_container_width=True, hide_index=True)
        else:
            st.info(t('no_transactions'))

elif menu == t('add_transaction'):
    st.title("➕ " + t('add_transaction'))

    # Initialize session state for company name if not present
    if 'company_name' not in st.session_state:
        st.session_state.company_name = ""

    # Callback to fetch company name when stock code changes
    def fetch_company_name():
        stock_code = st.session_state.get('stock_code_input', '').upper().strip()
        if stock_code:
            info = fetch_company_info(stock_code)
            if info and info.get('long_name'):
                st.session_state.company_name = info['long_name']
            elif info and info.get('short_name'):
                st.session_state.company_name = info['short_name']
            else:
                st.session_state.company_name = ""  # Clear if not found
        else:
            st.session_state.company_name = ""

    # t('stock') code and company name inputs (outside the form)
    col1, col2 = st.columns(2)

    with col1:
        if st.button(t('refresh_data'), type="secondary"):
            st.cache_data.clear()
            st.success("Data refreshed!")

    with col2:
        understand = st.checkbox(t('understand_clear'))
        if st.button(t('clear_all_data'), type="secondary", disabled=not understand):
            reset_database()
            st.success(t('all_data_cleared'))
            st.rerun()

    st.markdown("---")
    st.subheader(t('about'))
    st.markdown(t("app_description"))

elif menu == t('import_csv_title'):
    st.title("📥 " + t('import_csv_title'))
    st.markdown(t('import_instructions'))

    # Choose import type
    import_type = st.radio(t('select_data_type'), [t('transactions'), t('dividends')], horizontal=True)

    if import_type == t('transactions'):
        st.subheader(t('import_tx'))
        st.markdown("""
        **Expected CSV columns:**
        - `date` (YYYY-MM-DD)
        - `stock_code` (e.g., 0700.HK)
        - `company_name` (e.g., Tencent Holdings)
        - `quantity` (integer, number of shares)
        - `price_per_share` (numeric, HKD)
        - `fees` (numeric, HKD, optional)
        """)
        # Provide sample CSV download
        sample_tx_csv = get_sample_transaction_csv()
        st.download_button(
            label=t('download_sample_tx'),
            data=sample_tx_csv,
            file_name="sample_transactions.csv",
            mime="text/csv"
        )
        uploaded_file = st.file_uploader(t('upload_tx'), type=["csv"])
        if uploaded_file is not None:
            rows, error = parse_transaction_csv(uploaded_file)
            if error:
                st.error(error)
            else:
                if st.button(t('import_tx')):
                    success_count = 0
                    for row in rows:
                        try:
                            tx_id = add_transaction(
                                row['stock_code'],
                                row['company_name'],
                                row['transaction_date'],
                                row['quantity'],
                                row['price_per_share'],
                                row['fees']
                            )
                            success_count += 1
                        except Exception as e:
                            st.warning(f"Failed to add transaction {row['stock_code']} on {row['transaction_date']}: {e}")
                    st.success(f"{t('success')}fully imported {success_count} transactions.")
                    # Optionally clear the uploader
                    uploaded_file = None
    else:  # t('dividends')
        st.subheader(t('import_div'))
        st.markdown("""
        **Expected CSV columns:**
        - `stock_code` (e.g., 0700.HK)
        - `record_date` (YYYY-MM-DD)
        - `dividend_per_share` (numeric, HKD per share)
        - `payment_date` (YYYY-MM-DD, optional)
        """)
        sample_div_csv = get_sample_dividend_csv()
        st.download_button(
            label=t('download_sample_div'),
            data=sample_div_csv,
            file_name="sample_dividends.csv",
            mime="text/csv"
        )
        uploaded_file = st.file_uploader(t('upload_div'), type=["csv"])
        if uploaded_file is not None:
            rows, error = parse_dividend_csv(uploaded_file)
            if error:
                st.error(error)
            else:
                if st.button(t('import_div')):
                    success_count = 0
                    for row in rows:
                        try:
                            div_id = add_dividend(
                                row['stock_code'],
                                row['record_date'],
                                row['dividend_per_share'],
                                row['payment_date']
                            )
                            success_count += 1
                        except Exception as e:
                            st.warning(f"Failed to add dividend for {row['stock_code']} on {row['record_date']}: {e}")
                    st.success(f"{t('success')}fully imported {success_count} dividend records.")
                    uploaded_file = None
# Footer
st.markdown("---")
st.markdown(t('disclaimer'))