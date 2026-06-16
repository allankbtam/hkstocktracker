#!/usr/bin/env python3
"""Financial math and logic engine for HK Stock Tracker"""
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import sqlite3
from datetime import datetime
from database import get_connection, get_transactions, get_dividends


@dataclass
class Position:
    """Current position for a stock"""
    stock_code: str
    company_name: str
    total_shares: int
    total_cost: float  # Total amount invested (including fees)
    weighted_avg_cost: float  # Weighted average cost per share
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_pl_percent: float


@dataclass
class DividendIncome:
    """Dividend income for a period"""
    stock_code: str
    dividend_per_share: float
    shares_held_on_record_date: int
    total_dividend: float
    record_date: str
    payment_date: Optional[str]


@dataclass
class PortfolioSummary:
    """Overall portfolio summary"""
    total_invested: float
    total_market_value: float
    total_unrealized_pl: float
    total_unrealized_pl_percent: float
    total_dividend_income: float
    total_return: float
    total_return_percent: float
    positions: List[Position]


def calculate_weighted_avg_cost(transactions: List[sqlite3.Row]) -> Tuple[float, float]:
    """
    Calculate weighted average cost basis and total cost from transactions.
    
    Returns:
        (weighted_avg_cost_per_share, total_cost_including_fees)
    """
    if not transactions:
        return 0.0, 0.0
    
    total_shares = 0
    total_cost = 0.0  # Includes fees
    
    for txn in transactions:
        shares = txn["quantity"]
        price_per_share = txn["price_per_share"]
        fees = txn["fees"]
        
        cost = (shares * price_per_share) + fees
        total_shares += shares
        total_cost += cost
    
    if total_shares == 0:
        return 0.0, 0.0
    
    weighted_avg = total_cost / total_shares
    return weighted_avg, total_cost


def get_positions(current_prices: Dict[str, float]) -> List[Position]:
    """
    Calculate current positions for all stocks in portfolio.
    
    Args:
        current_prices: Dict mapping stock_code to current price
    
    Returns:
        List of Position objects
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        # Get all transactions grouped by stock
        cursor.execute("""
            SELECT stock_code, company_name, 
                   SUM(quantity) as total_shares,
                   SUM(quantity * price_per_share + fees) as total_cost
            FROM transactions
            GROUP BY stock_code, company_name
            HAVING SUM(quantity) > 0
        """)
        rows = cursor.fetchall()
    
    positions = []
    for row in rows:
        stock_code = row["stock_code"]
        company_name = row["company_name"]
        total_shares = row["total_shares"]
        total_cost = row["total_cost"]
        
        if total_shares <= 0:
            continue
            
        weighted_avg_cost = total_cost / total_shares if total_shares > 0 else 0
        current_price = current_prices.get(stock_code, 0.0)
        market_value = total_shares * current_price
        unrealized_pl = market_value - total_cost
        unrealized_pl_percent = (unrealized_pl / total_cost * 100) if total_cost > 0 else 0.0
        
        positions.append(Position(
            stock_code=stock_code,
            company_name=company_name,
            total_shares=total_shares,
            total_cost=total_cost,
            weighted_avg_cost=weighted_avg_cost,
            current_price=current_price,
            market_value=market_value,
            unrealized_pl=unrealized_pl,
            unrealized_pl_percent=unrealized_pl_percent
        ))
    
    return positions


def calculate_dividend_income(
    stock_code: str, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[DividendIncome]:
    """
    Calculate dividend income for a stock based on holdings on record dates.
    
    Args:
        stock_code: Stock ticker
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    
    Returns:
        List of DividendIncome objects
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get dividends
        query = """
            SELECT record_date, payment_date, dividend_per_share
            FROM dividends
            WHERE stock_code = ?
        """
        params = [stock_code]
        
        if start_date:
            query += " AND record_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND record_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY record_date"
        
        cursor.execute(query, params)
        dividend_rows = cursor.fetchall()
    
    if not dividend_rows:
        return []
    
    # Get all transactions for this stock ordered by date
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT transaction_date, quantity
            FROM transactions
            WHERE stock_code = ?
            ORDER BY transaction_date
        """, (stock_code,))
        txn_rows = cursor.fetchall()
    
    dividend_income = []
    running_shares = 0
    txn_idx = 0
    
    for div_row in dividend_rows:
        record_date = div_row["record_date"]
        payment_date = div_row["payment_date"]
        dividend_per_share = div_row["dividend_per_share"]
        
        # Update shares held up to this record date
        while txn_idx < len(txn_rows) and txn_rows[txn_idx]["transaction_date"] <= record_date:
            running_shares += txn_rows[txn_idx]["quantity"]
            txn_idx += 1
        
        if running_shares > 0:
            total_dividend = running_shares * dividend_per_share
            dividend_income.append(DividendIncome(
                stock_code=stock_code,
                dividend_per_share=dividend_per_share,
                shares_held_on_record_date=running_shares,
                total_dividend=total_dividend,
                record_date=record_date,
                payment_date=payment_date
            ))
    
    return dividend_income


def get_portfolio_summary(current_prices: Dict[str, float]) -> PortfolioSummary:
    """
    Calculate complete portfolio summary.
    
    Args:
        current_prices: Dict mapping stock_code to current price
    
    Returns:
        PortfolioSummary object
    """
    positions = get_positions(current_prices)
    
    total_invested = sum(pos.total_cost for pos in positions)
    total_market_value = sum(pos.market_value for pos in positions)
    total_unrealized_pl = total_market_value - total_invested
    total_unrealized_pl_percent = (
        (total_unrealized_pl / total_invested * 100) if total_invested > 0 else 0.0
    )
    
    # Calculate dividend income (all time)
    total_dividend_income = 0.0
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT stock_code FROM transactions")
        stock_codes = [row["stock_code"] for row in cursor.fetchall()]
    
    for stock_code in stock_codes:
        dividends = calculate_dividend_income(stock_code)
        total_dividend_income += sum(div.total_dividend for div in dividends)
    
    total_return = total_unrealized_pl + total_dividend_income
    total_return_percent = (
        (total_return / total_invested * 100) if total_invested > 0 else 0.0
    )
    
    return PortfolioSummary(
        total_invested=total_invested,
        total_market_value=total_market_value,
        total_unrealized_pl=total_unrealized_pl,
        total_unrealized_pl_percent=total_unrealized_pl_percent,
        total_dividend_income=total_dividend_income,
        total_return=total_return,
        total_return_percent=total_return_percent,
        positions=positions
    )


def round_currency(amount: float) -> float:
    """Round to 2 decimal places for currency"""
    return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


if __name__ == "__main__":
    # Quick test when run directly
    from database import init_database, add_transaction, add_dividend
    init_database()
    
    # Add test data
    add_transaction("0700.HK", "Tencent", "2024-01-15", 100, 350.00, 25.00)
    add_transaction("0700.HK", "Tencent", "2024-02-20", 100, 380.00, 15.00)
    add_dividend("0700.HK", "2024-05-15", 1.50, "2024-06-01")
    
    # Test calculations
    prices = {"0700.HK": 400.0}
    summary = get_portfolio_summary(prices)
    
    print(f"Total Invested: {summary.total_invested:.2f}")
    print(f"Total Shares: {summary.positions[0].total_shares}")
    print(f"Weighted Avg Cost: {summary.positions[0].weighted_avg_cost:.2f}")
    print(f"Unrealized P&L: {summary.total_unrealized_pl:.2f}")
    print(f"Dividend Income: {summary.total_dividend_income:.2f}")
    print(f"Total Return: {summary.total_return:.2f}")