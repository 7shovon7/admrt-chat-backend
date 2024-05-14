from sqlalchemy.orm import Session

from api.database.models import ChatModel
from api.public.chat.schemas import ChatCreate, ChatRead
from api.utils import generate_conversation_id
from api.utils.logger import logger_config


logger = logger_config(__name__)


async def save_chat(chat: ChatCreate, db: Session):
    chat_to_db = ChatModel(**chat.model_dump())
    db.add(chat_to_db)
    db.commit()
    db.refresh(chat_to_db)
    return ChatRead(**chat_to_db.as_dict())


async def get_chats_by_conversation(
        user_id1: str,
        user_id2: str,
        db: Session,
        limit: int = 20,
):
    conversation_id = generate_conversation_id(user_id1, user_id2)
    chats = db.query(ChatModel).filter(
        ChatModel.conversation_id==conversation_id
    ).order_by(ChatModel.id.desc()).limit(limit).all()
    conversation = [ChatRead(**chat.as_dict()) for chat in chats]
    return conversation
