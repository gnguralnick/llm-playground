from collections.abc import Generator
from typing import Iterable, Sequence
from app.chat_models.chat_model import ImageChatModel, StreamingChatModel, ToolChatModel
from app.chat_models.openai.openai_config import OpenAIConfig
from openai import OpenAI, NOT_GIVEN, NotGiven
import openai.types.chat as chat_types
from app.util import ModelAPI, Role

import json

import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.schemas import Message

class OpenAIModel(ImageChatModel, StreamingChatModel, ToolChatModel):

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
        from app.schemas import ImageMessageContent, TextMessageContent, ToolCallMessageContent, ToolResultMessageContent
        res = []
        for m in messages:
            msg = {
                'role': m.role,
                'content': None,
                'tool_calls': None
            }
            for c in m.contents:
                content = None
                if isinstance(c, TextMessageContent):
                    content = {}
                    content['type'] = 'text'
                    content['text'] = c.content
                elif isinstance(c, ImageMessageContent) and c.is_image():
                    content = {}
                    content['type'] = 'image_url'
                    content['image_url'] = {
                        'url': f"data:image/{c.image_type};base64,{c.get_image()}",
                        'detail': self.config.image_detail.val
                    }
                elif isinstance(c, ImageMessageContent):
                    content = {}
                    content['type'] = 'text'
                    content['text'] = c.get_file_content()
                elif isinstance(c, ToolCallMessageContent):
                    if msg['tool_calls'] is None:
                        msg['tool_calls'] = []
                    
                    tool_call = {
                        'id': c.tool_call_id,
                        'type': 'function',
                        'function': {
                            'name': c.content.name,
                            'arguments': json.dumps(c.content.args)
                        }
                    }
                    
                    msg['tool_calls'].append(tool_call)
                elif isinstance(c, ToolResultMessageContent):
                    # tool results have role 'tool' and are not part of the main message
                    new_msg = {
                        'role': 'tool',
                        'tool_call_id': c.tool_call_id,
                        'content': json.dumps(c.content)
                    }
                    
                    res.append(new_msg)
                    continue
                else:
                    logging.warning(f'Unsupported message type {type(c)} for OpenAI')
                    continue
                if msg['content'] is None and content is not None:
                    msg['content'] = []
                if content is not None:
                    msg['content'].append(content)
            if msg['content'] is not None and msg['tool_calls'] is not None:
                # OpenAI API does not allow both content and tool_calls in the same message
                # so we need to split them into separate messages
                msg_copy = msg.copy()
                del msg_copy['content']
                del msg['tool_calls']
                res.append(msg)
                res.append(msg_copy)
            elif msg['content'] is not None or msg['tool_calls'] is not None:
                res.append(msg)
        return res
    
    def process_tools(self) -> Iterable[chat_types.ChatCompletionToolParam] | NotGiven:
        """
        Convert the tools in the config to the format expected by the OpenAI API.
        """
        res = []
        for tool in self.config.tools:
            tool_param = {
                'type': 'function',
                'function': {
                    'name': tool.name,
                    'description': tool.description,
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            param: schema.model_dump(exclude_none=True) for param, schema in tool.parameters.items()
                        },
                        'required': tool.required
                    },
                    'strict': False,
                },
            }
            res.append(tool_param)
        return res if len(res) > 0 else NOT_GIVEN
        
    def chat(self, messages: Sequence['Message']) -> 'Message':
        completion: chat_types.ChatCompletion = self._client.chat.completions.create(
            model=self.api_name,
            messages=self.process_messages(messages),
            tools=self.process_tools(),
            **self.config.dump_values()
        )
        from schemas import MessageBuilder
        message = MessageBuilder(role=Role.ASSISTANT, model=self.api_name, config=self.config)
        
        match completion.choices[0].finish_reason:
            case 'stop' | 'length':
                if completion.choices[0].message.content is None:
                    raise ValueError('No completion content')
        
                message.add_text(completion.choices[0].message.content)
            case 'tool_calls':
                if completion.choices[0].message.tool_calls is None:
                    raise ValueError('No tool calls')
                for tool_call in completion.choices[0].message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    message.add_tool_use(tool_call.id, name, args)
            case _:
                raise ValueError('Unexpected completion finish reason')
            
        return message.build()
        

    
    def chat_stream(self, messages: Sequence['Message']) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self.api_name,
            messages=self.process_messages(messages),
            stream=True,
            # tools=self.process_tools(),
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