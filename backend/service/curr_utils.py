"""
Currency detection and conversion utilities
"""
import yfinance as yf

# Special ticker mappings for T212 -> yfinance
TICKER_MAPPINGS = {
    "BTl": "BT-A.L",    # BT Group Class A shares
    "BT": "BT-A.L",
}

def get_yf_symbol(symbol: str) -> str:
    """Convert T212 symbol to yfinance format with special cases"""
    # Check special mappings first
    if symbol in TICKER_MAPPINGS:
        return TICKER_MAPPINGS[symbol]
    
    # Handle UK stocks with 'l' suffix
    if symbol.endswith("l"):
        base_symbol = symbol[:-1]

        # Check if base symbol has special mapping
        if base_symbol in TICKER_MAPPINGS:
            return TICKER_MAPPINGS[base_symbol]
        return f"{base_symbol}.L"
    
    return symbol

def get_stock_info(symbol: str) -> dict:
    """Get stock information from yfinance including currency"""
    # Convert to yfinance format using our mapping
    yf_symbol = get_yf_symbol(symbol)
    
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        if not info or "symbol" not in info:
            print(f"Warning: No data found for {yf_symbol}, trying alternate symbols...")
            
            # Try alternate symbols for problematic tickers
            if symbol.upper() == "BTL" or symbol == "BTl":
                ticker = yf.Ticker("BT-A.L")
                info = ticker.info
                yf_symbol = "BT-A.L"
        
        # Determine currency - yfinance returns "GBX" for pence-denominated UK stocks
        currency = info.get("currency", "GBP")
        exchange_name = info.get("fullExchangeName", "")
        
        return {
            "currency": currency,
            "exchange": info.get("exchange", ""),
            "exchange_name": exchange_name,
            "is_lse": "LSE" in exchange_name.upper() or "LONDON" in exchange_name.upper(),
            "yf_symbol": yf_symbol,
            "symbol": symbol,
            "quote_type": info.get("quoteType", ""),
            "longName": info.get("longName", "")
        }
    except Exception as e:
        print(f"Error getting stock info for {symbol} (tried {yf_symbol}): {e}")
        
        # Return default values
        return {
            "currency": "GBP",
            "exchange": "",
            "exchange_name": "",
            "is_lse": False,
            "yf_symbol": yf_symbol,
            "symbol": symbol,
            "quote_type": "",
            "longName": ""
        }

def normalise_curr_code(currency:str) -> str:
    """
    Normalise currency codes to handle case sensitivity properly
    Returns standardise currency codes
    """
    if not currency:
        return "GBP"
    # Handle UK Pence variants before any case conversion
    if currency in ["GBp", "GBx", "gbp", "gbx", "GBX"]:
        return "GBX"

    return currency.upper()

def conv_to_pounds(stock_info: dict, price: float) -> float:
    """Convert pence to pounds for UK stocks"""
    raw_curr = stock_info.get("currency", "")
    normalised_curr = normalise_curr_code(raw_curr)

    if normalised_curr == "GBX":
        converted_price = price / 100
        return converted_price
    else:
        return price