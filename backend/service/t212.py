import requests
from backend import schemas, config
from icecream import ic

Holding = schemas.Holding
settings = config.settings

async def get_portfolio() -> list[Holding]:
    headers = {"Authorization": f"{settings.t212_key}"}
    
    # Debug the base URL
    ic(settings.base_url)

    # Retrieve Accounts
    resp = requests.get(f"{settings.base_url}/account/info", headers=headers)
    resp.raise_for_status()

    acc_data = resp.json()
    base_curr = acc_data.get("currencyCode")

    # Fetch all open positions
    portfolio_url = f"{settings.base_url}/portfolio"
    ic(portfolio_url)
    resp_portfolio = requests.get(portfolio_url, headers=headers)
    resp_portfolio.raise_for_status()
    positions = resp_portfolio.json()

    holdings: list[Holding] = []

    for pos in positions:
        ticker_full = pos.get("ticker")
        if not ticker_full:
            continue
        
        symbol = ticker_full.split("_")[0]
        quantity = float(pos.get("quantity", 0))
        avg_price = float(pos.get("averagePrice", 0))

        if quantity <= 0:
            continue

        holdings.append(
            Holding(
                symbol = symbol,
                shares = quantity,
                avg_price = avg_price,
                currency = base_curr
            )
        )
    return holdings