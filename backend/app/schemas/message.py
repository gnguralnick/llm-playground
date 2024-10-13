from pydantic import BaseModel, UUID4, field_validator
from util import Role, MessageContentType
import datetime
import base64
from app.chat_models.model_config import model_config_type

class MessageContent(BaseModel):
    """
    The base class for message content. Message content can be text or an image.
    If message content is an image, the content field should be a local file path.
    """
    type: MessageContentType
    content: str
    
    class Config:
        use_enum_values = True
        
class ImageMessageContent(MessageContent):
    """
    A message content item that represents an image.
    """
    type: MessageContentType = MessageContentType.IMAGE
    content: str
    image_type: str
    
    def get_image(self):
        
        # treat content as a local file path and return base64 encoded image
        with open(self.content, 'rb') as f:
            encoding = base64.b64encode(f.read()).decode('utf-8')
            
        return encoding
    
    @classmethod
    @field_validator('image_type')
    def validate_image_type(cls, value):
        if value is None:
            raise ValueError('Image type is required for image content')
        return value
    
class TextMessageContent(MessageContent):
    """
    A message content item that represents text.
    """
    type: MessageContentType = MessageContentType.TEXT
    content: str
    
message_content_type = ImageMessageContent | TextMessageContent

class MessageContentFull(MessageContent):
    """
    The content of a message. This class is used for messages retrieved from the database.
    """
    id: UUID4
    message_id: UUID4
    
    class Config:
        orm_mode = True

class Message(BaseModel):
    role: Role
    contents: list[message_content_type]
    model: str | None = None
    config: model_config_type | None = None
    
    class Config:
        use_enum_values = True
        
class MessageView(Message):
    id: UUID4
    user_id: UUID4
    chat_id: UUID4
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True

class MessageFull(MessageView):
    contents: list[message_content_type]
    
    class Config:
        orm_mode = True

class MessageBuilder:
    """
    A helper class for building messages. This class makes it easier to create messages with multiple content items.
    
    Example:
    ```
    builder = MessageBuilder(role=Role.USER, model='gpt-3.5', config={'temperature': 0.5})
    builder.add_text('Hello, how are you?')
    builder.add_image('path/to/image.jpg', 'jpg')
    message = builder.build()
    ```
    """
    def __init__(self, role: Role, model: str | None = None, config: model_config_type | None = None):
        self.role = role
        self.model = model
        self.config = config
        self.contents = []
        
    def add_text(self, content: str):
        self.contents.append(TextMessageContent(content=content))
        return self
    
    def add_image(self, content: str, image_type: str):
        self.contents.append(ImageMessageContent(content=content, image_type=image_type))
        return self
    
    def build(self):
        if len(self.contents) == 0:
            raise ValueError('No content')
        return Message(role=self.role, contents=self.contents, model=self.model, config=self.config)