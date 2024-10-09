from collections.abc import Generator
from typing import Iterable, cast
from chat_models.chat_model import ImageStreamingChatModel
from openai import OpenAI
import openai.types.chat as chat_types
from util import ModelAPI, ModelConfig, RangedFloat, RangedInt, MessageContentType, OptionedString, Role

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from schemas import MessageCreate as Message

class OpenAIConfig(ModelConfig):
    frequency_penalty: RangedFloat = RangedFloat(min=-2, max=2, val=0)
    max_completion_tokens: RangedInt = RangedInt(min=1, max=None, val=1024)
    # n: RangedInt = RangedInt(min=1, max=None, val=1)
    presence_penalty: RangedFloat = RangedFloat(min=-2, max=2, val=0)
    temperature: RangedFloat = RangedFloat(min=0, max=2, val=1)
    top_p: RangedFloat = RangedFloat(min=0, max=1, val=1)
    image_detail: OptionedString = OptionedString(options=['auto', 'low', 'high'], val='auto')
    
    def dump_values(self) -> dict:
        return {
            'frequency_penalty': self.frequency_penalty.val,
            'max_completion_tokens': self.max_completion_tokens.val,
            # 'n': self.n.val,
            'presence_penalty': self.presence_penalty.val,
            'temperature': self.temperature.val,
            'top_p': self.top_p.val
        }
    
class OpenAIModel(ImageStreamingChatModel):

    api_name: str
    human_name: str
    api_provider: ModelAPI = ModelAPI.OPENAI
    requires_key: bool = True
    config: OpenAIConfig = OpenAIConfig()
    config_type = OpenAIConfig
    
    def __init__(self, api_key: str, config: OpenAIConfig | None) -> None:
        super().__init__(api_key, config)
        if api_key is None:
            raise ValueError('API key is required')
        self._client = OpenAI(api_key=api_key)
        
    def process_messages(self, messages: list['Message']) -> Iterable[chat_types.ChatCompletionMessageParam]:
        res = []
        for m in messages:
            msg = {
                'role': m.role,
                'content': []
            }
            for c in m.contents:
                content = {}
                if c.type == MessageContentType.TEXT:
                    content['type'] = 'text'
                    content['text'] = c.content
                elif c.type == MessageContentType.IMAGE:
                    content['type'] = 'image_url'
                    content['image_url'] = {
                        'url': f"data:image/{c.image_type};base64,{c.get_image()}",
                        'detail': self.config.image_detail.val
                    }
                else:
                    raise ValueError('Unsupported message type')
                msg['content'].append(content)
            res.append(msg)
        return res
        
    def chat(self, messages: list['Message']) -> 'Message':
        completion = self._client.chat.completions.create(
            model=self.api_name,
            messages=self.process_messages(messages),
            **self.config.dump_values()
        )
        
        if completion.choices[0].message.content is None:
            raise ValueError('No completion content')
        
        from schemas import MessageBuilder
        return MessageBuilder(role=Role.ASSISTANT, model=self.api_name, config=self.config).add_text(completion.choices[0].message.content).build()
    
    def chat_stream(self, messages: list['Message']) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self.api_name,
            messages=self.process_messages(messages),
            stream=True,
            **self.config.dump_values()
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
            
class GPT4OMini(OpenAIModel):
    
    api_name: str = 'gpt-4o-mini'
    human_name: str = 'GPT-4o Mini'
        
class GPT4O(OpenAIModel):
    
    api_name: str = 'gpt-4o'
    human_name: str = 'GPT-4o'
        
model_types = [GPT4OMini, GPT4O]