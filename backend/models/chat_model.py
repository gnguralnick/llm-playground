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
    
    api_name: str
    human_name: str
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @abstractmethod
    def chat(self, messages: list[Message]) -> AssistantMessage:
        pass
    
    @abstractmethod
    def chat_stream(self, messages: list[Message]) -> Generator[str, None]:
        pass
    
class ModelInfo(BaseModel):
    human_name: str
    api_name: str
    supports_streaming: bool = False
    
class ModelInfoFull(ModelInfo):
    model: type[ChatModel]
    
def generate_model_info(model_type: type[ChatModel]) -> ModelInfoFull:
    model = model_type()
    return ModelInfoFull(
        human_name=model.human_name,
        api_name=model.api_name,
        model=model_type,
        supports_streaming=(model.chat_stream != ChatModel.chat_stream)
    )