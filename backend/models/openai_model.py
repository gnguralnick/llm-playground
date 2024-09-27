from collections.abc import Generator
from .chat_model import ChatModel, Message, AssistantMessage
from abc import ABC
from openai import OpenAI
from util import ModelAPI

class OpenAIModel(ChatModel, ABC):

    api_name: str
    human_name: str
    api_provider: ModelAPI = ModelAPI.OPENAI
    requires_key: bool = True
    supports_streaming: bool = True
    
    def __init__(self, api_key: str) -> None:
        super().__init__(api_key)
        if api_key is None:
            raise ValueError('API key is required')
        self._client = OpenAI(api_key=api_key)
        
    def chat(self, messages: list[Message]) -> AssistantMessage:
        completion = self._client.chat.completions.create(
            model=self.api_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages] # type: ignore
        )
        
        if completion.choices[0].message.content is None:
            raise ValueError('No completion content')
        
        return AssistantMessage(content=completion.choices[0].message.content, model=self.api_name)
    
    def chat_stream(self, messages: list[Message]) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self.api_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages], # type: ignore
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
            
class GPT4OMini(OpenAIModel):
    
    api_name: str = 'gpt-4o-mini'
    human_name: str = 'GPT-4o Mini'
    
    def __init__(self, api_key) -> None:
        super().__init__(api_key)
        
class GPT4O(OpenAIModel):
    
    api_name: str = 'gpt-4o'
    human_name: str = 'GPT-4o'
    
    def __init__(self, api_key) -> None:
        super().__init__(api_key)
        
model_types = [GPT4OMini, GPT4O]