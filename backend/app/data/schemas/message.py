from pydantic import BaseModel, UUID4
from util import Role, MessageContentType
from chat_models import model_config_type
import datetime

class MessageContentBase(BaseModel):
    type: MessageContentType
    content: str
    image_type: str | None = None
    order: int
    
    class Config:
        use_enum_values = True
    
class MessageContentCreate(MessageContentBase):
    pass

class MessageContent(MessageContentBase):
    id: UUID4
    message_id: UUID4
    
    class Config:
        orm_mode = True

class MessageBase(BaseModel):
    role: Role
    content: MessageContentBase
    model: str | None = None
    config: model_config_type | None = None
    
    class Config:
        use_enum_values = True
    
class MessageCreate(MessageBase):
    content: MessageContentCreate

class Message(MessageBase):
    id: UUID4
    user_id: UUID4
    chat_id: UUID4
    created_at: datetime.datetime
    content: MessageContent
    
    class Config:
        orm_mode = True

class MessageView(MessageBase):
    id: UUID4
    
    class Config:
        orm_mode = True