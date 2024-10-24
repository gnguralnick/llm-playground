from abc import ABC, abstractmethod
from collections.abc import Generator
from app.util import ModelAPI
from app.schemas.model_config import ModelConfig, ModelConfigWithTools

from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from schemas import Message

class ChatModel(ABC):
    """An abstract class for chat models. It defines the basic methods that all chat models should implement.

    Args:
        api_key (str | None, optional): The API key to use with the model. Defaults to None. Only required if the model requires an API key.
    """
    
    human_name: str
    api_name: str
    api_provider: ModelAPI
    requires_key: bool = False
    config: ModelConfig # to be overridden by subclasses
    config_type: type[ModelConfig] # to be overridden by subclasses
    
    def __init__(self, api_key: str | None = None, config: ModelConfig | dict | None = None, **kwargs) -> None:
        """Construct an instance of ChatModel.

        Args:
            api_key (str | None, optional): The API Key needed to interact with the chat model. Defaults to None.
            config (ModelConfig | dict | None, optional): The configuration used to initialize the chat model. Defaults to None (model default config).

        Raises:
            ValueError: If the provided config is not valid for the model type. Each subclass should define its own config type.
        """
        super().__init__(**kwargs)
        self._api_key = api_key
        if config is not None:
            if isinstance(config, dict):
                config = self.config_type(**config)
            elif not isinstance(config, self.config_type):
                raise ValueError(f'Invalid config type {type(config)} for model {self.api_name}, expected {self.config_type}')
            self.config = config

    @abstractmethod
    def chat(self, messages: Sequence['Message']) -> 'Message':
        """Send a list of messages to the model and return the response.

        Args:
            messages (Sequence[Message]): A list of messages to send to the model. The last message in the list is the one to which the model should respond.

        Returns:
            Message: The response from the model.
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
    """
    A chat model that supports streaming.
    """
    
    @abstractmethod
    def chat_stream(self, messages: Sequence['Message']) -> Generator[str, None]:
        """Send a list of messages to the model and stream the response.

        Args:
            messages (Sequence[Message]): A list of messages to send to the model. The last message in the list is the one to which the model should respond.

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
    """
    A chat model that supports images.
    """
    
    @classmethod
    def generate_model_info(cls):
        info = super().generate_model_info()
        info.supports_images = True
        return info
    
class ToolChatModel(ChatModel):
    config: ModelConfigWithTools
    config_type: type[ModelConfigWithTools]
    
    def __init__(self, api_key: str | None = None, config: ModelConfigWithTools | dict | None = None, **kwargs) -> None:
        super().__init__(api_key, config, **kwargs)
    
    @classmethod
    def generate_model_info(cls):
        info = super().generate_model_info()
        info.supports_tools = True
        return info