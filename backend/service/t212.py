import requests
import pandas as pd
import yfinance as yf 
from datetime import date
from backend import schemas, config
from backend.service.stock_info import get_stock_info
from backend.service.curr_utils import conv_to_pounds

Holding = schemas.Holding
settings = config.settings

# Fetch current portfolio from Trading 212 API.
async def get_portfolio() -> list[Holding]:
    headers = {"Authorization": settings.t212_key}
    
    # Get all open positions    
    resp = requests.get(url=f"{settings.base_url}/portfolio", headers=headers)
    resp.raise_for_status()
    positions = resp.json()

    holdings: list[Holding] = []

    for pos in positions:
        ticker_full = pos["ticker"]
        if not ticker_full:
            continue
        
        symbol = ticker_full.split("_")[0]
        quantity = float(pos.get("quantity", 0)) 
        price = float(pos.get("averagePrice", 0)) 

        # Skip positions with zero shares
        if quantity <= 0:
            continue

        # Get stock information from yfinance
        stock_info = get_stock_info(symbol)

        # Convert pence to pounds if needed
        avg_price = conv_to_pounds(stock_info, price)

        holding_curr = stock_info["currency"]
        if holding_curr.upper() == "GBX":
            holding_curr == "GBP"
            
            holdings.append(
                Holding(
                    symbol = symbol,
                    shares = quantity,
                    avg_price = avg_price,
                    currency = holding_curr  # Use currency from yfinance
                )
            )

        if stock_info["currency"].upper() == "GBX":
            print(f"{symbol}: {avg_price} GBX → £{avg_price:.2f} GBP")
        else: 
            print(f"{symbol}: {quantity} shares @ {holding_curr}{avg_price:.2f}")
        
    print(f"\nTotal holdings: {len(holdings)}")
    return holdings


def get_dividend_per_share(yf_symbol: str, ex_dividend_date: date):
    ticker = yf.Ticker(yf_symbol)
    info = ticker.info

    # Get dividend history as pandas Series
    dividends_dates = ticker.dividends

    # Convert ex_dividend_date to pandas Timestamp with timezone
    ex_div_ts = pd.Timestamp(ex_dividend_date).tz_localize("UTC")
    
    # Find the exact dividend for the ex-dividend date
    dividend_per_share = None
    
    is_historical_prediction = False

    if ex_div_ts in dividends_dates.index:
        # Exact match found - using actual announced dividend
        dividend_per_share = dividends_dates.loc[ex_div_ts]
    else:
        # No exact match - company hasn"t announced future dividend
        # Get the most recent dividend before the ex-date
        past_dividends = dividends_dates[dividends_dates.index <= ex_div_ts]
        if not past_dividends.empty:
            dividend_per_share = past_dividends.iloc[-1]
            is_historical_prediction = True
            # Add asterisk to indicate this is a prediction based on historical data
            dividend_per_share = f"{dividend_per_share}*"
    
    # Normalize dividend_per_share using conv_to_pounds
    stock_info = get_stock_info(yf_symbol)
    if dividend_per_share is not None:
        if isinstance(dividend_per_share, str):
            # Remove asterisk for calculation but keep it in the display value
            calc_dividend = float(dividend_per_share.rstrip("*"))
            normalized = conv_to_pounds(stock_info, calc_dividend)
            dividend_per_share = f"{normalized}*" if "*" in dividend_per_share else str(normalized)
        else:
            dividend_per_share = conv_to_pounds(stock_info, dividend_per_share)

    print(f"Dividend per share: {dividend_per_share} (Historical prediction: {is_historical_prediction})")
    return dividend_per_share