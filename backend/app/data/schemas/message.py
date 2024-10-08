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
    content: list[MessageContentBase]
    model: str | None = None
    config: model_config_type | None = None
    
    class Config:
        use_enum_values = True
    
class MessageCreate(MessageBase):
    content: list[MessageContentCreate]

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

class MessageBuilder:
        
        def __init__(self, role: Role, model: str | None = None, config: model_config_type | None = None):
            self.role = role
            self.model = model
            self.config = config
            self.content = []
            
        def add_text(self, content: str):
            self.content.append(MessageContentCreate(type=MessageContentType.TEXT, content=content, order=len(self.content)))
            return self
        
        def add_image(self, content: str, image_type: str):
            self.content.append(MessageContentCreate(type=MessageContentType.IMAGE, content=content, image_type=image_type, order=len(self.content)))
            return self
        
        def build(self):
            if len(self.content) == 0:
                raise ValueError('No content')
            return MessageCreate(role=self.role, content=self.content, model=self.model, config=self.config)