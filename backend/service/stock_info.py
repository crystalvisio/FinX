import yfinance as yf
from cachetools import TTLCache
from backend import config

settings = config.settings
stock_info_cache = TTLCache(maxsize=100, ttl=3600)

def get_stock_info(symbol: str) -> dict:
    if symbol in stock_info_cache:
        return stock_info_cache[symbol]
    yf_symbol = symbol
    if symbol.endswith("l"):
        yf_symbol = f"{symbol[:-1]}.L"
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        currency = info.get("currency", "GBP")
        exchange_name = info.get("fullExchangeName", "")
        exchange = info.get("exchange", "")
        if symbol.upper() == "BTL" and (not currency or exchange == "YHD"):
            currency = "GBX"
            exchange_name = "London Stock Exchange (Fallback)"
            exchange = "LSE"
        is_lse = "LSE" in exchange_name.upper() or "LONDON" in exchange_name.upper()
        result = {
            "currency": currency,
            "exchange": exchange,
            "exchange_name": exchange_name,
            "is_lse": is_lse,
            "yf_symbol": yf_symbol,
            "symbol": symbol
        }
        stock_info_cache[symbol] = result
        return result
    except Exception as e:
        print(f"Error getting stock info for {symbol}: {e}") 