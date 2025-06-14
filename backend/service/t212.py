import requests
from datetime import date
from backend import schemas, config
from backend.service.stock_info import get_stock_info
from backend.service.curr_utils import conv_to_pounds

Holding = schemas.Holding
settings = config.settings

async def get_portfolio() -> list[Holding]:
    """Fetch current portfolio from Trading 212 API."""
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

        # Get stock information and convert price to GBP if needed
        stock_info = get_stock_info(symbol)
        avg_price_gbp = conv_to_pounds(stock_info, price)
        
        # All holdings stored in GBP for consistency
        holdings.append(
            Holding(
                symbol=symbol,
                shares=quantity,
                avg_price=avg_price_gbp,  # Always in GBP
                currency="GBP"  # Standardize to GBP
            )
        )
        
    print(f"\nPORTFOLIO LOADED: {len(holdings)} Holdings")
    return holdings