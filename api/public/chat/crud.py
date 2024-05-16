from typing import List, Optional, Union
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from api.database.models import Chat as ChatModel
from api.database.models import User as UserModel
from api.database.models import Conversation as ConversationModel
from api.public.chat.schemas import ChatCreate, ChatOutput, ChatRead, ConversationCreate
from api.public.user.crud import create_user_in_db
from api.public.user.schemas import UserCreate
from api.public.ws.schemas import ConversationObject, SingleMessageDistribution
from api.utils import generate_conversation_id
from api.utils.logger import logger_config


logger = logger_config(__name__)


async def create_conversation(conversation: ConversationCreate, db: Session):
    conv_to_db = ConversationModel(**conversation.model_dump())
    db.add(conv_to_db)
    db.commit()
    db.refresh(conv_to_db)
    return conv_to_db


async def save_chat(chat: ChatCreate, db: Session):
    conversation = db.query(ConversationModel).filter(ConversationModel.id==chat.conversation_id).first()
    if conversation is None:
        conversation = await create_conversation(ConversationCreate(id=chat.conversation_id), db)
    sender = db.query(UserModel).filter(UserModel.id==chat.sender_id).first()
    if sender is None:
        sender = await create_user_in_db(UserCreate(id=chat.sender_id), db)
    receiver = db.query(UserModel).filter(UserModel.id==chat.receiver_id).first()
    if receiver is None:
        receiver = await create_user_in_db(UserCreate(id=chat.receiver_id), db)
    chat_to_db = ChatModel(
        **chat.model_dump(),
        conversation=conversation,
        sender=sender,
        receiver=receiver,
    )
    db.add(chat_to_db)
    db.commit()
    db.refresh(chat_to_db)
    return ChatOutput(**chat_to_db.as_dict())


async def get_chats_by_conversation(
    user_id1: str,
    user_id2: str,
    db: Session,
    limit: int = 20,
):
    conversation_id = generate_conversation_id(user_id1, user_id2)
    conversation = db.query(ConversationModel).filter(
        ConversationModel.id==conversation_id
    ).limit(limit).first()

    # conversation = [ChatOutput(**chat.as_dict()) for chat in chats]
    
    return conversation.chats


async def fetch_undelivered_chats(
    user_id1: str,
    user_id2: str,
    db: Session,
    limit: int = 500,
):
    conversation_id = generate_conversation_id(user_id1, user_id2)
    chats = db.query(ChatModel).filter(
        and_(
            ChatModel.conversation_id==conversation_id,
            ChatModel.delivered==False
        )
    ).order_by(ChatModel.id.desc()).limit(limit).all()

    conversation = [ChatRead(**chat.as_dict()) for chat in chats]
    
    return conversation


async def update_as_delivered(
    chat_id: int,
    db: Session,
):
    # chat = db.query(Chat).get(chat_id).first()
    db.query(ChatModel).filter_by(id=chat_id).update({'delivered': True})
    db.commit()
    return True


async def update_as_delivered_in_bulk(
    chat_ids: List[int],
    db: Session,
):
    db.bulk_update_mappings(
        ChatModel,
        [{'id': id, 'delivered': True} for id in chat_ids],
    )
    db.commit()
    return True


# async def fetch_initial_conversations(
#     user_id: str,
#     db: Session,
# ):
#     chats_from_db = db.query(Chat).filter(
#         or_(
#             Chat.sender_id==user_id,
#             Chat.receiver_id==user_id,
#         )
#     )


async def fetch_all_unread_conversations(
    user_id: str,
    db: Session,
):
    conversations = db.query(ConversationModel).filter(
        or_(
            ConversationModel.id.contains(f'{user_id}-'),
            ConversationModel.id.contains(f'-{user_id}')
        )
    ).all()
    resp_dict = {}
    for conv in conversations:
        users = conv.id.split('-')
        users.remove(user_id)
        user = db.query(UserModel).filter_by(id=users[0]).first()
        new_messages = db.query(ChatModel).filter(
            and_(
                ChatModel.conversation_id==conv.id,
                ChatModel.delivered==False
            )
        ).count()
        user_dict = user.as_dict()
        user_dict['unread_messages'] = new_messages
        if user.id not in resp_dict:
            resp_dict[user.id] = [user_dict]
        else:
            resp_dict[user.id].append(user_dict)
    return {"summary": resp_dict}
    # chats_from_db = db.query(Chat).filter(
    #     and_(
    #         or_(
    #             Chat.sender_id==user_id,
    #             Chat.receiver_id==user_id
    #         ),
    #         Chat.delivered==False
    #     )
    # ).order_by(Chat.id.desc()).all()
    # conversations = {}
    # for chat in chats_from_db:
    #     chat_obj = SingleMessageDistribution(**chat.as_dict())
    #     if chat_obj.sender_id != user_id:
    #         partner_id = chat_obj.sender_id
    #     else:
    #         partner_id = chat_obj.receiver_id

    #     if partner_id in conversations:
    #         conversations[partner_id].append(chat_obj)
    #     else:
    #         conversations[partner_id] = [chat_obj]

    # # Process to List of conversations
    # conversation_obj = []
    # for key, value in conversations.items():
    #     conversation_obj.append(
    #         ConversationObject(
    #             partner_id=key,
    #             conversation=value
    #         )
    #     )

    # return conversation_obj


async def fetch_single_conversation_upto_a_certain_time(
    user_id1: str,
    user_id2: str,
    db: Session,
    max_timestamp: Optional[Union[int, None]] = None,
    limit: Optional[Union[int, None]] = 100,
):
    conversation_id = generate_conversation_id(user_id1, user_id2)
    if max_timestamp is not None:
        chat_query = db.query(ChatModel).filter(
            and_(
                ChatModel.conversation_id==conversation_id,
                ChatModel.created_at>=max_timestamp
            )
        ).order_by(ChatModel.id.desc())
    else:
        chat_query = db.query(ChatModel).filter(
            and_(
                ChatModel.conversation_id==conversation_id
            )
        ).order_by(ChatModel.id.desc())
    chats = chat_query.limit(limit).all()

    conversation = [chat.as_dict() for chat in chats]
    
    return conversation
