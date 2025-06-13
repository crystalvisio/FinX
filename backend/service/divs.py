from backend.schemas import Holding, DividendInfo
from backend.service.div_calc import DividendCalculator, create_dividend_summary
from typing import List, Dict

async def fetch_dividends(holdings: List[Holding]) -> List[DividendInfo]:
    """
    Fetch Dividend information for all holdings

        - Past Dividends with no shares owned - Skip
        - Past Dividends with shares owned - Calcuate based on historical holdings
        - Future Dividends - Calculate based on current holdings
            - If amount announced: Use actual amount
            - If amount not announec: Estimate based on last dividend (marked with *)
    """

    calculator = DividendCalculator()
    dividends = await calculator.calc_dividends(holdings)

    # Print Summary
    summary = create_dividend_summary(dividends)

    print("\n" + "="*70)
    print("DIVIDEND SUMMARY")
    print("="*70)
    print(f"Total Expected: £{summary['total_expected']:.2f}")
    print(f"Past Dividends: {len(summary['past_dividends'])}")
    print(f"Future Dividends (confirmed): {len(summary['future_dividends'])}")
    print(f"Future Dividends (estimated): {len(summary['estimated_dividends'])}")
    
    if summary['next_dividend']:
        next_div = summary['next_dividend']
        print(f"\nNext Dividend: {next_div.symbol} on {next_div.ex_dividend_date}")
        print(f"Expected: £{next_div.payout:.2f}{'*' if next_div.is_estimated else ''}")
    
    print("="*70 + "\n")
    
    return dividends

# Additional helper functions for the API
async def get_dividend_forecast(holdings: List[Holding]) -> Dict:
    """Get detailed dividend forecast with categorisation"""
    dividends = await fetch_dividends(holdings)
    return create_dividend_summary(dividends)

async def get_upcoming_dividends(holdings: List[Holding], days_ahead: int = 30) -> List[DividendInfo]:
    """Get only upcoming dividends within specified days"""
    from datetime import date, timedelta
    
    dividends = await fetch_dividends(holdings)
    cutoff_date = date.today() + timedelta(days=days_ahead)
    
    upcoming = [
        d for d in dividends 
        if d.ex_dividend_date and d.ex_dividend_date > date.today() and d.ex_dividend_date <= cutoff_date
    ]
    
    return upcoming