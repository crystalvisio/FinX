from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    t212_key: str
    base_url: str
    alpha_vantage_key:str
    polygon_key: str
    iex_key:str

    # FX settings
    fx_url: str
    fx_base_curr: str

    class Config:
        env_file = ".env"

settings = Settings()