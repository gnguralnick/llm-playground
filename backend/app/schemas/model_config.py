from pydantic import BaseModel
from .tools import ToolConfig


class ModelConfig(BaseModel):
    pass

class ModelConfigWithTools(ModelConfig):
    tools: list[ToolConfig] = []