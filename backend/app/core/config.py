"""Application configuration loaded from environment files.

Secrets are read once at import time from ``.env`` (preferred) or ``env``
(the file currently shipped in the repo).  Never ``print()`` or log any of
these values.
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Employee OS"
    ENVIRONMENT: str = "development"
    VERSION: str = "1.0.0"

    # ---------------------------------------------------------------- database
    DATABASE_URL: str

    # ---------------------------------------------------------------- supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str = ""

    # ---------------------------------------------------------------- jwt
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Fernet key source for encrypting sensitive DB fields at rest
    # (integration tokens, webhook secrets, SSO client secrets).
    ENCRYPTION_KEY: str = ""

    # ---------------------------------------------------------------- ai / llm
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_AI_MODEL: str = "gpt-5"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_AI_KEY: Optional[str] = None

    # ---------------------------------------------------------------- infra
    REDIS_URL: str = "redis://localhost:6379"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # ---------------------------------------------------------------- integrations
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/gmail/callback"
    OUTLOOK_CLIENT_ID: Optional[str] = None
    OUTLOOK_CLIENT_SECRET: Optional[str] = None
    OUTLOOK_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/outlook/callback"
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/microsoft365/callback"
    GOOGLE_CAL_CLIENT_ID: Optional[str] = None
    GOOGLE_CAL_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CAL_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/google-calendar/callback"
    SLACK_CLIENT_ID: Optional[str] = None
    SLACK_CLIENT_SECRET: Optional[str] = None
    SLACK_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/slack/callback"
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = ""
    ACCOUNTING_BASE_URL: Optional[str] = None
    ACCOUNTING_API_KEY: Optional[str] = None

    # ---------------------------------------------------------------- observability
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 600
    AUDIT_LOG_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=(".env", "env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()