from time import time_ns
from typing import List, Optional, Union
from pydantic import BaseModel, ValidationError, computed_field, field_validator

from api.public.user.schemas import UserDBModel
from api.utils import generate_conversation_id


# Conversation
class ConversationBase(BaseModel):
    id: str

    @field_validator('id')
    def validate_conversation_id(cls, value):
        if len(value.split('-')) == 2:
            return value
        else:
            raise ValidationError


class ConversationCreate(ConversationBase):
    @property
    def user_ids(self) -> List[str]:
        return self.id.split('-')


class ConversationRead(ConversationBase):
    user_ids: List[str]


# Chat
class ChatBase(BaseModel):
    text: str


class ChatInput(ChatBase):
    '''
    Validate incoming chat object
    '''
    receiver_id: Union[int, str]

    @field_validator('receiver_id')
    def convert_to_string(cls, value):
        return int(value)


class ChatCreate(ChatInput):
    '''
    Create a complete chat combining sender_id,
    generating conversation_id and adding created_at
    '''
    sender_id: Union[str, int]
    delivered: Optional[bool] = False

    @field_validator('sender_id')
    def convert_to_string(cls, value):
        return str(value)
    
    @computed_field
    @property
    def conversation_id(self) -> str:
        return generate_conversation_id(self.sender_id, self.receiver_id)
    
    @computed_field
    @property
    def created_at(self) -> int:
        return time_ns() // 1000
    
    # class Config:
    #     from_attributes: bool = True
    

class ChatOutput(ChatBase):
    sender_id: str
    receiver_id: str
    text: str
    created_at: int
    delivered: bool


class ChatRead(ChatOutput):
    id: int
    conversation_id: str
