import json
from json.decoder import JSONDecodeError
from typing import List, Optional, Union
from fastapi import WebSocket
from pydantic import BaseModel, TypeAdapter, ValidationError
# import traceback

from api.config import settings
from api.public.ws import ALLOWED_ACTIONS
from api.public.ws.schemas import ConversationObject, ErrorNotification, FetchConversationRequest, SendMessageRequest, WSObject
from api.utils.logger import logger_config
import httpx


logger = logger_config(__name__)


HEADER_KEY = 'Authorization'


async def load_conversation_list(token: str):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url=f"{settings.AUTH_URI}/chat/",
                headers={
                    HEADER_KEY: 'JWT ' + token
                }
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(e)
    return None


async def get_messages_with_a_partner(token: str, partner_id: int):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url=f"{settings.AUTH_URI}/chat/?partner_id={partner_id}",
                headers={
                    HEADER_KEY: 'JWT ' + token
                }
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(e)
    return None


async def send_chat_message(token: str, msg: dict):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url=f"{settings.AUTH_URI}/chat/",
                headers={
                    HEADER_KEY: 'JWT ' + token
                },
                json=msg
            )
            if resp.status_code == 201:
                return resp.json()
    except Exception as e:
        print(e)
    return None


async def mark_message_as_delivered(token: str, chat_id: int):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                url=f"{settings.AUTH_URI}/chat/{chat_id}/",
                headers={
                    HEADER_KEY: 'JWT ' + token
                },
                json={"delivered": True}
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(e)
    return None


async def mark_conversation_as_delivered(token: str, partner_id: int):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url=f"{settings.AUTH_URI}/chat/mark-delivered/",
                headers={
                    HEADER_KEY: 'JWT ' + token
                },
                json={"partner_id": partner_id}
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(e)
    return None


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, token: str):
        try:
            # Send the token to main api and grab the response [probably grab the conversation list response here]
            loaded_conversations = await load_conversation_list(token)
            # If valid, accept and add the user id and websocket connection id to db
            if loaded_conversations:
                client_id = str(loaded_conversations['user_id'])
                await websocket.accept()
                self.active_connections[client_id] = websocket
                await self.notify_client(
                    client_id=client_id,
                    message=WSObject(
                        action=ALLOWED_ACTIONS.UNREAD_CONVERSATION,
                        body={"summary": loaded_conversations['conversations']}
                    )
                )
                return client_id
        except Exception:
            pass
        return None

    def disconnect(self, client_id: str):
        try:
            del self.active_connections[client_id]
        except KeyError:
            pass

    async def notify_client(self, client_id: Union[str, int], message: BaseModel):
        client_id = str(client_id)
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
            token: str,
            client_id: str,
            message: str,
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
                if chat.receiver_id == client_id:
                    error_message="Messaging ownself isn't supported yet"
                    # It's done!
                else:
                    # Send chat
                    sent_message = await send_chat_message(
                        token=token,
                        msg=chat.model_dump()
                    )
                    client_notified = False
                    if sent_message:
                        chat_object = WSObject(
                            action=ALLOWED_ACTIONS.NEW_MESSAGE,
                            body=sent_message
                        )
                        client_notified = await self.notify_client(
                            client_id=chat.receiver_id,
                            message=chat_object
                        )
                    # Save chat to db
                    if client_notified:
                        await mark_message_as_delivered(token, sent_message.get('id'))

            elif ws_object.action == ALLOWED_ACTIONS.FETCH_CONVERSATION:
                req_data: FetchConversationRequest = TypeAdapter(FetchConversationRequest).validate_python(ws_object.body)
                conversation = await get_messages_with_a_partner(token, req_data.partner_id)
                # Process database object
                conversation_object = WSObject(
                    action = ALLOWED_ACTIONS.CONVERSATION,
                    body = ConversationObject(
                        partner_id=req_data.partner_id,
                        conversation=conversation
                    )
                )
                client_notified = await self.notify_client(client_id, conversation_object)
                if client_notified:
                    await mark_conversation_as_delivered(token, req_data.partner_id)
        except JSONDecodeError:
            error_message = "Not a valid JSON formatted String"
        except ValidationError:
            # print(traceback.print_exc())
            error_message = "Request body is not properly formatted"

        await self.handle_error(client_id, error_message)


manager = ConnectionManager()
