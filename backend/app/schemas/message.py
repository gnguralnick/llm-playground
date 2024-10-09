from pydantic import BaseModel, UUID4, field_validator
from util import Role, MessageContentType
import typing
import datetime
import base64
from chat_models import model_config_type

class MessageContentBase(BaseModel):
    type: MessageContentType
    content: str
    image_type: str | None = None
    
    class Config:
        use_enum_values = True
        
    def get_image(self):
        if self.type != MessageContentType.IMAGE:
            raise ValueError('Content is not an image')
        
        # treat content as a local file path and return base64 encoded image
        with open(self.content, 'rb') as f:
            encoding = base64.b64encode(f.read()).decode('utf-8')
            
        return encoding
    
    @classmethod
    @field_validator('image_type')
    def validate_image_type(cls, value, values):
        if values['type'] == MessageContentType.IMAGE and value is None:
            raise ValueError('Image type is required for image content')
        return value
    
class MessageContentCreate(MessageContentBase):
    pass

class MessageContent(MessageContentBase):
    id: UUID4
    message_id: UUID4
    
    class Config:
        orm_mode = True

class MessageBase(BaseModel):
    role: Role
    contents: list[MessageContentBase]
    model: str | None = None
    config: model_config_type | None = None
    
    class Config:
        use_enum_values = True
    
class MessageCreate(MessageBase):
    contents: list[MessageContentCreate]

class Message(MessageBase):
    id: UUID4
    user_id: UUID4
    chat_id: UUID4
    created_at: datetime.datetime
    contents: list[MessageContent]
    
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
            self.contents = []
            
        def add_text(self, content: str):
            self.contents.append(MessageContentCreate(type=MessageContentType.TEXT, content=content))
            return self
        
        def add_image(self, content: str, image_type: str):
            self.contents.append(MessageContentCreate(type=MessageContentType.IMAGE, content=content, image_type=image_type))
            return self
        
        def build(self):
            if len(self.contents) == 0:
                raise ValueError('No content')
            return MessageCreate(role=self.role, contents=self.contents, model=self.model, config=self.config)