from typing import Any, List, Optional, Union
from pydantic import BaseModel, ValidationError, field_validator

from api.public.chat.schemas import ChatInput
from api.public.ws import ALLOWED_ACTIONS


# 'SEND-MESSAGE'
class SendMessageRequest(ChatInput):
    pass


# General chat object
class SingleMessageDistribution(SendMessageRequest):
    sender_id: str
    created_at: int


# 'NEW-MESSAGE'
class NewMessageDistribution(SingleMessageDistribution):
    full_name: Optional[Union[str, None]] = None
    profile_image: Optional[Union[str, None]] = None


# 'CONVERSATION'
class ConversationObject(BaseModel):
    partner_id: Union[str, int]
    conversation: List[dict]

    @field_validator('partner_id')
    def convert_to_string(cls, value):
        return int(value)


# 'UNREAD-CONVERSATION'
class UnreadConversationDistribution(ConversationObject):
    pass


# 'FETCH-CONVERSATION'
class FetchConversationRequest(BaseModel):
    partner_id: Union[str, int]
    max_timestamp: Optional[Union[int, None]] = None
    limit: Optional[Union[int, None]] = 100

    @field_validator('partner_id')
    def convert_to_string(cls, value):
        return int(value)


# Any incoming or outgoing message object
class WSObject(BaseModel):
    action: str
    body: Any

    @field_validator('action')
    def validate_action(cls, value):
        value = value.upper()
        if value in ALLOWED_ACTIONS.all_actions:
            return value
        else:
            raise ValidationError


#### CHAT SCHEMAS ENDS


class ErrorNotification(BaseModel):
    message: str
    
