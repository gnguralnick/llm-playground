from collections.abc import Generator
from typing import Iterable, Sequence
import anthropic
from chat_models.chat_model import StreamingChatModel
from util import MessageContentType, ModelAPI, Role, ModelConfig, RangedFloat, RangedInt

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from schemas import MessageBase as Message

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
    

class AnthropicModel(StreamingChatModel):
    
    api_provider: ModelAPI = ModelAPI.ANTHROPIC
    requires_key: bool = True
    config: AnthropicConfig = AnthropicConfig()
    config_type = AnthropicConfig
    
    def __init__(self, api_key: str, config: AnthropicConfig | None) -> None:
        super().__init__(api_key, config)
        if api_key is None:
            raise ValueError('API key is required')
        self._client = anthropic.Anthropic(api_key=api_key)
        
    def process_messages(self, messages: Sequence['Message']) -> Iterable[anthropic.types.MessageParam]:
        """
        Convert a list of messages to the format expected by the Anthropic API.
        """
        res = []
        for m in messages:
            if m.role != Role.SYSTEM:
                msg = {
                    'role': m.role,
                    'content': []
                }
                for c in m.contents:
                    content = {}
                    if c.type == MessageContentType.TEXT:
                        content['type'] = 'text'
                        content['text'] = c.content
                    else:
                        raise ValueError('Unsupported message type')
                    msg['content'].append(content)
                res.append(msg)
        return res
        
    def chat(self, messages: Sequence['Message']) -> 'Message':
        system_msg = [m for m in messages if m.role == Role.SYSTEM]
        system_msg = system_msg[0] if system_msg else None
        response = self._client.messages.create(
            model=self.api_name,
            messages=self.process_messages(messages),
            system=system_msg.contents[0].content if system_msg is not None else anthropic.NOT_GIVEN,
            **self.config.dump_values()
        )
        
        if response.type == 'error':
            print(response.error)
            raise ValueError(response.error.type + ': ' + response.error.message)
        
        from schemas import MessageBuilder
        return MessageBuilder(role=Role.ASSISTANT, model=self.api_name, config=self.config).add_text(response.content[0].text).build()
    
    def chat_stream(self, messages: Sequence['Message']) -> Generator[str, None, None]:
        system_msg = [m for m in messages if m.role == Role.SYSTEM]
        system_msg = system_msg[0] if system_msg else None
        with self._client.messages.stream(
            model=self.api_name,
            messages=self.process_messages(messages),
            system=system_msg.contents[0].content if system_msg is not None else anthropic.NOT_GIVEN,
            **self.config.dump_values()
        ) as stream:
            for text in stream.text_stream:
                yield text
    
class Claude3Point5Sonnet(AnthropicModel):
    
    api_name: str = 'claude-3-5-sonnet-20240620'
    human_name: str = 'Claude 3.5 Sonnet'
        
class Claude3Opus(AnthropicModel):
    
    api_name: str = 'claude-3-opus-20240229'
    human_name: str = 'Claude 3 Opus'
        
class Claude3Sonnet(AnthropicModel):
    
    api_name: str = 'claude-3-sonnet-20240229'
    human_name: str = 'Claude 3 Sonnet'
        
class Claude3Haiku(AnthropicModel):
    
    api_name: str = 'claude-3-haiku-20240307'
    human_name: str = 'Claude 3 Haiku'
        
model_types = [Claude3Point5Sonnet, Claude3Opus, Claude3Sonnet, Claude3Haiku]