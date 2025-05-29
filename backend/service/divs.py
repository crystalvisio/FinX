import yfinance as yf
import requests
from icecream import ic
from datetime import datetime, UTC
from backend.schemas import Holding, DividendInfo
from backend.config import settings

def convert_to_yfinance_symbol(symbol: str) -> str:
    """Convert Trading 212 symbol format to yfinance format."""
    # If symbol ends with 'l', it's a London exchange stock
    if symbol.endswith('l'):
        return f"{symbol[:-1]}.L"
    # Otherwise, it's a US stock or other exchange, return as is
    return symbol

async def fetch_dividends(holdings: list[Holding]) -> list[DividendInfo]:
    results: list[DividendInfo] = []
    ic(holdings)
    
    for stock in holdings:
        yf_symbol = convert_to_yfinance_symbol(stock.symbol)
        ic(f"Processing stock: {stock.symbol} -> {yf_symbol}")
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        ex_timestamp = info.get("exDividendDate")
        dividend_rate = info.get("dividendRate")

        if not ex_timestamp or dividend_rate is None:
            continue

        # Convert timestamp to date
        ex_date = datetime.fromtimestamp(ex_timestamp, UTC).date()

        # Get FX rate from holding currency to GBP
        resp = requests.get(settings.fx_url, params={"base": stock.currency, "symbols": settings.fx_base_curr})
        data = resp.json()
        fx_rate = data.get("rates", {}).get(settings.fx_base_curr, 1.0)

        expected_amount = stock.shares * dividend_rate * fx_rate

        results.append(
            DividendInfo(
                symbol=stock.symbol,
                ex_date=ex_date,
                div_per_share=dividend_rate,
                ex_payout=round(expected_amount, 2)
            )
        )
    
    return results