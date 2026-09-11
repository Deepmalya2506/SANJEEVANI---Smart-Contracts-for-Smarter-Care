from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    # GIS, Blockchain & AI
    GIS_URL: str = Field("http://localhost:8001", validation_alias=AliasChoices("GIS_URL"))
    BLOCKCHAIN_URL: str = Field(
        "http://127.0.0.1:7545",
        validation_alias=AliasChoices("BLOCKCHAIN_URL", "BLOCKCHAIN_RPC_URL"),
    )
    CONTRACT_ADDRESS: str = Field("", validation_alias=AliasChoices("CONTRACT_ADDRESS"))
    GROQ_API_KEY: str = Field("", validation_alias=AliasChoices("GROQ_API_KEY"))

    # Razorpay Payment Gateway
    RAZORPAY_KEY_ID: str | None = Field(None, validation_alias=AliasChoices("RAZORPAY_KEY_ID"))
    RAZORPAY_KEY_SECRET: str | None = Field(None, validation_alias=AliasChoices("RAZORPAY_KEY_SECRET"))
    RAZORPAY_WEBHOOK_SECRET: str | None = Field(None, validation_alias=AliasChoices("RAZORPAY_WEBHOOK_SECRET"))

    # Supabase Direct PostgreSQL Connection
    SUPABASE_HOST: str = Field("", validation_alias=AliasChoices("SUPABASE_HOST", "host"))
    SUPABASE_PORT: int = Field(5432, validation_alias=AliasChoices("SUPABASE_PORT", "port"))
    SUPABASE_DATABASE: str = Field("postgres", validation_alias=AliasChoices("SUPABASE_DATABASE", "database"))
    SUPABASE_USER: str = Field("postgres", validation_alias=AliasChoices("SUPABASE_USER"))
    SUPABASE_PASSWORD: str = Field("", validation_alias=AliasChoices("SUPABASE_PASSWORD", "db_pw"))

    # Supabase REST / Auth / Storage APIs
    SUPABASE_URL: str = Field("", validation_alias=AliasChoices("SUPABASE_URL", "PROJECT_URL"))
    # Supabase Service Role Key (API secret key for admin Auth & Storage)
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        "",
        validation_alias=AliasChoices(
            "SUPABASE_SERVICE_ROLE_KEY",
            "SERVICE_ROLE_KEY",
            "SUPABASE_SECRET_KEY",
            "SECRET_KEY",
        ),
    )
    SUPABASE_STORAGE_BUCKET: str = Field("id-proofs", validation_alias=AliasChoices("SUPABASE_STORAGE_BUCKET"))


settings = Settings()