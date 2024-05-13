from datetime import datetime
# from pydantic import computed_field
from typing import Optional, Union
from sqlmodel import Field, SQLModel

# from api.utils.utility_functions import generate_conversation_id


class ChatBase(SQLModel):
    sender_id: str
    receiver_id: str
    text: str

    class Config:
        json_schema_extra = {
            "example": {
                "sender_id": "13",
                "receiver_id": "15",
                "text": "Hello!",
            }
        }


class Chat(ChatBase, table=True):
    id: Optional[Union[int, None]] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    conversation_id: Optional[Union[str, None]] = None

    # @computed_field
    # @property
    # def conversation_id(self) -> str:
    #     return generate_conversation_id(self.sender_id, self.receiver_id)


class ChatCreate(ChatBase):
    pass


class ChatRead(ChatBase):
    id: int
    created_at: Optional[datetime]
    conversation_id: str
