from fastapi import APIRouter, HTTPException
from backend import schemas
from backend.service import divs, t212
from icecream import ic

router = APIRouter()

@router.get("/", response_model=list[schemas.DividendInfo])
async def read_dividends():
    try:
        holdings = await t212.get_portfolio()
        dividends = await divs.fetch_dividends(holdings)

        return dividends
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
