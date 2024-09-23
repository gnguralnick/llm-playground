from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel
from collections.abc import Generator

class Role(str, Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'
    
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

class ChatModel(ABC):
    """An abstract class for chat models. It defines the basic methods that all chat models should implement.

    Args:
        api_name (str): The name of the model as it appears in its API (for models accessed via an API) - e.g. 'gpt-4o-mini'.
        human_name (str): The human-readable name of the model - e.g. 'GPT-4o Mini' - for display in the UI.
    """
    
    api_name: str
    human_name: str
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

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
    
class ModelInfo(BaseModel):
    human_name: str
    api_name: str
    supports_streaming: bool = False
    
class ModelInfoFull(ModelInfo):
    model: type[ChatModel]
    
def generate_model_info(model_type: type[ChatModel]) -> ModelInfoFull:
    """Generate a model information object from a model type.
    The point of this is to generate a Pydantic model object that can be used to serialize the model information to JSON.
    Specialized functionality that the model supports, such as streaming, will be automatically verified and included in the model information object.

    Args:
        model_type (type[ChatModel]): The type of the model for which to generate the model information object.

    Returns:
        ModelInfoFull: The model information object.
    """
    model = model_type()
    return ModelInfoFull(
        human_name=model.human_name,
        api_name=model.api_name,
        model=model_type,
        supports_streaming=(model.chat_stream != ChatModel.chat_stream)
    )