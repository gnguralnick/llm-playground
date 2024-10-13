

from app.chat_models.anthropic.anthropic_config import AnthropicConfig
from app.chat_models.openai.openai_config import OpenAIConfig
from app.util import ModelConfig

model_config_type = OpenAIConfig | AnthropicConfig | ModelConfig