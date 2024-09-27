from pydantic import BaseModel, UUID4
import datetime
from util import Role, ModelAPI



class MessageBase(BaseModel):
    role: Role
    content: str
    model: str | None = None
    
    class Config:
        use_enum_values = True
    
class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: UUID4
    user_id: UUID4
    chat_id: UUID4
    chat: 'Chat'
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True

class MessageView(MessageBase):
    id: UUID4
    
    class Config:
        orm_mode = True
        
class ChatBase(BaseModel):
    title: str
    default_model: str = 'gpt-4o-mini'
    
class ChatCreate(ChatBase):
    system_prompt: str = """You are a helpful assistant. Format responses using Markdown. 
    You may use latex by wrapping in $ symbols (for inline) or $$ symbols (for block).
    DO NOT use brackets or parentheses to denote latex; you MUST use $ or $$."""

class Chat(ChatBase):
    id: UUID4
    user_id: UUID4
    messages: list[MessageView] = []
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True
        
class ChatView(ChatBase):
    id: UUID4
    user_id: UUID4
    
    class Config:
        orm_mode = True
        
class UserBase(BaseModel):
    email: str
    
class UserCreate(UserBase):
    password: str
    
class User(UserBase):
    id: UUID4
    chats: list[Chat] = []
    
    class Config:
        orm_mode = True
        
        
class ModelAPIKeyBase(BaseModel):
    key: str
    provider: ModelAPI
    
class ModelAPIKeyCreate(ModelAPIKeyBase):
    pass

class ModelAPIKey(ModelAPIKeyBase):
    id: UUID4
    user_id: UUID4
    
    class Config:
        orm_mode = True