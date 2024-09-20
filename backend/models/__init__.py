from . import openai_model as openai
from .chat_model import ChatModel, ModelInfo, ModelInfoFull, generate_model_info

model_types = openai.model_types
model_infos = [generate_model_info(model) for model in model_types]

def get_models() -> list[ModelInfo]:
    return model_infos

def get_chat_model_info(model_name: str) -> ModelInfoFull:
    for model_info in model_infos:
        if model_info.api_name == model_name:
            return model_info
    raise ValueError('Model not found')