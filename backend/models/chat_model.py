from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel

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
    
class SystemMessage(Message):
    role: Role = Role.SYSTEM

class ChatModel(ABC):
    
    def __init__(self, model_name) -> None:
        super().__init__()
        self.model_name = model_name

    @abstractmethod
    def chat(self, messages: list[Message]) -> AssistantMessage:
        pass
    
def get_chat_model(model_name: str) -> ChatModel:
    from .openai_model import OpenAIModel
    
    if model_name.find('gpt') != -1:
        return OpenAIModel(model_name)
    else:
        raise ValueError('Model not found')