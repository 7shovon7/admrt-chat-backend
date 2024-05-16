from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.auth import approve_jwt_token_for_http
from api.database import get_session
from api.public.user.crud import create_user_in_db, get_user_from_db
from api.public.user.schemas import UserCreate
from api.utils.logger import logger_config


router = APIRouter()
logger = logger_config(__name__)


@router.get('')
async def get_user(
    id: str,
    db: Session = Depends(get_session)
):
    return await get_user_from_db(id, db)


@router.post('')
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_session)
):
    return await create_user_in_db(user, db)
