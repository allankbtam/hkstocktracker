import yfinance as yf
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=32)
def fetch_current_price(stock_code: str) -> float:
    """Return current price for a given HK stock code (e.g., '0700.HK')."""
    try:
        ticker = yf.Ticker(stock_code)
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception:
        pass
    return 0.0

@lru_cache(maxsize=32)
def fetch_company_info(stock_code: str) -> dict:
    """Return dict with keys 'company_name', 'sector'."""
    try:
        ticker = yf.Ticker(stock_code)
        info = ticker.info
        return {
            "company_name": info.get("longName", ""),
            "sector": info.get("sector", ""),
        }
    except Exception:
        return {"company_name": "", "sector": ""}

def fetch_dividends(stock_code: str, years_back: int = 5):
    """Return list of (record_date, dividend_per_share) for given ticker."""
    try:
        ticker = yf.Ticker(stock_code)
        divs = ticker.dividends
        if divs.empty:
            return []
        cutoff = datetime.now() - timedelta(days=365*years_back)
        result = []
        for date, div in divs.items():
            # date is a Timestamp
            if date.to_pydatetime() >= cutoff:
                result.append((date.strftime("%Y-%m-%d"), float(div)))
        return result
    except Exception:
        return []
