from fastapi import APIRouter, HTTPException
from backend import schemas
from backend.service import t212

router = APIRouter()

@router.get("/", response_model=list[schemas.Holding])
async def read_portfolio():
    try:
        portfolio = await t212.get_portfolio()
        return portfolio
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))