from pydantic import BaseModel, UUID4
from schemas import Chat, ModelAPIKeyBase

class UserBase(BaseModel):
    email: str
    
class UserCreate(UserBase):
    password: str
    
class User(UserBase):
    id: UUID4
    chats: list[Chat] = []
    api_keys: list[ModelAPIKeyBase] = []
    
    class Config:
        orm_mode = True
        
        