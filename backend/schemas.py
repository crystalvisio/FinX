from pydantic import BaseModel
from datetime import date

class Holding(BaseModel):
    symbol: str
    shares: float
    avg_price: float
    currency: str

class DividendInfo(BaseModel):
    symbol: str
    ex_date: date
    div_per_share: float
    ex_payout: float