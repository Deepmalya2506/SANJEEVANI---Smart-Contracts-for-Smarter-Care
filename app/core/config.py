from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str
    GIS_URL: str
    BLOCKCHAIN_URL: str

    class Config:
        env_file = ".env"

settings = Settings()