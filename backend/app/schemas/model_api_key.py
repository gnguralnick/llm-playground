from pydantic import BaseModel, UUID4
from app.util import ModelAPI

class ModelAPIKeyBase(BaseModel):
    provider: ModelAPI
    
class ModelAPIKeyCreate(ModelAPIKeyBase):
    key: str

class ModelAPIKey(ModelAPIKeyBase):
    id: UUID4
    user_id: UUID4
    key: str
    
    class Config:
        orm_mode = True