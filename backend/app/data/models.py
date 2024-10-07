from sqlalchemy import Column, ForeignKey, String, Enum, DateTime, PickleType
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from data.database import Base
from util import Role, ModelAPI

import uuid

class User(Base):
    __tablename__ = 'user'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    chats = relationship('Chat', back_populates='user', cascade='all, delete-orphan')
    api_keys = relationship('APIKey', back_populates='user', cascade='all, delete-orphan')
    
class Chat(Base):
    __tablename__ = 'chat'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    default_model = Column(String, nullable=False)
    config = Column(PickleType, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default='now()')
    
    user = relationship('User', back_populates='chats')
    messages = relationship('Message', back_populates='chat', order_by='Message.created_at', cascade='all, delete-orphan')

class Message(Base):
    __tablename__ = 'message'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(Enum(Role), nullable=False)
    content = Column(String, nullable=False)
    model = Column(String, nullable=True)
    config = Column(PickleType, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chat.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default='now()')
    
    user = relationship('User')
    chat = relationship('Chat', back_populates='messages')
    
class APIKey(Base):
    __tablename__ = 'api_key'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, nullable=False, unique=True)
    provider = Column(Enum(ModelAPI), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    
    user = relationship('User', back_populates='api_keys')