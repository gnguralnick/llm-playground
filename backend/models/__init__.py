from . import openai_model as openai
from .chat_model import ChatModel, ModelInfo, ModelInfo

model_types: list[type[ChatModel]] = openai.model_types

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