from fastapi import APIRouter, Depends

from api.auth import approve_jwt_token_for_http, approve_jwt_token_for_ws
from api.public.health import views as health
from api.public.chat import views as chat
from api.public.ws import views as ws

api = APIRouter()


# api.include_router(
#     health.router,
#     prefix="/health",
#     tags=["Health"],
#     # dependencies=[Depends(authent)],
# )
api.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"],
    dependencies=[Depends(approve_jwt_token_for_http)],
)
api.include_router(
    ws.router,
    prefix="/ws",
    tags=["WebSocket"],
    dependencies=[Depends(approve_jwt_token_for_ws)]
)
