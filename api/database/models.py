from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from api.database import Base


class UserModel(Base):
    __tablename__ = 'user'

    id = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)


class ConversationModel(Base):
    __tablename__ = 'conversation'

    id = Column(String, primary_key=True, index=True)
    user1 = relationship(UserModel, back_populates='conversations')
    user2 = relationship(UserModel, back_populates='conversations')


class ChatModel(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(String)
    receiver_id = Column(String)
    # conversation_id = Column(String)
    conversation = relationship(ConversationModel, back_populates='chats')
    text = Column(String)
    created_at = Column(Integer)
    delivered = Column(Boolean, default=False)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
