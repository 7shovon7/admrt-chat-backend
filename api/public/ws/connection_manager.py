import json
from json.decoder import JSONDecodeError
from typing import List, Optional
from fastapi import WebSocket
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy.orm import Session
# import traceback

from api.auth.schemas import ClientData
from api.public.chat.crud import (
    fetch_initial_conversations,
    fetch_single_conversation_upto_a_certain_time,
    save_chat,
    update_as_delivered_in_bulk
)
from api.public.chat.schemas import ChatCreate
from api.public.ws import ALLOWED_ACTIONS
from api.public.ws.schemas import ConversationObject, ErrorNotification, FetchConversationRequest, NewMessageDistribution, SendMessageRequest, SingleMessageDistribution, WSObject
from api.utils.logger import logger_config


logger = logger_config(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        try:
            del self.active_connections[client_id]
        except KeyError:
            pass

    async def notify_client(self, client_id: str, message: BaseModel):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message.model_dump()))
            return True
        return False

    async def handle_error(self, client_id: str, error_message: Optional[str] = None):
        if error_message is not None:
            notification = WSObject(
                action='ERROR',
                body=ErrorNotification(
                    message=error_message
                ),
            )
            await self.notify_client(client_id, notification)

    async def handle_message(
            self,
            sender_info: ClientData,
            message: str,
            db: Session,
    ):
        try:
            error_message = None
            # Check if the message is a valid json
            message_object: dict = json.loads(message)
            # Convert to Websocket object
            ws_object: WSObject = TypeAdapter(WSObject).validate_python(message_object)
            # Handle different actions
            if ws_object.action == ALLOWED_ACTIONS.SEND_MESSAGE:
                chat: SendMessageRequest = TypeAdapter(SendMessageRequest).validate_python(ws_object.body)
                # print(chat)
                if chat.receiver_id == sender_info.id:
                    error_message="Messaging ownself isn't supported yet"
                    # It's done!
                else:
                    # Send chat
                    create_chat_for_db = ChatCreate(sender_id=sender_info.id, **chat.model_dump())
                    chat_object = WSObject(
                        action=ALLOWED_ACTIONS.NEW_MESSAGE,
                        body=NewMessageDistribution(
                            **create_chat_for_db.model_dump(),
                            full_name=sender_info.full_name,
                            profile_image=sender_info.profile_image
                        )
                    )
                    client_notified = await self.notify_client(
                        client_id=chat.receiver_id,
                        message=chat_object
                    )
                    # Save chat to db
                    if client_notified:
                        create_chat_for_db.delivered = True
                    await save_chat(
                        chat=create_chat_for_db,
                        db=db,
                    )
            elif ws_object.action == ALLOWED_ACTIONS.FETCH_CONVERSATION:
                req_data: FetchConversationRequest = TypeAdapter(FetchConversationRequest).validate_python(ws_object.body)
                db_conversation = await fetch_single_conversation_upto_a_certain_time(
                    user_id1=sender_info.id,
                    user_id2=req_data.partner_id,
                    max_timestamp=req_data.max_timestamp,
                    limit=req_data.limit,
                    db=db,
                )
                # Process database object received as dict to user specific format
                conversation_object = WSObject(
                    action = ALLOWED_ACTIONS.CONVERSATION,
                    body = ConversationObject(
                        partner_id=req_data.partner_id,
                        conversation=[SingleMessageDistribution(**conv) for conv in db_conversation]
                    )
                )
                client_notified = await self.notify_client(sender_info.id, conversation_object)
                if client_notified:
                    await update_as_delivered_in_bulk(
                        chat_ids=[conv.get('id') for conv in db_conversation],
                        db=db
                    )
        except JSONDecodeError:
            error_message = "Not a valid JSON formatted String"
        except ValidationError:
            # print(traceback.print_exc())
            error_message = "Request body is not properly formatted"

        await self.handle_error(sender_info.id, error_message)

    async def handle_new_connection(self, websocket: WebSocket, client_id: str, db: Session):
        # Accept connection
        await self.connect(websocket, client_id)
        # Fetch and Send all unread conversations
        await self.send_all_unread_conversations(client_id, db)

    async def send_all_unread_conversations(self, client_id: str, db: Session):
        # Fetch all unread conversations
        conversations = await fetch_initial_conversations(client_id, db)
        # # Send
        await self.notify_client(
            client_id=client_id,
            message=WSObject(
                action=ALLOWED_ACTIONS.UNREAD_CONVERSATION,
                body=conversations
            )
        )

manager = ConnectionManager()
