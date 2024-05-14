import json
from fastapi import WebSocket
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from api.public.chat.crud import save_chat
from api.public.chat.schemas import ChatCreate, ChatInput
from api.public.ws.schemas import ChatToBeSent, ClientNotification, DeliveryStatusNotification, ErrorNotification


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
            message: ChatInput = TypeAdapter(ChatInput).validate_json(message)
            if message.receiver_id == sender_id:
                notification = ClientNotification(
                    notification_type='ERROR',
                    notification_object=ErrorNotification(
                        message="Messaging ownself isn't supported yet"
                    )
                )
                await self.notify_client(sender_id, notification)
            else:
                # Send chat
                await self.send_personal_message(
                    chat=ChatCreate(sender_id=sender_id, **message.model_dump()),
                    db=db,
                )
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
            chat: ChatCreate,
            db: Session,
    ):
        # Send message to receiver
        if chat.receiver_id in self.active_connections:
            await self.active_connections[chat.receiver_id].send_text(
                json.dumps(ChatToBeSent(**chat.model_dump()).model_dump())
            )
            # Send delivery status to sender
            if chat.sender_id in self.active_connections:
                notification = ClientNotification(
                    notification_type='DELIVERY-STATUS',
                    notification_object=DeliveryStatusNotification(
                        sent=True
                    )
                )
                await self.notify_client(chat.sender_id, notification)
        # Save chat to db
        await save_chat(
            chat=ChatCreate(**chat.model_dump()),
            db=db,
        )

    
manager = ConnectionManager()
