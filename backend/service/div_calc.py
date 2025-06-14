import requests
import pandas as pd
import yfinance as yf
from tabulate import tabulate
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Optional

from backend.config import settings
from backend.schemas import Holding, DividendInfo
from backend.service.curr_utils import get_yf_symbol, conv_to_pounds, normalise_curr_code
from backend.service.portf_snapshot import get_portfolio_snapshot

class DividendCalculator:
    def __init__(self):
        self.fx_cache = {}

    async def calc_dividends(self, holdings: List[Holding]) -> List[DividendInfo]:
        """
        Calculate expected dividend payouts for all holdings.
        Handle past dividends, future announced, and future estimated
        """

        results = []
        today = date.today()
        # print(f"\nProcessing {len(holdings)} holdings for dividends...")  # DEBUG

        for holding in holdings:
            try:
                dividend_info = await self._process_holdings(holding, today)
                if dividend_info:
                    results.append(dividend_info)
                    # print(f"✓ Successfully processed {holding.symbol}")  # DEBUG
                # else:
                    # print(f"⚠ No dividend data found for {holding.symbol}")  # DEBUG
            
            except Exception as e:
                print(f"✗ Error processing {holding.symbol}: {str(e)}")  # KEEP - Important error
                continue

        # Sort by ex-dividend date
        results.sort(key=lambda x: x.ex_dividend_date if x.ex_dividend_date else date.max)

        # Print final table ONLY
        if results:
            table_data = []
            today = date.today()
            
            for div in results:
                status = "Est *" if div.is_estimated else "✅ Conf"
                date_str = div.ex_dividend_date.strftime("%d-%m-%Y") if div.ex_dividend_date else "N/A"
                
                # Add future/past indicators  
                if div.ex_dividend_date and div.ex_dividend_date > today:
                    date_str = f"{date_str}"
                else:
                    date_str = f"📅 {date_str}"
                    
                table_data.append([
                    div.symbol,
                    date_str,
                    f"£{div.dividend_per_share:.4f}",
                    f"{div.shares:.2f}",
                    f"£{div.payout:.2f}",
                    status
                ])
            
            headers = ["Symbol", "Ex-Date", "Per Share", "Shares", "Payout", "Status"]
            
            print("\n" + "="*80)
            print("📈 DIVIDEND SUMMARY")
            print("="*80)
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Summary stats
            total_future = sum(d.payout for d in results if d.ex_dividend_date and d.ex_dividend_date > today)
            confirmed_count = len([d for d in results if not d.is_estimated and d.ex_dividend_date and d.ex_dividend_date > today])
            estimated_count = len([d for d in results if d.is_estimated and d.ex_dividend_date and d.ex_dividend_date > today])
            
            print(f"💰 Total Expected: £{total_future:.2f}")
            print(f"✅ Confirmed: {confirmed_count} | Estimated: {estimated_count}")
            print("="*80 + "\n")
        else:
            print(f"\n⚠️  No dividends found\n")

        return results

    async def _process_holdings(self, holding: Holding, today: date) -> Optional[DividendInfo]:
        """Process a single holding for dividend calculation"""

        # Get Stock info from yfinance
        yf_symbol = self._get_yf_symbol(holding.symbol)
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        # Get Dividend Data
        ex_date, div_per_share, is_estimated = self._get_dividend_data(ticker, info, today)
        
        if not ex_date or not div_per_share:
            return None

        # Convert dividend amount from pence to pounds if needed
        stock_info = {
            "currency": info.get("currency", ""),
            "yf_symbol": yf_symbol
        }
        div_per_share = round(conv_to_pounds(stock_info, div_per_share), 2)
        # print(f"  Dividend per share: {div_per_share:.2f} GBP")  # DEBUG

        # Get shares for dividend calculation
        shares = round(await self._get_shares_for_dividend(holding.symbol, holding.shares, ex_date, today), 2)
        
        # Calculate payout
        payout = self._calculate_payout(shares, div_per_share, holding.currency)
        
        return DividendInfo(
            symbol=holding.symbol,
            ex_dividend_date=ex_date,
            dividend_per_share=div_per_share,
            shares=shares,
            payout=payout,
            is_estimated=is_estimated
        )

    async def _get_shares_for_dividend(self, symbol:str, curr_shares:float, ex_date: date, today:date) -> float:
        """
        Determine how many shares to use for dividend calculation.
            - Past dividend: use historical snapshot
            - Future dividend: use current holdings
        """
        if ex_date <= today:
            # Past Dividend - Need historical holdings (Owned Shares)
            snapshot = await get_portfolio_snapshot(ex_date)
            historical_shares = snapshot.get(symbol, 0.0)
            return historical_shares
        else:
            return curr_shares

    def _get_yf_symbol(self, symbol: str) -> str: 
        """Convert symbol to yFinance format"""
        return get_yf_symbol(symbol)
    
    def _get_dividend_data(self, ticker: yf.Ticker, info: dict, today: date) -> Tuple[Optional[date], Optional[float], bool]:
        """
        Get dividend data from yfinance with proper handling of past vs future dates.
        Returns (ex_date, dividend_per_share, is_estimated)
        """
        
        # Get dividend history first
        dividends = ticker.dividends
        if dividends.empty:
            # print(f"  No dividend history found")  # DEBUG
            return None, None, False
        
        # Convert dividend dates to simple dates for easier comparison
        dividend_dates = [d.date() for d in dividends.index.to_pydatetime()]
        dividend_amounts = dividends.values
        
        # Get ex_timestamp first
        ex_timestamp = info.get("exDividendDate")
        
        # Calculate ex_date if timestamp exists
        ex_date = None
        if ex_timestamp:
            ex_date = datetime.fromtimestamp(ex_timestamp).date()
        
        # Check if there's a future ex-dividend date announced
        if ex_timestamp and ex_date:
            if ex_date > today:
                # print(f"  ✓ Future dividend detected for {ex_date}")  # DEBUG
                
                # Check if we already have the amount in dividend history
                amount_found = None
                for hist_date, amount in zip(dividend_dates, dividend_amounts):
                    if abs((hist_date - ex_date).days) <= 7:
                        amount_found = amount
                        # print(f"  ✓ Found matching dividend amount: {amount_found:.2f}")  # DEBUG
                        break
                
                if amount_found is not None:
                    # print(f"  → Using ANNOUNCED dividend: {ex_date} = {amount_found:.2f}")  # DEBUG
                    return ex_date, float(amount_found), False
                else:
                    last_amount = float(dividend_amounts[-1])
                    # print(f"  → Using ESTIMATED dividend: {ex_date} = {last_amount:.2f} (estimated)")  # DEBUG
                    return ex_date, last_amount, True
            
            elif ex_date <= today:
                # print(f"  ⚠ Ex-date {ex_date} is in the past, will estimate next one")  # DEBUG
                pass
        else:
            # print(f"  ⚠ No ex-dividend date found in info")  # DEBUG
            pass
        
        # Estimate next ex-date based on dividend frequency
        estimated_ex_date = self._estimate_next_ex_date(dividends, today)
        
        if estimated_ex_date and estimated_ex_date > today:
            last_amount = float(dividend_amounts[-1])
            # print(f"  → ESTIMATED next dividend: {estimated_ex_date} = {last_amount:.2f} (estimated)")  # DEBUG
            return estimated_ex_date, last_amount, True
        else:
            # print(f"  ✗ Could not estimate future dividend")  # DEBUG
            return None, None, False

    def _estimate_next_ex_date(self, dividends: pd.Series, today: date) -> Optional[date]:
        """Estimate next ex dividend date based on historical pattern"""
        if len(dividends) < 2:
            return None
        
        # Calculate average days between dividends
        dates = dividends.index.to_pydatetime()
        intervals = []

        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            intervals.append(interval)

        avg_interval = sum(intervals)/len(intervals)

        # Estimate next date: 
        last_date = dates[-1].date()
        estimated_next = last_date + timedelta(days=int(avg_interval))

        # Only return if its in the future
        return estimated_next if estimated_next > today else None

    def _calculate_payout(self, shares: float, div_per_share: float, stock_curr: str) -> float: 
        """Calculate payout in base currency (GBP)"""
        
        # Calculate all values first
        payout_local = round((shares * div_per_share), 2)
        
        if stock_curr == settings.fx_base_curr:
            fx_conversion = "Not needed"
            fx_rate = 1.0
            final_payout = payout_local
        else:
            fx_rate = self._get_fx_rate(stock_curr, settings.fx_base_curr)
            fx_conversion = f"Rate: {fx_rate}"
            final_payout = round((payout_local * fx_rate), 2)
        
        return final_payout

    def _get_fx_rate(self, from_curr:str, to_curr: str) -> float:
        """Get FX rate with caching""" 
        # Normalize currency codes
        from_curr = normalise_curr_code(from_curr)
        to_curr = normalise_curr_code(to_curr)
        
        if from_curr == to_curr:
            return 1.0

        # Handle pence to pounds conversion
        if from_curr in ["GBX", "GBP"] and to_curr == "GBP":
            return 0.01

        cache_key = f"{from_curr}_{to_curr}"
        if cache_key in self.fx_cache:
            return self.fx_cache[cache_key]

        try:
            resp = requests.get(settings.fx_url, params={"base": from_curr, "symbols": to_curr})
            resp.raise_for_status()
            data = resp.json()
            
            if "rates" not in data:
                raise ValueError("No rates found in response")
                
            rate = data["rates"].get(to_curr)
            if not rate:
                raise ValueError(f"No rate found for {to_curr}")
                
            self.fx_cache[cache_key] = rate
            return rate
        
        except (requests.RequestException, KeyError, ValueError) as e:
            fallbacks = {
                ("USD", "GBP"): 0.79,
                ("EUR", "GBP"): 0.86,
                ("GBX", "GBP"): 0.01,
            }
            
            fallback_rate = fallbacks.get((from_curr, to_curr))
            if fallback_rate:
                return fallback_rate
                
            print(f"No fallback rate available for {from_curr}->{to_curr}, using 1.0")
            return 1.0
        
# Create summary report
def create_dividend_summary(dividends: List[DividendInfo]) -> Dict:
    """Create a summary report of dividends"""
    if not dividends:
        return {
            "total_expected": 0,
            "next_dividend": None,
            "past_dividends": [],
            "future_dividends": [],
            "estimated_dividends": []
        }
    
    today = date.today()
    
    # Split dividends into past and future
    past_dividends = [d for d in dividends if d.ex_dividend_date and d.ex_dividend_date <= today]
    future_dividends = [d for d in dividends if d.ex_dividend_date and d.ex_dividend_date > today]
    
    # Split future dividends into confirmed and estimated
    confirmed_dividends = [d for d in future_dividends if not getattr(d, 'is_estimated', False)]
    estimated_dividends = [d for d in future_dividends if getattr(d, 'is_estimated', False)]
    
    # Calculate total expected
    total_expected = sum(d.payout or 0 for d in future_dividends)
    
    # Get next dividend
    next_dividend = min(future_dividends, key=lambda x: x.ex_dividend_date) if future_dividends else None
    
    return {
        "total_expected": total_expected,
        "next_dividend": next_dividend,
        "past_dividends": past_dividends,
        "future_dividends": confirmed_dividends,
        "estimated_dividends": estimated_dividends
    }

# Usage in your divs.py
async def fetch_dividends_smart(holdings: List[Holding]) -> List[DividendInfo]:
    """Main entry point for dividend fetching"""
    calculator = DividendCalculator()
    return await calculator.calc_dividends(holdings)