from . import chat_model, openai_model as openai
from .chat_model import ChatModel, ModelInfo

models = openai.models

def get_chat_model(model_name: str) -> chat_model.ChatModel:
    if model_name not in models:
        raise ValueError(f'Unknown model name: {model_name}')
    return models[model_name](model_name=model_name)

def get_models() -> list[ModelInfo]:
    return models.values()