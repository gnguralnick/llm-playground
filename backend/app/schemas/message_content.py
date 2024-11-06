from typing import Literal
from pydantic import UUID4, BaseModel, field_validator
from app.util import MessageContentType
import base64
from pypdf import PdfReader
import docx2txt


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
    type: Literal[MessageContentType.IMAGE, MessageContentType.FILE] = MessageContentType.IMAGE
    content: str
    image_type: str
    
    def is_image(self):
        return self.type == MessageContentType.IMAGE
    
    def get_image(self):
        
        if not self.image_type in ['image/png', 'image/jpg', 'image/jpeg', 'image/gif']:
            raise ValueError('Invalid image type')
        
        # treat content as a local file path and return base64 encoded image
        with open(self.content, 'rb') as f:
            encoding = base64.b64encode(f.read()).decode('utf-8')
            
        return encoding
    
    def get_file_content(self):
        if not self.image_type in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']:
            raise ValueError('Invalid file type')
        
        if self.image_type == 'application/pdf':
            reader = PdfReader(self.content)
            content = ''
            for page in reader.pages:
                content += page.extract_text()
            return content
        elif self.image_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': # docx
            return docx2txt.process(self.content)
        elif self.image_type == 'text/plain':
            with open(self.content, 'r') as f:
                return f.read()
        
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
    type: Literal[MessageContentType.TEXT] = MessageContentType.TEXT
    content: str
    
class ToolResultMessageContent(MessageContent):
    """
    A message content item that represents the result of a tool operation.
    Content should be a dictionary whose structure is defined by the tool.
    """
    type: Literal[MessageContentType.TOOL_RESULT] = MessageContentType.TOOL_RESULT
    content: object
    tool_call_id: str
    
class ToolCall(BaseModel):
    name: str
    args: dict

class ToolCallMessageContent(MessageContent):
    """
    A message content item that represents the use of a tool.
    Content should be a dictionary whose structure is defined by the tool.
    """
    type: Literal[MessageContentType.TOOL_CALL] = MessageContentType.TOOL_CALL
    content: ToolCall
    tool_call_id: str
    
message_content_type = ImageMessageContent | TextMessageContent | ToolResultMessageContent | ToolCallMessageContent

class MessageContentFull(MessageContent):
    """
    The content of a message. This class is used for messages retrieved from the database.
    """
    id: UUID4
    message_id: UUID4
    
    class Config:
        orm_mode = True