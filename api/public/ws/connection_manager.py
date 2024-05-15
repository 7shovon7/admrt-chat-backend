import json
from json.decoder import JSONDecodeError
from typing import Any, List, Literal, Optional, Union
from fastapi import WebSocket
from pydantic import BaseModel, TypeAdapter, ValidationError, field_validator
from sqlalchemy.orm import Session

from api.public.chat.crud import fetch_conversation_upto_a_certain_time, save_chat
from api.public.chat.schemas import ChatCreate, ChatInput, ChatRead
from api.public.ws.schemas import ChatToBeSent, ErrorNotification

ALLOWED_ACTION = [
    'SEND',
    'FETCH',
    # for server only
    'MESSAGE',
    'CONVERSATION',
    'ERROR',
]


class WSObject(BaseModel):
    action: str
    body: Any

    @field_validator('action')
    def validate_action(cls, value):
        value = str(value).upper()
        if value in ALLOWED_ACTION:
            return value
        else:
            raise ValidationError
        

class FetchObjectRequest(BaseModel):
    receiver_id: Union[str, int]
    last_timestamp: int

    @field_validator('receiver_id')
    def convert_to_string(cls, value):
        return str(value)


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

    async def notify_client(self, client_id: str, notification: WSObject):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(notification.model_dump()))
        pass

    async def handle_error(self, client_id: str, error_message: Optional[str] = None):
        if error_message is not None:
            notification = WSObject(
                action='ERROR',
                body=ErrorNotification(
                    message=error_message
                ),
            )
            await self.notify_client(client_id, notification)

    async def send_personal_message(
            self,
            chat: ChatCreate,
            db: Session,
    ):
        # Send message to receiver
        if chat.receiver_id in self.active_connections:
            await self.active_connections[chat.receiver_id].send_text(
                json.dumps(ChatToBeSent(**chat.model_dump()).model_dump())
            )
        # Save chat to db
        await save_chat(
            chat=ChatCreate(**chat.model_dump()),
            db=db,
        )

    async def send_conversation(
            self,
            receiver_id: str,
            conversation: List[ChatRead],
    ):
        # Send message to receiver
        if receiver_id in self.active_connections:
            await self.active_connections[receiver_id].send_text(
                json.dumps(WSObject(action='CONVERSATION', body=conversation).model_dump())
            )

    async def handle_message(
            self,
            sender_id: str,
            message: str,
            db: Session,
    ):
        try:
            error_message = None
            # Check if the message is a valid json
            message_object: dict = json.loads(message)
            # Convert to Websocket object
            ws_object: WSObject = TypeAdapter(WSObject).validate_python(message_object)
            if ws_object.action == 'SEND':
                message: ChatInput = TypeAdapter(ChatInput).validate_python(ws_object.body)
                if message.receiver_id == sender_id:
                    error_message="Messaging ownself isn't supported yet"
                else:
                    # Send chat
                    await self.send_personal_message(
                        chat=ChatCreate(sender_id=sender_id, **message.model_dump()),
                        db=db,
                    )
            elif ws_object.action == 'FETCH':
                fetch_req_data: FetchObjectRequest = TypeAdapter(FetchObjectRequest).validate_python(ws_object.body)
                conversation = await fetch_conversation_upto_a_certain_time(
                    user_id1=sender_id,
                    user_id2=fetch_req_data.receiver_id,
                    last_timestamp=fetch_req_data.last_timestamp,
                    db=db,
                )
                await self.send_conversation(sender_id, conversation)
        except JSONDecodeError:
            error_message = "Not a valid json"
        except ValidationError:
            error_message = "Problem with chat object format"

        await self.handle_error(sender_id, error_message)


manager = ConnectionManager()
