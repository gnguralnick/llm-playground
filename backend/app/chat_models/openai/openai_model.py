from collections.abc import Generator
from typing import Iterable, Sequence
from app.chat_models.chat_model import ImageStreamingChatModel
from app.chat_models.openai.openai_config import OpenAIConfig
from openai import OpenAI
import openai.types.chat as chat_types
from app.util import ModelAPI, Role

import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.schemas import Message

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
        
    def process_messages(self, messages: Sequence['Message']) -> Iterable[chat_types.ChatCompletionMessageParam]:
        """
        Convert a sequence of messages to the format expected by the OpenAI API.
        """
        from app.schemas import ImageMessageContent, TextMessageContent
        res = []
        for m in messages:
            msg = {
                'role': m.role,
                'content': []
            }
            for c in m.contents:
                content = {}
                if isinstance(c, TextMessageContent):
                    content['type'] = 'text'
                    content['text'] = c.content
                elif isinstance(c, ImageMessageContent):
                    content['type'] = 'image_url'
                    content['image_url'] = {
                        'url': f"data:image/{c.image_type};base64,{c.get_image()}",
                        'detail': self.config.image_detail.val
                    }
                else:
                    logging.warning(f'Unsupported message type {type(c)} for OpenAI')
                    continue
                msg['content'].append(content)
            res.append(msg)
        return res
        
    def chat(self, messages: Sequence['Message']) -> 'Message':
        completion = self._client.chat.completions.create(
            model=self.api_name,
            messages=self.process_messages(messages),
            **self.config.dump_values()
        )
        
        if completion.choices[0].message.content is None:
            raise ValueError('No completion content')
        
        from schemas import MessageBuilder
        return MessageBuilder(role=Role.ASSISTANT, model=self.api_name, config=self.config).add_text(completion.choices[0].message.content).build()
    
    def chat_stream(self, messages: Sequence['Message']) -> Generator[str, None, None]:
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