import json
from json.decoder import JSONDecodeError
from typing import List, Optional, Union
from fastapi import WebSocket
from pydantic import BaseModel, TypeAdapter, ValidationError
# import traceback

from api.auth import get_user
from api.config import settings
from api.public.ws import ALLOWED_ACTIONS
from api.public.ws.schemas import ConversationObject, ErrorNotification, FetchConversationRequest, SendMessageRequest, WSObject
from api.utils.logger import logger_config
import httpx


logger = logger_config(__name__)


HEADER_KEY = 'Authorization'


# async def load_conversation_list(token: str):
#     try:
#         async with httpx.AsyncClient() as client:
#             resp = await client.get(
#                 url=f"{settings.AUTH_URI}/chat/",
#                 headers={
#                     HEADER_KEY: 'JWT ' + token
#                 }
#             )
#             if resp.status_code == 200:
#                 return resp.json()
#     except Exception as e:
#         print(e)
#     return None


# async def get_messages_with_a_partner(token: str, partner_id: int):
#     try:
#         async with httpx.AsyncClient() as client:
#             resp = await client.get(
#                 url=f"{settings.AUTH_URI}/chat/?partner_id={partner_id}",
#                 headers={
#                     HEADER_KEY: 'JWT ' + token
#                 }
#             )
#             if resp.status_code == 200:
#                 return resp.json()
#     except Exception as e:
#         print(e)
#     return None


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


# async def mark_conversation_as_delivered(token: str, partner_id: int):
#     try:
#         async with httpx.AsyncClient() as client:
#             resp = await client.post(
#                 url=f"{settings.AUTH_URI}/chat/mark-delivered/",
#                 headers={
#                     HEADER_KEY: 'JWT ' + token
#                 },
#                 json={"partner_id": partner_id}
#             )
#             if resp.status_code == 200:
#                 return resp.json()
#     except Exception as e:
#         print(e)
#     return None


# async def add_connection_data_to_db(user_id: str, connection_id: str):
#     DYNAMO_DB_TABLE.put_item(Item={"userId": user_id, "connectionId": connection_id})
#     return True


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, token: str):
        try:
            # Check the user
            user_data = await get_user(token)
            if user_data and user_data.get('id') is not None:
                # If valid, accept the connection first
                await websocket.accept()
                client_id = str(user_data.get('id'))
                if client_id in self.active_connections:
                    # If connection id is present, just append new connection
                    self.active_connections[client_id].append(websocket)
                else:
                    # create new key with a list containing the new connection
                    self.active_connections[client_id] = [websocket]
                return client_id
        except Exception:
            pass
        return None
    
    def disconnect(self, client_id: str, websocket: WebSocket):
        # check if the id is in the keys
        if client_id in self.active_connections:
            # Loop through the ids and delete whichever connection matches
            # Because single person can be connected from multiple devices
            for websocket_conection in self.active_connections[client_id]:
                if websocket_conection == websocket:
                    self.active_connections[client_id].remove(websocket_conection)
            # If no connections exist in that key, delete the key
            if len(self.active_connections[client_id]) == 0:
                del self.active_connections[client_id]
            return True
        # else attempted to delete such a connection which was not there
        # something unusual
        logger.info(f"Attempted to disconnect a websocket connection from client {client_id}, which was not found on existing websocket list.")
        return False

    async def notify_client(self, client_id: Union[str, int], message: BaseModel):
        client_id = str(client_id)
        if client_id in self.active_connections:
            # Loop through all the connections under the id and notify
            for websocket_connection in self.active_connections[client_id]:
                await websocket_connection.send_text(json.dumps(message.model_dump()))
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
                if str(chat.receiver_id) == client_id:
                    error_message="Messaging ownself isn't supported yet"
                    # It's done!
                else:
                    # Send chat
                    sent_message = await send_chat_message(
                        token=token,
                        msg=chat.model_dump()
                    )
                    if sent_message:
                        # Deliver the message
                        client_is_notified = await self.notify_client(
                            client_id=chat.receiver_id,
                            message=WSObject(
                                action=ALLOWED_ACTIONS.NEW_MESSAGE,
                                body=sent_message
                            )
                        )
                        if client_is_notified:
                            # Mark as delivered in database
                            await mark_message_as_delivered(token, sent_message.get('id'))

            # elif ws_object.action == ALLOWED_ACTIONS.FETCH_CONVERSATION:
            #     req_data: FetchConversationRequest = TypeAdapter(FetchConversationRequest).validate_python(ws_object.body)
            #     conversation = await get_messages_with_a_partner(token, req_data.partner_id)
            #     # Process database object
            #     conversation_object = WSObject(
            #         action = ALLOWED_ACTIONS.CONVERSATION,
            #         body = ConversationObject(
            #             partner_id=req_data.partner_id,
            #             conversation=conversation
            #         )
            #     )
            #     client_notified = await self.notify_client(client_id, conversation_object)
            #     if client_notified:
            #         await mark_conversation_as_delivered(token, req_data.partner_id)
        except JSONDecodeError:
            error_message = "Not a valid JSON formatted String"
        except ValidationError:
            # print(traceback.print_exc())
            error_message = "Request body is not properly formatted"

        await self.handle_error(client_id, error_message)


manager = ConnectionManager()
