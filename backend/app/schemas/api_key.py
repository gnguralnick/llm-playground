from pydantic import BaseModel, UUID4
from app.util import ModelAPI, ToolAPI

class APIKeyBase(BaseModel):
    provider: ModelAPI | ToolAPI
    
    class Config:
        use_enum_values = True
    
class APIKeyCreate(APIKeyBase):
    key: str

class APIKey(APIKeyBase):
    id: UUID4
    user_id: UUID4
    key: str
    
    class Config:
        orm_mode = True