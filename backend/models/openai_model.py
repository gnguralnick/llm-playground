from .chat_model import ChatModel, Message, AssistantMessage, ModelInfoFull
from abc import ABC
from openai import OpenAI

class OpenAIModel(ChatModel, ABC):
    
    def __init__(self) -> None:
        super().__init__()
        self.client = OpenAI()
        raise NotImplementedError('OpenAIModel is an abstract class')
        
    def chat(self, messages: list[Message]) -> AssistantMessage:
        completion = self.client.chat.completions.create(
            model=self.api_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages]
        )
        
        return AssistantMessage(content=completion.choices[0].message.content)
    
class GPT4OMini(OpenAIModel):
    
    api_name: str = 'gpt-4o-mini'
    human_name: str = 'GPT-4o Mini'
        
class GPT4O(OpenAIModel):
    
    api_name: str = 'gpt-4o'
    human_name: str = 'GPT-4o'
        
models: dict[str, ModelInfoFull] = {
    'gpt-4o-mini': {
        'model': GPT4OMini,
        'human_name': 'GPT-4o Mini',
        'api_name': 'gpt-4o-mini',
    },
    'gpt-4o': {
        'model': GPT4O,
        'human_name': 'GPT-4o',
        'api_name': 'gpt-4o',
    },
}