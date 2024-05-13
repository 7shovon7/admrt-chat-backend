from typing import List
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from api.auth import approve_jwt_token_for_http
from api.database import get_session
from api.public.chat.crud import (
    get_chats_by_conversation,
    save_chat,
)
from api.public.chat.models import ChatCreate, ChatRead
from api.utils.logger import logger_config


router = APIRouter()
logger = logger_config(__name__)


@router.get('/', response_model=List[ChatRead])
async def get_chats(
        receiver_id: str,
        token: str = Depends(approve_jwt_token_for_http),
        offset: int = 0,
        limit: int = Query(default=20, lte=20),
        db: Session = Depends(get_session),
):
    return await get_chats_by_conversation(token, receiver_id, offset, limit, db)


@router.post('/', response_model=ChatRead)
async def save_the_chat(chat: ChatCreate, db: Session = Depends(get_session)):
    return await save_chat(chat, db)
