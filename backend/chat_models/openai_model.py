from collections.abc import Generator
from chat_models.chat_model import ChatModel, Message, AssistantMessage
from abc import ABC
from openai import OpenAI
from util import ModelAPI, ModelConfig, RangedFloat, RangedInt

class OpenAIConfig(ModelConfig):
    frequency_penalty: RangedFloat = RangedFloat(min=-2, max=2, val=0)
    max_completion_tokens: RangedInt = RangedInt(min=1, max=None, val=1024)
    # n: RangedInt = RangedInt(min=1, max=None, val=1)
    presence_penalty: RangedFloat = RangedFloat(min=-2, max=2, val=0)
    temperature: RangedFloat = RangedFloat(min=0, max=2, val=1)
    top_p: RangedFloat = RangedFloat(min=0, max=1, val=1)
    
    def dump_values(self) -> dict:
        return {
            'frequency_penalty': self.frequency_penalty.val,
            'max_completion_tokens': self.max_completion_tokens.val,
            # 'n': self.n.val,
            'presence_penalty': self.presence_penalty.val,
            'temperature': self.temperature.val,
            'top_p': self.top_p.val
        }
    
class OpenAIModel(ChatModel, ABC):

    api_name: str
    human_name: str
    api_provider: ModelAPI = ModelAPI.OPENAI
    requires_key: bool = True
    supports_streaming: bool = True
    config: OpenAIConfig = OpenAIConfig()
    
    def __init__(self, api_key: str, config: OpenAIConfig | None) -> None:
        super().__init__(api_key, config)
        if api_key is None:
            raise ValueError('API key is required')
        self._client = OpenAI(api_key=api_key)
        
    def chat(self, messages: list[Message]) -> AssistantMessage:
        completion = self._client.chat.completions.create(
            model=self.api_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages], # type: ignore
            **self.config.dump_values()
        )
        
        if completion.choices[0].message.content is None:
            raise ValueError('No completion content')
        
        return AssistantMessage(content=completion.choices[0].message.content, model=self.api_name)
    
    def chat_stream(self, messages: list[Message]) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self.api_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages], # type: ignore
            stream=True,
            **self.config.dump_values()
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
            
class GPT4OMini(OpenAIModel):
    
    api_name: str = 'gpt-4o-mini'
    human_name: str = 'GPT-4o Mini'
    
    def __init__(self, api_key, config) -> None:
        super().__init__(api_key, config)
        
class GPT4O(OpenAIModel):
    
    api_name: str = 'gpt-4o'
    human_name: str = 'GPT-4o'
    
    def __init__(self, api_key, config) -> None:
        super().__init__(api_key, config)
        
model_types = [GPT4OMini, GPT4O]