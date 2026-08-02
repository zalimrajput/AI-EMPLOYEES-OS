from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Employee OS"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str = ""

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Fernet key source for encrypting sensitive DB fields at rest
    # (integration tokens, webhook secrets, SSO client secrets).
    ENCRYPTION_KEY: str = ""

    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"


settings = Settings()