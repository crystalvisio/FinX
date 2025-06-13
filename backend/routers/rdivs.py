from fastapi import APIRouter, HTTPException
from backend import schemas
from backend.service import t212, divs
from icecream import ic

router = APIRouter()

# End point to fetch dividedn information for all holdings
@router.get("/", response_model=list[schemas.DividendInfo])
async def read_dividends():

    try:
        holdings = await t212.get_portfolio()
        dividends = await divs.fetch_dividends(holdings)

        ic(dividends)

        return dividends
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
