from dotenv import load_dotenv
import os
import secrets
from typing import Literal

from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = f"AdMrt Chat API - {os.getenv('ENV', 'production').capitalize()}"
    DESCRIPTION: str = "Chat API for AdMrt.com"
    ENV: Literal["development", "staging", "production"] = os.getenv('ENV', 'production')
    VERSION: str = "0.1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DATABASE_URI: str = "sqlite:///database.db"
    AUTH_URI: str = os.getenv('AUTH_URI', "http://23.239.17.162:8000")
    # API_USERNAME: str = "svc_test"
    # API_PASSWORD: str = "superstrongpassword"

    class Config:
        case_sensitive = True


settings = Settings()
