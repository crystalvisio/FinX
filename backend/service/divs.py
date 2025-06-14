from datetime import date, timedelta
from typing import List, Dict
from tabulate import tabulate

from backend.schemas import Holding, DividendInfo
from backend.service.div_calc import DividendCalculator, create_dividend_summary

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

    summary_data = [
        ["💰 Total Expected", f"£{summary['total_expected']:.2f}"],
        ["📅 Past Dividends", f"{len(summary['past_dividends'])}"],
        ["✅ Future (Confirmed)", f"{len(summary['future_dividends'])}"],
        ["🔮 Future (Estimated)", f"{len(summary['estimated_dividends'])}"]
    ]

    if summary['next_dividend']:
        next_div = summary['next_dividend']
        status = "*" if next_div.is_estimated else ""
        summary_data.append(["🔜 Next Dividend", f"{next_div.symbol} on {next_div.ex_dividend_date} (£{next_div.payout:.2f}{status})"])

    print("\n" + "="*50)
    print("📊 DIVIDEND SUMMARY")
    print("="*50)
    print(tabulate(summary_data, headers=["Metric", "Value"], tablefmt="simple"))
    print("="*50 + "\n")
    
    return dividends

# Additional helper functions for the API
async def get_dividend_forecast(holdings: List[Holding]) -> Dict:
    """Get detailed dividend forecast with categorisation"""

    calculator = DividendCalculator()
    dividends = await calculator.calc_dividends(holdings)
    return create_dividend_summary(dividends)

async def get_upcoming_dividends(holdings: List[Holding], days_ahead: int = 30) -> List[DividendInfo]:
    """Get only upcoming dividends within specified days"""

    calculator = DividendCalculator()
    dividends = await calculator.calc_dividends(holdings)
    cutoff_date = date.today() + timedelta(days=days_ahead)
    
    upcoming = [
        d for d in dividends 
        if d.ex_dividend_date and d.ex_dividend_date > date.today() and d.ex_dividend_date <= cutoff_date
    ]
    
    return upcoming