from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import secrets
import os


class Settings(BaseSettings):
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
