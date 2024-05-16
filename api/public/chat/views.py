from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.auth import approve_jwt_token_for_http
from api.database import get_session
from api.public.chat.crud import get_chats_by_conversation, save_chat
from api.public.chat.schemas import ChatCreate, ChatInput, ChatOutput
from api.utils.logger import logger_config


router = APIRouter()
logger = logger_config(__name__)


@router.get('', status_code=200)
async def get_chats(
    partner_id: str,
    token: str = Depends(approve_jwt_token_for_http),
    limit: Optional[int] = 20,
    db: Session = Depends(get_session),
):
    return await get_chats_by_conversation(
        user_id1=partner_id,
        user_id2=str(token.get('id')),
        db=db,
        limit=limit,
    )


@router.post('', status_code=201)
async def save_the_chat(
    chat: ChatInput,
    token: str = Depends(approve_jwt_token_for_http),
    db: Session = Depends(get_session),
):
    return await save_chat(
        chat=ChatCreate(sender_id=str(token.get('id')), **chat.model_dump()),
        db=db
    )
