#!/usr/bin/env python3
"""Data fetching module for HK Stock Tracker using yfinance"""
import yfinance as yf
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StockPrice:
    """Current stock price data"""
    stock_code: str
    current_price: float
    currency: str = "HKD"
    timestamp: str = ""
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None


@dataclass
class DividendData:
    """Dividend information"""
    stock_code: str
    ex_dividend_date: str
    payment_date: Optional[str]
    dividend_per_share: float
    currency: str = "HKD"


def fetch_current_price(stock_code: str, timeout: int = 10) -> Optional[StockPrice]:
    """
    Fetch current market price for a HK stock.
    
    Args:
        stock_code: Stock ticker (e.g., "0700.HK", "9988.HK")
        timeout: Request timeout in seconds
    
    Returns:
        StockPrice object or None if failed
    """
    try:
        ticker = yf.Ticker(stock_code)
        
        # Get fast info (no history needed)
        info = ticker.fast_info
        
        current_price = info.get("last_price") or info.get("regular_market_price")
        previous_close = info.get("previous_close")
        currency = info.get("currency", "HKD")
        
        if current_price is None:
            # Fallback to history
            hist = ticker.history(period="1d", timeout=timeout)
            if hist.empty:
                logger.warning(f"No price data for {stock_code}")
                return None
            current_price = float(hist["Close"].iloc[-1])
            if previous_close is None and len(hist) > 1:
                previous_close = float(hist["Close"].iloc[-2])
        
        change = None
        change_percent = None
        if previous_close and previous_close > 0:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
        
        return StockPrice(
            stock_code=stock_code,
            current_price=float(current_price),
            currency=currency,
            timestamp=datetime.now().isoformat(),
            previous_close=float(previous_close) if previous_close else None,
            change=change,
            change_percent=change_percent
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch price for {stock_code}: {e}")
        return None


def fetch_dividends(stock_code: str, years_back: int = 5) -> list[DividendData]:
    """
    Fetch historical dividend data for a HK stock.
    
    Args:
        stock_code: Stock ticker (e.g., "0700.HK")
        years_back: How many years of history to fetch
    
    Returns:
        List of DividendData objects
    """
    dividends = []
    try:
        ticker = yf.Ticker(stock_code)
        
        # Get dividend history
        div_history = ticker.dividends
        
        if div_history.empty:
            logger.info(f"No dividend history for {stock_code}")
            return dividends
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=years_back * 365)
        
        for date, amount in div_history.items():
            if date.tz is not None:
                date = date.tz_localize(None)
            
            if date >= cutoff_date:
                dividends.append(DividendData(
                    stock_code=stock_code,
                    ex_dividend_date=date.strftime("%Y-%m-%d"),
                    payment_date=None,  # yfinance doesn't always provide this
                    dividend_per_share=float(amount),
                    currency="HKD"
                ))
        
        logger.info(f"Fetched {len(dividends)} dividends for {stock_code}")
        return dividends
        
    except Exception as e:
        logger.error(f"Failed to fetch dividends for {stock_code}: {e}")
        return dividends


def fetch_company_info(stock_code: str) -> Optional[Dict[str, Any]]:
    """Fetch basic company information"""
    try:
        ticker = yf.Ticker(stock_code)
        info = ticker.info
        return {
            "long_name": info.get("longName"),
            "short_name": info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency", "HKD"),
            "exchange": info.get("exchange"),
        }
    except Exception as e:
        logger.error(f"Failed to fetch company info for {stock_code}: {e}")
        return None


if __name__ == "__main__":
    # Quick test
    print("Testing price fetch for 0700.HK...")
    price = fetch_current_price("0700.HK")
    if price:
        print(f"Price: {price.current_price} {price.currency}")
        if price.change_percent:
            print(f"Change: {price.change_percent:.2f}%")
    
    print("\nTesting dividend fetch for 0700.HK...")
    divs = fetch_dividends("0700.HK")
    for d in divs[:3]:
        print(f"  {d.ex_dividend_date}: {d.dividend_per_share} {d.currency}")