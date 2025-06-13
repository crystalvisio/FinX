import time
import requests
import urllib.parse
from datetime import date, datetime
from typing import Dict, Optional, List
from backend.config import settings

def safe_request(url: str, headers: dict, params: dict = None, max_retries: int = 5, delay: int = 2) -> requests.Response:
    """Make API request with rate limiting handling"""
    for attempt in range(max_retries):
        print(f"[{datetime.now().isoformat()}] Requesting: {url}")
        res = requests.get(url=url, headers=headers, params=params)

        if res.status_code == 429:
            retry_after = int(res.headers.get("Retry-After", delay))
            print(f"[{datetime.now().isoformat()}] Rate Limited. Retrying in {retry_after} seconds...")
            time.sleep(retry_after)
            delay = min(delay+1, 10) # Cap at 10 seconds

        else:
            res.raise_for_status()
            time.sleep(delay)
            return res
        
    raise Exception("Too many retries, still getting 429 errors.")

def parse_order(order: dict) -> tuple[str, float]:
    """
    Parse a single order from T212 API.
    
    Returns:
        Tuple of (symbol, signed_quantity, execution_date)
        - symbol: Stock symbol (e.g., "AAPL")
        - signed_quantity: Positive for buy, negative for sell
        - execution_date: When the order was executed
    """

    # Extract ticker and symbol
    ticker_full = order.get("ticker, ")
    if not ticker_full:
        return "", 0.0, None
    
    symbol = ticker_full.split("_")[0]

    # Get the execution date
    exec_timestamp = order.get("dateExecuted") or order.get("dateCreated")
    if not exec_timestamp:
        return symbol, 0.0, None
    
    exec_date = datetime.fromisoformat(exec_timestamp.rstrip("Z"))

    # Skip non-filled orders
    if order.get("status") != "FILLED":
        return symbol, 0.0, exec_date

    # Get the Filled Quantity
    filled_qty = order.get("filledQuantity")
    if filled_qty is None:
        # Calculate from value and price
        filled_value = order.get("filledValue")
        fill_price = order.get("fillPrice")
        if filled_value and fill_price and fill_price != 0:
            filled_qty = abs(filled_value / fill_price)
        else:
            return symbol, 0.0, exec_date
    else:
        filled_qty = float(filled_qty)
    
    # Determine buy or sell
    filled_value = float(order.get("filledValue", 0))
    
    if filled_value > 0:
        return symbol, filled_qty, exec_date # BUY
    elif filled_value < 0:
        return symbol, -filled_qty, exec_date # SELL
    else:
        return symbol, 0.0, exec_date


async def get_portfolio_snapshot(cutoff_date: date) -> Dict[str, float]:
    """Get portfolio holdings as of a specific date by replaying all transactions."""
    
    headers = {"Authorization": settings.t212_key}

    # Convert cutoff date to datetime for comparison
    deadline = datetime.combine(cutoff_date, datetime.min.time())
    deadline_iso = deadline.isoformat() + "Z"

    print(f"Getting portfolio snapshot for {cutoff_date}")

    # Track holdings for each symbol
    snapshot: Dict[str, float] = {}

    # Pagination variables
    next_page: Optional[str] = None
    total_orders = 0
    relevant_orders = 0

    while True:
        if next_page:
            parsed_url = urllib.parse.urlparse(next_page)
            next_page_path = parsed_url.path
            query_params = urllib.parse.parse_qs(parsed_url.query)

            # Convert query params from lists to single values
            query_params_clean = {k: v[0] for k, v in query_params.items()}

            # Remove the base API path if present
            base_api_path = "/api/v0/equity"
            if next_page_path.startswith(base_api_path):
                next_page_path = next_page_path[len(base_api_path)]

            url = f"{settings.base_url}{next_page_path}"
            resp = safe_request(url, headers=headers, params=query_params_clean)

        else:
            url = f"{settings.base_url}/history/orders"
            resp = safe_request(url, headers=headers)
        
        data = resp.json()
        orders = data.get("items", [])
        total_orders += len(orders)

        # Process each order
        for order in orders:
            symbol, signed_qty, exec_date = parse_order(order)

            if not symbol or not exec_date or signed_qty == 0:
                continue

            if exec_date >= deadline:
                continue

            # Update Holdings
            curr_shares = snapshot.get(symbol, 0.0)
            new_shares = curr_shares + signed_qty
            snapshot[symbol] = new_shares
            relevant_orders += 1

            # Log the transaction
            action = "BUY" if signed_qty > 0 else "SELL"
            print(f"{exec_date.date()}: {action} {symbol} {abs(signed_qty):.2f} shares (Total: {new_shares:.2f})")

        next_page = data.get("nextPagePath")
        if not next_page:
            break

        # Remove any positions with 0 or negative shares
        final_snapshot = {symbol: shares for symbol, shares in snapshot.items() if shares > 0}

        # Print Summary
        print(f"\nPortfolio snapshot for {cutoff_date}:")
        print(f"  Total orders processed: {total_orders}")
        print(f"  Orders before cutoff: {relevant_orders}")
        print(f"  Active positions: {len(final_snapshot)}")

        for symbol, shares in sorted(final_snapshot.items()):
            print(f"  {symbol}: {shares:.2f} shares")

        return final_snapshot