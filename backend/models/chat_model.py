from abc import ABC, abstractmethod
from pydantic import BaseModel
from collections.abc import Generator
from util import Role, ModelAPI
    
class Message(BaseModel):
    role: Role
    content: str
    
class HumanMessage(Message):
    role: Role = Role.USER
    
class AssistantMessage(Message):
    role: Role = Role.ASSISTANT
    model: str
    
class SystemMessage(Message):
    role: Role = Role.SYSTEM
    
class ModelInfo(BaseModel):
    human_name: str
    api_name: str
    api_provider: ModelAPI
    requires_key: bool = False
    supports_streaming: bool = False

class ChatModel(ABC):
    """An abstract class for chat models. It defines the basic methods that all chat models should implement.

    Args:
        api_key (str | None, optional): The API key to use with the model. Defaults to None. Only required if the model requires an API key.
    """
    
    human_name: str
    api_name: str
    api_provider: ModelAPI
    requires_key: bool = False
    supports_streaming: bool = False
    
    def __init__(self, api_key: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._api_key = api_key

    @abstractmethod
    def chat(self, messages: list[Message]) -> AssistantMessage:
        """Send a list of messages to the model and return the response.

        Args:
            messages (list[Message]): A list of messages to send to the model. The last message in the list is the one to which the model should respond.

        Returns:
            AssistantMessage: The response from the model.
        """
        pass
    
    @abstractmethod
    def chat_stream(self, messages: list[Message]) -> Generator[str, None]:
        """Send a list of messages to the model and stream the response.

        Args:
            messages (list[Message]): A list of messages to send to the model. The last message in the list is the one to which the model should respond.

        Yields:
            Generator[str, None]: A generator that yields the response from the model in chunks. The size of the chunks is implementation-dependent.
        """
        pass
    
    @classmethod
    def generate_model_info(cls) -> ModelInfo:
        """Generate and return information about the model.

        Returns:
            ModelInfoFull: Information about the model.
        """
        attrs = {x: getattr(cls, x) for x in dir(cls) if not (x.startswith('__') or callable(getattr(cls, x)))}
        return ModelInfo(**attrs)
