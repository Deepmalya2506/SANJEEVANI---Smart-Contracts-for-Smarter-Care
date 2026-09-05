from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    MONGO_URI: str
    DB_NAME: str
    GIS_URL: str
    BLOCKCHAIN_URL: str = Field(
        validation_alias=AliasChoices("BLOCKCHAIN_URL", "BLOCKCHAIN_RPC_URL")
    )
    CONTRACT_ADDRESS: str
    GROQ_API_KEY: str   # ✅ added
    SUPABASE_HOST: str = Field(validation_alias=AliasChoices("SUPABASE_HOST", "host"))
    SUPABASE_PORT: int = Field(5432, validation_alias=AliasChoices("SUPABASE_PORT", "port"))
    SUPABASE_DATABASE: str = Field("postgres", validation_alias=AliasChoices("SUPABASE_DATABASE", "database"))
    SUPABASE_USER: str = Field("postgres", validation_alias=AliasChoices("SUPABASE_USER"))
    SUPABASE_PASSWORD: str = Field(validation_alias=AliasChoices("SUPABASE_PASSWORD", "db_pw"))

# 🚨 THIS LINE MUST EXIST
settings = Settings() 