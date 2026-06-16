"""
Database module for HK Stock Tracker.
Handles SQLite database initialization and schema management.
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


DB_NAME = "portfolio.db"


def get_db_path() -> Path:
    """Get the path to the SQLite database file."""
    return Path(__file__).parent / DB_NAME


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    """Initialize the database with required tables."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                company_name TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_share REAL NOT NULL,
                fees REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Dividends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dividends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                record_date TEXT NOT NULL,
                payment_date TEXT,
                dividend_per_share REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_stock_code
            ON transactions(stock_code)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dividends_stock_code
            ON dividends(stock_code)
        """)

        conn.commit()


def reset_database() -> None:
    """Drop and recreate all tables (for testing)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS dividends")
        cursor.execute("DROP TABLE IF EXISTS transactions")
        conn.commit()
    init_database()


# Transaction CRUD operations
def add_transaction(
    stock_code: str,
    company_name: str,
    transaction_date: str,
    quantity: int,
    price_per_share: float,
    fees: float = 0.0
) -> int:
    """Add a new transaction and return its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (stock_code, company_name, transaction_date, quantity, price_per_share, fees)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (stock_code, company_name, transaction_date, quantity, price_per_share, fees))
        conn.commit()
        return cursor.lastrowid


def get_transactions(stock_code: Optional[str] = None) -> list[sqlite3.Row]:
    """Get all transactions, optionally filtered by stock code."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if stock_code:
            cursor.execute("SELECT * FROM transactions WHERE stock_code = ? ORDER BY transaction_date", (stock_code,))
        else:
            cursor.execute("SELECT * FROM transactions ORDER BY transaction_date")
        return cursor.fetchall()


def get_transaction_by_id(transaction_id: int) -> Optional[sqlite3.Row]:
    """Get a single transaction by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        return cursor.fetchone()


def delete_transaction(transaction_id: int) -> bool:
    """Delete a transaction by ID. Returns True if deleted."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        return cursor.rowcount > 0


# Dividend CRUD operations
def add_dividend(
    stock_code: str,
    record_date: str,
    dividend_per_share: float,
    payment_date: Optional[str] = None
) -> int:
    """Add a new dividend record and return its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dividends (stock_code, record_date, payment_date, dividend_per_share)
            VALUES (?, ?, ?, ?)
        """, (stock_code, record_date, payment_date, dividend_per_share))
        conn.commit()
        return cursor.lastrowid


def get_dividends(stock_code: Optional[str] = None) -> list[sqlite3.Row]:
    """Get all dividends, optionally filtered by stock code."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if stock_code:
            cursor.execute("SELECT * FROM dividends WHERE stock_code = ? ORDER BY record_date", (stock_code,))
        else:
            cursor.execute("SELECT * FROM dividends ORDER BY record_date")
        return cursor.fetchall()


def get_dividend_by_id(dividend_id: int) -> Optional[sqlite3.Row]:
    """Get a single dividend by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dividends WHERE id = ?", (dividend_id,))
        return cursor.fetchone()


def delete_dividend(dividend_id: int) -> bool:
    """Delete a dividend by ID. Returns True if deleted."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dividends WHERE id = ?", (dividend_id,))
        conn.commit()
        return cursor.rowcount > 0


if __name__ == "__main__":
    # Quick test when run directly
    init_database()
    print(f"Database initialized at: {get_db_path()}")