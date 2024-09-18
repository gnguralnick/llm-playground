from .chat_model import ChatModel, Message, AssistantMessage
from abc import ABC
from openai import OpenAI

class OpenAIModel(ChatModel, ABC):
    
    def __init__(self, model_name) -> None:
        super().__init__(model_name)
        self.client = OpenAI()
        
    def chat(self, messages: list[Message]) -> AssistantMessage:
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{'role': m.role, 'content': m.content} for m in messages]
        )
        
        return AssistantMessage(content=completion.choices[0].message.content)