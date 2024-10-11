from pydantic import BaseModel
from app.util import ModelAPI, ModelConfig
from app.chat_models import ChatModel
import app.chat_models.openai_model as openai
import app.chat_models.anthropic_model as anthropic

model_config_type = openai.OpenAIConfig | anthropic.AnthropicConfig | ModelConfig
model_types: list[type[ChatModel]] = openai.model_types + anthropic.model_types

class ModelInfo(BaseModel):
    human_name: str
    api_name: str
    api_provider: ModelAPI
    requires_key: bool = False
    user_has_key: bool = False
    supports_streaming: bool = False
    supports_images: bool = False
    config: model_config_type



def get_models() -> list[ModelInfo]:
    return [model.generate_model_info() for model in model_types]

def get_chat_model_info(model_name: str) -> ModelInfo:
    for model_type in model_types:
        if model_type.api_name == model_name:
            return model_type.generate_model_info()
    raise ValueError('Model not found')

def get_chat_model(model_name: str) -> type[ChatModel]:
    for model_type in model_types:
        if model_type.api_name == model_name:
            return model_type
    raise ValueError('Model not found')