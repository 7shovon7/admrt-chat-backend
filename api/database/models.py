from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from api.database import Base


user_conversation = Table(
    'user_conversation',
    Base.metadata,
    Column('user_id', ForeignKey('user.id'), primary_key=True),
    Column('conversation_id', ForeignKey('conversation.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'user'

    id = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)

    conversations = relationship('Conversation', secondary='user_conversation', back_populates='users')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Conversation(Base):
    __tablename__ = 'conversation'

    id = Column(String, primary_key=True, index=True)

    users = relationship('User', secondary='user_conversation', back_populates='conversations')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, index=True)

    sender_id = Column(String, ForeignKey('user.id'))
    receiver_id = Column(String, ForeignKey('user.id'))
    conversation_id = Column(String, ForeignKey('conversation.id'))
    text = Column(String)
    created_at = Column(Integer)
    delivered = Column(Boolean, default=False)

    sender = relationship('User', foreign_keys=[sender_id], backref='sent_chats')
    receiver = relationship('User', foreign_keys=[receiver_id], backref='received_chats')
    conversation = relationship('Conversation', backref='chats', foreign_keys=[conversation_id])

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
