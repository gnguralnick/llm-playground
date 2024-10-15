from enum import Enum
import inspect
from pydantic import BaseModel, field_validator, ValidationInfo

class Role(str, Enum):
    """Role of the message sender
    Can be 'user', 'assistant', or 'system'
    """
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'
    
class MessageContentType(str, Enum):
    TEXT = 'text'
    IMAGE = 'image'
    TOOL_USE = 'tool_use'
    TOOL_RESULT = 'tool_result'
    
class ModelAPI(str, Enum):
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    
class ConfigItem(BaseModel):
    type: str
    
class RangedFloat(ConfigItem):
    """
    A float value with optional min and max constraints
    """
    type: str = 'float'
    min: float | None
    max: float | None
    val: float
    
    @field_validator('val')
    @classmethod
    def validate_val(cls, value, info: ValidationInfo):
        if (info.data['min'] and value < info.data['min']) or (info.data['max'] and value > info.data['max']):
            raise ValueError(f'Value must be between {cls.min} and {cls.max}')
        return value
    
class RangedInt(ConfigItem):
    """
    An integer value with optional min and max constraints
    """
    type: str = 'int'
    min: int | None
    max: int | None
    val: int
    
    @field_validator('val')
    @classmethod
    def validate_val(cls, value, info: ValidationInfo):
        if (info.data['min'] and value < info.data['min']) or (info.data['max'] and value > info.data['max']):
            raise ValueError(f'Value must be between {cls.min} and {cls.max}')
        return value
    
class OptionedString(ConfigItem):
    """
    A string value that must be one of a set of options
    """
    type: str = 'string'
    options: list[str]
    val: str
    
    @field_validator('val')
    @classmethod
    def validate_val(cls, value, info: ValidationInfo):
        if value not in info.data['options']:
            raise ValueError(f'Value must be one of {cls.options}')
        return value
    
class ToolParameter(BaseModel):
    type: str
    description: str
    enum: list[str] | None = None
    
class ToolConfig(BaseModel):
    name: str
    description: str
    parameters: dict[str, ToolParameter]
    required: list[str]
    
    @classmethod
    def from_func(cls, func):
        sig = inspect.signature(func)
        params = {}
        required = []
        for name, param in sig.parameters.items():
            param_type = str(param.annotation)
            enum = None
            if param_type == 'str':
                param_type = 'string'
            elif param_type == 'int':
                param_type = 'integer'
            elif param_type == 'float':
                param_type = 'number'
            elif param_type == 'bool':
                param_type = 'boolean'
            elif param_type.startswith('<enum'):
                param_type = 'string'
                enum = [x.name for x in param.annotation]
            param_info = {
                'type': param_type,
                'description': param.annotation,
                'enum': enum
            }
            if param.default == inspect.Parameter.empty:
                required.append(name)
            params[name] = ToolParameter(**param_info)
        return cls(name=func.__name__, description=func.__doc__, parameters=params, required=required)
    
class ModelConfig(BaseModel):
    pass

class ModelConfigWithTools(ModelConfig):
    tools: list[ToolConfig] = []