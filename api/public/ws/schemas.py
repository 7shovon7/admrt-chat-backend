from typing import Literal, Optional, Union
from pydantic import BaseModel

from api.public.chat.schemas import ChatBase


class ChatToBeSent(ChatBase):
    sender_id: str
    created_at: int


#### CHAT SCHEMAS ENDS


class ErrorNotification(BaseModel):
    message: str
    
