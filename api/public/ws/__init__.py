import json
from fastapi import WebSocket
from sqlmodel import Session

from api.database import get_session
from api.public.chat.crud import save_chat
from api.public.chat.models import ChatCreate


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        del self.active_connections[client_id]

    async def send_personal_message(
            self,
            from_client: str,
            to_client: str,
            message: str,
            db: Session = get_session
    ):
        if to_client in self.active_connections:
            await self.active_connections[to_client].send_text(json.dumps({
                "from_id": from_client,
                "message": message,
            }))
            await self.active_connections[from_client].send_text(json.dumps({
                "to_id": to_client,
                "sent": True,
            }))
        # Save to db
        await save_chat(
            chat=ChatCreate(
                sender_id=from_client,
                receiver_id=to_client,
                text=message
            ),
            db=db
        )

    async def send_connection_closure_notification(self, from_client: str, to_client: str):
        if to_client in self.active_connections:
            await self.active_connections[to_client].send_text(json.dumps({
                'from_id': from_client,
                'disconnected': True,
            }))

    
manager = ConnectionManager()
