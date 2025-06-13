from pydantic import BaseModel
from datetime import date
from typing import Union, Optional

class Holding(BaseModel):
    symbol: str
    shares: float
    avg_price: float
    currency: str

class DividendInfo(BaseModel):
    symbol: str
    ex_dividend_date: Optional[date] = None
    dividend_per_share: Optional[Union[float, str]] = None
    shares: Optional[float] = None
    payout: Optional[float] = None
    is_estimated: bool = False