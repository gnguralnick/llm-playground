from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    chats = relationship('Chat', back_populates='user')
    
class Chat(Base):
    __tablename__ = 'chat'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    
    user = relationship('User', back_populates='chats')
    messages = relationship('Message', back_populates='chat')
    
class Message(Base):
    __tablename__ = 'message'
    
    id = Column(Integer, primary_key=True)
    role = Column(String)
    content = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    chat_id = Column(Integer, ForeignKey('chat.id'))
    
    user = relationship('User')
    chat = relationship('Chat', back_populates='messages')