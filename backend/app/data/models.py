from sqlalchemy import Column, ForeignKey, Integer, String, Enum, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.data.database import Base
from app.util import Role, ModelAPI, MessageContentType

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
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default='now()')
    
    user = relationship('User', back_populates='chats')
    messages = relationship('Message', back_populates='chat', order_by='Message.created_at', cascade='all, delete-orphan')
    
class MessageContent(Base):
    __tablename__ = 'message_content'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(MessageContentType), nullable=False)
    content = Column(JSON, nullable=False)
    image_type = Column(String, nullable=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey('message.id'), nullable=False)
    order = Column(Integer, nullable=False)
    tool_call_id = Column(String, nullable=True)
    
    message = relationship('Message', back_populates='contents')

class Message(Base):
    __tablename__ = 'message'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(Enum(Role), nullable=False)
    model = Column(String, nullable=True)
    config = Column(JSON, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chat.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default='now()')
    
    user = relationship('User')
    chat = relationship('Chat', back_populates='messages')
    contents = relationship('MessageContent', back_populates='message', cascade='all, delete-orphan', order_by='MessageContent.order', lazy='joined')
    
class APIKey(Base):
    __tablename__ = 'api_key'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, nullable=False, unique=True)
    provider = Column(Enum(ModelAPI), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    
    user = relationship('User', back_populates='api_keys')