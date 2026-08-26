from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "VersionRAG"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default="versionrag-super-secure-production-secret-key-change-in-prod-1234567890")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day for convenience
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    VERIFY_TOKEN_EXPIRE_HOURS: int = 24
    RESET_TOKEN_EXPIRE_HOURS: int = 2

    # SMTP Email (Gmail App Password)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_NAME: str = "VersionRAG Platform"
    EMAILS_FROM_EMAIL: Optional[str] = None
    OTP_EXPIRE_MINUTES: int = 15
    OTP_LENGTH: int = 6

    # Database (Postgres with SQLite automatic fallback)
    DATABASE_URL: str = Field(
        default="sqlite:///./versionrag.db",
        description="SQLAlchemy database connection URL (Postgres or SQLite fallback)"
    )
    SQL_DEBUG: bool = False

    # Redis / Job Queue
    REDIS_URL: Optional[str] = Field(default=None, description="Optional Redis URL for caching & rate limiting")
    
    # Storage
    STORAGE_LOCAL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage_data")
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "md", "markdown", "txt", "html", "htm", "docx", "json"]

    # AI / LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    USE_MOCK_AI_IF_NO_KEY: bool = True

    # Rate Limiting
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
