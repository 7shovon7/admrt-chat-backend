from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from websockets import ConnectionClosedError

from api.auth import approve_jwt_token_for_ws
from api.database import get_session
from api.public.user.crud import update_user_info
from api.public.user.schemas import UserUpdate
from api.public.ws.connection_manager import manager as connection_manager


router = APIRouter()


@router.websocket('')
async def websocket_endpoint_for_chat(
    *,
    websocket: WebSocket,
    token: str = Depends(approve_jwt_token_for_ws),
    db: Session = Depends(get_session),
):
    from_id = str(token.get('id'))
    # have to handle updated user data
    await update_user_info(UserUpdate(**token), db)
    await connection_manager.handle_new_connection(websocket, from_id, db)
    try:
        while True:
            message = await websocket.receive_text()
            await connection_manager.handle_message(from_id, message, db)
    except WebSocketDisconnect:
        connection_manager.disconnect(from_id)
    except ConnectionClosedError:
        pass
