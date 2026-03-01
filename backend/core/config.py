"""Application configuration loaded via pydantic settings."""

from typing import List
import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Strongly-typed application settings with environment overrides."""

    # Application
    APP_NAME: str = "Cafe & Greengrocer Stock Tracker"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./backend/stock_tracker.db"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_LEVELS: str = "TRACE,ERROR,WARNING,INFO"
    LOG_FILE_PATH: str = "./backend/logs/app.log"
    LOG_TRACE_CALLS: bool = True

    class Config:
        """Configure environment file loading behavior."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
