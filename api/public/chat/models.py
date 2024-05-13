from time import time_ns
from typing import Optional, Union
from sqlmodel import Field, SQLModel


class ChatBase(SQLModel):
    sender_id: str
    receiver_id: str
    text: str


class Chat(ChatBase, table=True):
    id: Optional[Union[int, None]] = Field(default=None, primary_key=True)
    created_at: Optional[int] = Field(default_factory=lambda: time_ns() // 1000)
    conversation_id: Optional[Union[str, None]] = None

    # @computed_field
    # @property
    # def conversation_id(self) -> str:
    #     return generate_conversation_id(self.sender_id, self.receiver_id)


class ChatCreate(ChatBase):
    pass


class ChatRead(ChatBase):
    id: int
    created_at: Optional[int]
    conversation_id: str
