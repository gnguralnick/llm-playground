from pydantic import BaseModel
from enum import Enum

class Role(Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'

class MessageBase(BaseModel):
    role: Role
    content: str
    
class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    user_id: int
    chat_id: int
    chat: 'Chat'
    
    class Config:
        orm_mode = True
        
class ChatBase(BaseModel):
    title: str
    
class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: int
    user_id: int
    messages: list[Message] = []
    
    class Config:
        orm_mode = True
        
class UserBase(BaseModel):
    email: str
    
class UserCreate(UserBase):
    password: str
    
class User(UserBase):
    id: int
    chats: list[Chat] = []
    
    class Config:
        orm_mode = True