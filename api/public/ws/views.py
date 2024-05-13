from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlmodel import Session
from websockets import ConnectionClosedError

from api.auth import approve_jwt_token_for_ws
from api.database import get_session
from api.public.ws import manager as connection_manager


router = APIRouter()


@router.websocket('/')
async def websocket_endpoint_for_chat(
    *,
    websocket: WebSocket,
    to_id: str,
    token: str = Depends(approve_jwt_token_for_ws),
    db: Session = Depends(get_session),
):
    from_id = str(token.get('id'))
    await connection_manager.connect(websocket, from_id)
    try:
        while True:
            chat = await websocket.receive_text()
            await connection_manager.send_personal_message(
                from_client=from_id,
                to_client=to_id,
                message=str(chat),
                db=db,
            )
    except WebSocketDisconnect:
        connection_manager.disconnect(from_id)
        await connection_manager.send_connection_closure_notification(
            from_client=from_id,
            to_client=to_id,
        )
    except ConnectionClosedError:
        pass