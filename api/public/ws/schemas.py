from typing import Literal, Optional, Union
from pydantic import BaseModel

from api.public.chat.schemas import ChatBase


class ChatToBeSent(ChatBase):
    sender_id: str
    created_at: int


#### CHAT SCHEMAS ENDS


class DeliveryStatusNotification(BaseModel):
    sent: Optional[bool] = True


class ErrorNotification(BaseModel):
    message: str
    

class ClientNotification(BaseModel):
    notification_type: Literal[
        'ERROR',
        'DELIVERY-STATUS',
    ]
    notification_object: Union[
        ErrorNotification,
        DeliveryStatusNotification,
    ]