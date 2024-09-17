from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from database import Base

class User(Base):
    __tablename__ = 'user'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    chats = relationship('Chat', back_populates='user')
    
class Chat(Base):
    __tablename__ = 'chat'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'))
    
    user = relationship('User', back_populates='chats')
    messages = relationship('Message', back_populates='chat')
    
class Message(Base):
    __tablename__ = 'message'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(String)
    content = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'))
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chat.id'))
    
    user = relationship('User')
    chat = relationship('Chat', back_populates='messages')