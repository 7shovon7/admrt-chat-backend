from time import time_ns
from typing import Literal, Optional, Union
from pydantic import BaseModel, computed_field, field_validator


class ChatBaseSchema(BaseModel):
    text: str


class ChatSenderSchema(ChatBaseSchema):
    sender_id: Union[int, str]

    @field_validator('sender_id')
    def convert_to_string(cls, value):
        return str(value)
    
    @computed_field
    @property
    def created_at(self) -> int:
        return time_ns() // 1000


class ChatReceiverSchema(ChatBaseSchema):
    receiver_id: Union[int, str]

    @field_validator('receiver_id')
    def convert_to_string(cls, value):
        return str(value)


class ChatInputSchema(ChatReceiverSchema):
    sender_id: Optional[Union[int, str, None]] = None
    conversation_id: Optional[Union[str, None]] = None

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