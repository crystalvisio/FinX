# Import Dependencies
from fastapi import FastAPI
from backend.routers import rdivs, rportf
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="T212 Dividend Tracker API",
    description="Backend service to fetch Trading 212 portfolio and dividend forecasts",
    version="0.1.0"
)

# Set Up CORS
origins = [ "http://localhost:8000", ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(rdivs.router, prefix="/dividends", tags=["Dividends"])
app.include_router(rportf.router, prefix="/portfolio", tags=["Portfolio"])

# Home Page
@app.get("/")
def home():
    return {"message": "Welcome to Dividend Tracker"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
