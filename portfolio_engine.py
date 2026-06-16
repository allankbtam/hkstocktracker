from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple
from database import get_transactions, get_dividends

def weight_avg_cost(transactions: List[Tuple]) -> float:
    """Calculate weighted average cost per share including fees."""
    total_cost = 0.0
    total_shares = 0
    for tx in transactions:
        # tx: (id, stock_code, company_name, transaction_date, quantity, price_per_share, fees)
        qty = tx[4]
        price = tx[5]
        fees = tx[6]
        total_cost += qty * price + fees
        total_shares += qty
    if total_shares == 0:
        return 0.0
    return total_cost / total_shares

def unrealized_pl(transactions: List[Tuple], current_price: float) -> float:
    """Unrealized P&L = (current_price - avg_cost) * shares."""
    avg_cost = weight_avg_cost(transactions)
    total_shares = sum(tx[4] for tx in transactions)
    return (current_price - avg_cost) * total_shares

def dividend_income(transactions: List[Tuple], dividends: List[Tuple]) -> float:
    """Sum of dividends earned based on shares held on record date."""
    # Build map of stock_code -> list of transactions with date
    from collections import defaultdict
    tx_by_stock = defaultdict(list)
    for tx in transactions:
        tx_by_stock[tx[1]].append(tx)  # stock_code at index 1
    total_div = 0.0
    for div in dividends:
        stock_code, record_date, _payment_date, div_per_share = div
        # sum quantities of transactions on or before record_date
        shares_held = 0
        for tx in tx_by_stock.get(stock_code, []):
            tx_date = tx[3]  # transaction_date
            if tx_date <= record_date:
                shares_held += tx[4]
        total_div += shares_held * div_per_share
    return total_div

def total_return(unrealized_pl: float, dividend_income: float) -> float:
    return unrealized_pl + dividend_income
