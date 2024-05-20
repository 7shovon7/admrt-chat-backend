from dotenv import load_dotenv
import os
import secrets
from typing import Literal


load_dotenv()


class Settings:
    PROJECT_NAME: str = f"AdMrt Chat API - {os.getenv('ENV', 'production').capitalize()}"
    DESCRIPTION: str = "Chat API for AdMrt.com"
    ENV: Literal["development", "staging", "production"] = os.getenv('ENV', 'production')
    VERSION: str = "0.1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DATABASE_URI: str = os.getenv('DATABASE_URI', 'sqlite:///database.db')
    DYNAMO_DB_TABLE: str = os.getenv('DYNAMO_DB_TABLE')
    AUTH_URI: str = os.getenv('AUTH_URI', "https://dvuysrcv6p.us-east-1.awsapprunner.com")

    class Config:
        case_sensitive = True


settings = Settings()
