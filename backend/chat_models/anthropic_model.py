from collections.abc import Generator
import anthropic
from chat_models.chat_model import ChatModel, Message, AssistantMessage
from abc import ABC
from util import ModelAPI, Role, ModelConfig, RangedFloat, RangedInt

class AnthropicConfig(ModelConfig):
    max_tokens: RangedInt = RangedInt(min=1, max=None, val=1024)
    temperature: RangedFloat = RangedFloat(min=0, max=1, val=1)
    top_k: int | None = None
    top_p: float | None = None
    
    def dump_values(self) -> dict:
        return {
            'max_tokens': self.max_tokens.val,
            'temperature': self.temperature.val,
            'top_k': self.top_k if self.top_k is not None else anthropic.NOT_GIVEN,
            'top_p': self.top_p if self.top_p is not None else anthropic.NOT_GIVEN
        }
    

class AnthropicModel(ChatModel, ABC):
    
    api_provider: ModelAPI = ModelAPI.ANTHROPIC
    requires_key: bool = True
    supports_streaming: bool = True
    config: AnthropicConfig = AnthropicConfig()
    config_type = AnthropicConfig
    
    def __init__(self, api_key: str, config: AnthropicConfig | None) -> None:
        super().__init__(api_key, config)
        if api_key is None:
            raise ValueError('API key is required')
        self._client = anthropic.Anthropic(api_key=api_key)
        
    def chat(self, messages: list[Message]) -> AssistantMessage:
        system_msg = [m for m in messages if m.role == Role.SYSTEM][0]
        response = self._client.messages.create(
            model=self.api_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages if m.role != Role.SYSTEM], # type: ignore
            system=system_msg.content,
            **self.config.dump_values()
        )
        
        if response.type == 'error':
            print(response.error)
            raise ValueError(response.error.type + ': ' + response.error.message)
        
        return AssistantMessage(content=response.content[0].text, model=self.api_name)
    
    def chat_stream(self, messages: list[Message]) -> Generator[str, None, None]:
        system_msg = [m for m in messages if m.role == Role.SYSTEM][0]
        with self._client.messages.stream(
            model=self.api_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages if m.role != Role.SYSTEM], # type: ignore
            system=system_msg.content,
            **self.config.dump_values()
        ) as stream:
            for text in stream.text_stream:
                yield text
    
class Claude3Point5Sonnet(AnthropicModel):
    
    api_name: str = 'claude-3-5-sonnet-20240620'
    human_name: str = 'Claude 3.5 Sonnet'
    
    def __init__(self, api_key, config) -> None:
        super().__init__(api_key, config)
        
class Claude3Opus(AnthropicModel):
    
    api_name: str = 'claude-3-opus-20240229'
    human_name: str = 'Claude 3 Opus'
    
    def __init__(self, api_key, config) -> None:
        super().__init__(api_key, config)
        
class Claude3Sonnet(AnthropicModel):
    
    api_name: str = 'claude-3-sonnet-20240229'
    human_name: str = 'Claude 3 Sonnet'
    
    def __init__(self, api_key, config) -> None:
        super().__init__(api_key, config)
        
class Claude3Haiku(AnthropicModel):
    
    api_name: str = 'claude-3-haiku-20240307'
    human_name: str = 'Claude 3 Haiku'
    
    def __init__(self, api_key, config) -> None:
        super().__init__(api_key, config)
        
model_types = [Claude3Point5Sonnet, Claude3Opus, Claude3Sonnet, Claude3Haiku]