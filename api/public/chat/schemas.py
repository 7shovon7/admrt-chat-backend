from time import time_ns
from typing import Union
from pydantic import BaseModel, computed_field, field_validator

from api.utils import generate_conversation_id


class ChatBase(BaseModel):
    text: str


class ChatInput(ChatBase):
    '''
    Validate incoming chat object
    '''
    receiver_id: Union[int, str]


class ChatCreate(ChatInput):
    '''
    Create a complete chat combining sender_id,
    generating conversation_id and adding created_at
    '''
    sender_id: str

    @field_validator('sender_id', 'receiver_id')
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
    

class ChatRead(ChatBase):
    sender_id: str
    receiver_id: str
    conversation_id: str
    text: str
    created_at: int
