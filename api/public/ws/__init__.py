from time import time_ns
import json
import sys
from typing import Literal, Optional, Union
from fastapi import WebSocket
from pydantic import BaseModel, TypeAdapter, ValidationError, field_validator, computed_field
from sqlmodel import Session

from api.public.chat.crud import save_chat
from api.public.chat.models import ChatCreate
from api.utils.utility_functions import generate_conversation_id


# Chat Schemas
class ChatBaseSchema(BaseModel):
    text: str


class ChatSenderSchema(ChatBaseSchema):
    sender_id: Union[int, str]
    # created_at: Optional[datetime] = Field(default_factory=datetime.now().timestamp)

    @field_validator('sender_id')
    def convert_to_string(cls, value):
        return str(value)
    
    @computed_field
    @property
    def created_at(self) -> int:
        return time_ns() // 1000000


class ChatReceiverSchema(ChatBaseSchema):
    receiver_id: Union[int, str]

    @field_validator('receiver_id')
    def convert_to_string(cls, value):
        return str(value)


class ChatInputSchema(ChatReceiverSchema):
    sender_id: Optional[Union[int, str, None]] = None
    conversation_id: Optional[Union[str, None]] = None

#### CHAT SCHEMAS ENDS


class DeliveryStatusNotification(BaseModel):
    sent: Optional[bool] = True


class ErrorNotification(BaseModel):
    message: str
    

class ClientNotification(BaseModel):
    notification_type: Literal[
        'ERROR',
        'DELIVERY-STATUS',
    ]
    notification_object: Union[
        ErrorNotification,
        DeliveryStatusNotification,
    ]


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(sys.getsizeof(self.active_connections))

    def disconnect(self, client_id: str):
        try:
            del self.active_connections[client_id]
        except KeyError:
            pass

    async def notify_client(self, client_id: str, notification: ClientNotification):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(notification.model_dump()))
        pass

    async def manage_message(
            self,
            sender_id: str,
            message: str,
            db: Session,
    ):
        try:
            # Generate proper chat object
            message: ChatInputSchema = TypeAdapter(ChatInputSchema).validate_json(message)
            message.sender_id = sender_id
            message.conversation_id = generate_conversation_id(sender_id, message.receiver_id)
            # Send chat
            await self.send_personal_message(message, db)
        except ValidationError:
            notification = ClientNotification(
                notification_type='ERROR',
                notification_object=ErrorNotification(
                    message="Problem with chat object format"
                )
            )
            await self.notify_client(sender_id, notification)

    async def send_personal_message(
            self,
            chat: ChatInputSchema,
            db: Session,
    ):
        if chat.receiver_id in self.active_connections:
            print(chat.model_dump())
            print(ChatSenderSchema(**chat.model_dump()))
            print(ChatSenderSchema(**chat.model_dump()).model_dump())
            print(json.dumps(ChatSenderSchema(**chat.model_dump()).model_dump()))
            await self.active_connections[chat.receiver_id].send_text(
                json.dumps(ChatSenderSchema(**chat.model_dump()).model_dump())
            )
            notification = ClientNotification(
                notification_type='DELIVERY-STATUS',
                notification_object=DeliveryStatusNotification(
                    sent=True
                )
            )
            await self.notify_client(chat.sender_id, notification)

        await save_chat(
            chat=ChatCreate(**chat.model_dump()),
            db=db,
        )

    
manager = ConnectionManager()
