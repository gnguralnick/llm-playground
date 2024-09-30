import anthropic
from .chat_model import ChatModel, Message, AssistantMessage
from abc import ABC
from util import ModelAPI, Role

class AnthropicModel(ChatModel, ABC):
    
    api_provider: ModelAPI = ModelAPI.ANTHROPIC
    requires_key: bool = True
    supports_streaming: bool = False
    
    def __init__(self, api_key: str) -> None:
        super().__init__(api_key)
        if api_key is None:
            raise ValueError('API key is required')
        self._client = anthropic.Anthropic(api_key=api_key)
        
    def chat(self, messages: list[Message]) -> AssistantMessage:
        system_msg = [m for m in messages if m.role == Role.SYSTEM][0]
        response = self._client.messages.create(
            model=self.api_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages if m.role != Role.SYSTEM], # type: ignore
            system=system_msg.content,
            max_tokens=1000
        )
        
        if response.type == 'error':
            print(response.error)
            raise ValueError(response.error.type + ': ' + response.error.message)
        
        return AssistantMessage(content=response.content[0].text, model=self.api_name)
    
class Claude3Point5Sonnet(AnthropicModel):
    
    api_name: str = 'claude-3-5-sonnet-20240620'
    human_name: str = 'Claude 3.5 Sonnet'
    
    def __init__(self, api_key) -> None:
        super().__init__(api_key)
        
class Claude3Opus(AnthropicModel):
    
    api_name: str = 'claude-3-opus-20240229'
    human_name: str = 'Claude 3 Opus'
    
    def __init__(self, api_key) -> None:
        super().__init__(api_key)
        
class Claude3Sonnet(AnthropicModel):
    
    api_name: str = 'claude-3-sonnet-20240229'
    human_name: str = 'Claude 3 Sonnet'
    
    def __init__(self, api_key) -> None:
        super().__init__(api_key)
        
class Claude3Haiku(AnthropicModel):
    
    api_name: str = 'claude-3-haiku-20240307'
    human_name: str = 'Claude 3 Haiku'
    
    def __init__(self, api_key) -> None:
        super().__init__(api_key)
        
model_types = [Claude3Point5Sonnet, Claude3Opus, Claude3Sonnet, Claude3Haiku]