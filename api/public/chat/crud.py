from fastapi import Depends
from sqlmodel import Session, select, text

from api.database import get_session
from api.public.chat.models import Chat, ChatCreate, ChatRead
from api.utils.logger import logger_config
from api.utils.utility_functions import generate_conversation_id

logger = logger_config(__name__)


async def save_chat(chat: ChatCreate, db: Session = Depends(get_session)):
    conversation_id = generate_conversation_id(chat.sender_id, chat.receiver_id)
    chat_to_db = Chat(
        **chat.model_dump(),
        conversation_id=conversation_id,
    )
    print(chat_to_db)
    db.add(chat_to_db)
    db.commit()
    db.refresh(chat_to_db)
    return ChatRead(**chat_to_db.model_dump())


async def get_chats_by_conversation(
        user_id1: str,
        user_id2: str,
        offset: int = 0,
        limit: int = 20,
        db: Session = Depends(get_session),
):
    conversation_id = generate_conversation_id(user_id1, user_id2)
    chats = db.exec(
        select(Chat).where(Chat.conversation_id==conversation_id).order_by(Chat.id.desc()).offset(offset).limit(limit)
    ).all()
    return chats
