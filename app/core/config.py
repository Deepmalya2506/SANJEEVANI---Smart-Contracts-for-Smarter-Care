from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str
    GIS_URL: str
    BLOCKCHAIN_URL: str
    CONTRACT_ADDRESS: str
    GROQ_API_KEY: str   # ✅ added

    class Config:
        env_file = ".env"

# 🚨 THIS LINE MUST EXIST
settings = Settings() 