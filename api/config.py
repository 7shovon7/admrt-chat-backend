import os
import secrets
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = f"AdMrt Chat API - {os.getenv('ENV', 'development').capitalize()}"
    DESCRIPTION: str = "Chat API for AdMrt.com"
    ENV: Literal["development", "staging", "production"] = "development"
    VERSION: str = "0.1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DATABASE_URI: str = "sqlite:///database.db"
    # API_USERNAME: str = "svc_test"
    # API_PASSWORD: str = "superstrongpassword"

    class Config:
        case_sensitive = True


settings = Settings()


class TestSettings(Settings):
    class Config:
        case_sensitive = True


test_settings = TestSettings()
