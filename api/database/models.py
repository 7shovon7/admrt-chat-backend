from sqlalchemy import Column, Integer, String
from api.database import Base


class ChatModel(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(String)
    receiver_id = Column(String)
    conversation_id = Column(String)
    text = Column(String)
    created_at = Column(Integer)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
