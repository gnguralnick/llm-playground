from pydantic import UUID4, BaseModel, field_validator
from app.util import MessageContentType
import base64


class MessageContent(BaseModel):
    """
    The base class for message content. Message content can be text or an image.
    If message content is an image, the content field should be a local file path.
    """
    type: MessageContentType
    content: str | dict
    
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
    
class ToolResultMessageContent(MessageContent):
    """
    A message content item that represents the result of a tool operation.
    Content should be a dictionary whose structure is defined by the tool.
    """
    type: MessageContentType = MessageContentType.TOOL_RESULT
    content: dict
    tool_use_id: str
    
class ToolCall(BaseModel):
    name: str
    args: dict

class ToolUseMessageContent(MessageContent):
    """
    A message content item that represents the use of a tool.
    Content should be a dictionary whose structure is defined by the tool.
    """
    type: MessageContentType = MessageContentType.TOOL_USE
    content: ToolCall
    id: str
    
message_content_type = ImageMessageContent | TextMessageContent | ToolResultMessageContent | ToolUseMessageContent

class MessageContentFull(MessageContent):
    """
    The content of a message. This class is used for messages retrieved from the database.
    """
    id: UUID4
    message_id: UUID4
    
    class Config:
        orm_mode = True