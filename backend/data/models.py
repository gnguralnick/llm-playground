from sqlalchemy import Column, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from data.database import Base
from data.schemas import Role

class User(Base):
    __tablename__ = 'user'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    chats = relationship('Chat', back_populates='user')
    
class Chat(Base):
    __tablename__ = 'chat'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    default_model = Column(String, nullable=False)
    
    user = relationship('User', back_populates='chats')
    messages = relationship('Message', back_populates='chat')

class Message(Base):
    __tablename__ = 'message'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(Enum(Role), nullable=False)
    content = Column(String, nullable=False)
    model = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chat.id'), nullable=False)
    
    user = relationship('User')
    chat = relationship('Chat', back_populates='messages')