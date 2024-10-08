from abc import ABC, abstractmethod
from pydantic import BaseModel
from collections.abc import Generator
from util import Role, ModelAPI, ModelConfig, MessageContentType
import base64

class MessageContent(BaseModel):
    type: MessageContentType
    order: int
    content: str
    
class TextMessageContent(MessageContent):
    type: MessageContentType = MessageContentType.TEXT
    
class ImageMessageContent(MessageContent):
    type: MessageContentType = MessageContentType.IMAGE
    image_type: str
    
    def get_image(self):
        
        # treat content as a local file path and return base64 encoded image
        with open(self.content, 'rb') as f:
            encoding = base64.b64encode(f.read()).decode('utf-8')
            
        return encoding
            
class Message(BaseModel):
    role: Role
    contents: list[TextMessageContent | ImageMessageContent]
    
class TextMessage(Message):
    contents: list[TextMessageContent]
    
class HumanMessage(Message):
    role: Role = Role.USER
    
class AssistantMessage(Message):
    role: Role = Role.ASSISTANT
    model: str
    
class SystemMessage(Message):
    role: Role = Role.SYSTEM

class ChatModel(ABC):
    """An abstract class for chat models. It defines the basic methods that all chat models should implement.

    Args:
        api_key (str | None, optional): The API key to use with the model. Defaults to None. Only required if the model requires an API key.
    """
    
    human_name: str
    api_name: str
    api_provider: ModelAPI
    requires_key: bool = False
    config: ModelConfig
    config_type: type[ModelConfig]
    
    def __init__(self, api_key: str | None = None, config: ModelConfig | dict | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._api_key = api_key
        if config is not None:
            if isinstance(config, dict):
                config = self.config_type(**config)
            if not isinstance(config, self.config_type):
                raise ValueError('Invalid config type')
            self.config = config

    @abstractmethod
    def chat(self, messages: list[TextMessage]) -> AssistantMessage:
        """Send a list of messages to the model and return the response.

        Args:
            messages (list[Message]): A list of messages to send to the model. The last message in the list is the one to which the model should respond.

        Returns:
            AssistantMessage: The response from the model.
        """
        pass
    
    @classmethod
    def generate_model_info(cls):
        """Generate and return information about the model.

        Returns:
            ModelInfo: Information about the model.
        """
        from chat_models import ModelInfo
        attrs = {x: getattr(cls, x) for x in dir(cls) if not (x.startswith('__') or callable(getattr(cls, x)))}
        return ModelInfo(**attrs)

class StreamingChatModel(ChatModel):
    
    @abstractmethod
    def chat_stream(self, messages: list[TextMessage]) -> Generator[str, None]:
        """Send a list of messages to the model and stream the response.

        Args:
            messages (list[Message]): A list of messages to send to the model. The last message in the list is the one to which the model should respond.

        Yields:
            Generator[str, None]: A generator that yields the response from the model in chunks. The size of the chunks is implementation-dependent.
        """
        pass
    
    @classmethod
    def generate_model_info(cls):
        info = super().generate_model_info()
        info.supports_streaming = True
        return info
    
class ImageChatModel(ChatModel):
    
    @abstractmethod
    def chat(self, messages: list[Message]) -> AssistantMessage:
        pass
    
    @classmethod
    def generate_model_info(cls):
        info = super().generate_model_info()
        info.supports_images = True
        return info
    
class ImageStreamingChatModel(StreamingChatModel, ImageChatModel):
    
    @abstractmethod
    def chat_stream(self, messages: list[Message]) -> Generator[str, None]:
        pass