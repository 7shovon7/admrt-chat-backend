from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets import ConnectionClosedError

from api.public.ws.connection_manager import manager as connection_manager


router = APIRouter()


@router.websocket('')
async def websocket_endpoint_for_chat(
    *,
    websocket: WebSocket,
    token: str,
):
    client_id = await connection_manager.connect(websocket, token)
    try:
        while client_id is not None:
            message = await websocket.receive_text()
            await connection_manager.handle_message(token, client_id, message)
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id, websocket)
    except ConnectionClosedError:
        pass
