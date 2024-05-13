import json
import sys
from fastapi import WebSocket
from pydantic import TypeAdapter, ValidationError
from sqlmodel import Session

from api.public.chat.crud import save_chat
from api.public.chat.models import ChatCreate
from api.public.ws.schemas import ChatInputSchema, ChatSenderSchema, ClientNotification, DeliveryStatusNotification, ErrorNotification
from api.utils.utility_functions import generate_conversation_id


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
