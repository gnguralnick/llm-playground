from pydantic import BaseModel, UUID4
from app.schemas.chat import Chat
from app.schemas.api_key import APIKeyBase

class UserBase(BaseModel):
    email: str
    
class UserCreate(UserBase):
    password: str
    
class User(UserBase):
    id: UUID4
    chats: list[Chat] = []
    api_keys: list[APIKeyBase] = []
    
    class Config:
        orm_mode = True
        
        