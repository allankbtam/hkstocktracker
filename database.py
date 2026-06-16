import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "portfolio.db"

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            company_name TEXT,
            transaction_date TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price_per_share REAL NOT NULL,
            fees REAL NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS dividends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            record_date TEXT NOT NULL,
            payment_date TEXT,
            dividend_per_share REAL NOT NULL
        )
        """)
        conn.commit()

def add_transaction(stock_code, company_name, transaction_date, quantity, price_per_share, fees):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO transactions
               (stock_code, company_name, transaction_date, quantity, price_per_share, fees)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (stock_code, company_name, transaction_date, quantity, price_per_share, fees)
        )
        conn.commit()
        return cur.lastrowid

def add_dividend(stock_code, record_date, payment_date, dividend_per_share):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO dividends
               (stock_code, record_date, payment_date, dividend_per_share)
               VALUES (?, ?, ?, ?)""",
            (stock_code, record_date, payment_date, dividend_per_share)
        )
        conn.commit()
        return cur.lastrowid

def get_transactions():
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM transactions ORDER BY transaction_date")
        return cur.fetchall()

def get_dividends():
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM dividends ORDER BY record_date")
        return cur.fetchall()

def reset_database():
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM dividends")
        conn.commit()
