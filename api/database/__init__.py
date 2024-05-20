# import boto3
# from boto3.dynamodb.conditions import Attr
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from api.config import settings
from api.utils.logger import logger_config


logger = logger_config(__name__)

# DYNAMO_DB_TABLE = boto3.resource('dynamodb').Table(settings.DYNAMO_DB_TABLE)
# logger.info("DynamoDB has been connected")

engine = create_engine(settings.DATABASE_URI, connect_args={"check_same_thread": False})

# # If not sqlite3
# engine = create_engine(DATABASE_URI)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
