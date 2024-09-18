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

class ChatModel(ABC, BaseModel):
    
    api_name: str
    human_name: str
    
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def chat(self, messages: list[Message]) -> AssistantMessage:
        pass
    
class ModelInfo(BaseModel):
    human_name: str
    api_name: str
    
class ModelInfoFull(BaseModel):
    model: ChatModel