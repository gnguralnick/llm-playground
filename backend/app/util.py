from enum import Enum
import inspect
from pydantic import BaseModel, field_validator, ValidationInfo, Field, model_validator
from typing import Callable, Any
import re

class Role(str, Enum):
    """Role of the message sender
    Can be 'user', 'assistant', or 'system'
    """
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'
    TOOL = 'tool'
    
class MessageContentType(str, Enum):
    TEXT = 'text'
    IMAGE = 'image'
    TOOL_CALL = 'tool_call'
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
    func: Callable = Field(exclude=True)
    
    @model_validator(mode='before')
    @classmethod
    def populate_func(cls, data: Any) -> Any:
        from app.tools import get_tools
        if 'func' not in data:
            tool = get_tools().get(data['name'])
            if tool is None:
                raise ValueError(f'No tool found with name {data["name"]}')
            data['func'] = tool.func
        return data
    
    @classmethod
    def from_func(cls, func):
        sig = inspect.signature(func)
        params = {}
        required = []
        doc: str = func.__doc__
        description = doc.split('Args:')[0].strip()
        for name, param in sig.parameters.items():
            enum: list[str] | None = None
            param_type = param.annotation
            if param_type == str:
                param_type = 'string'
            elif param_type == int:
                param_type = 'integer'
            elif param_type == float:
                param_type = 'number'
            elif param_type == bool:
                param_type = 'boolean'
            elif issubclass(param_type, Enum):
                param_type = 'string'
                enum = [x.name for x in param.annotation]
                
            # each parameter should have a line in the docstring of the form
            # <param_name> (<param_type>): <param_description>
            arg_doc = re.search(f'{name} \\(([^)]+)\\): (.+)', doc)
            if arg_doc is None:
                raise ValueError(f'No documentation found for parameter {name}')
            param_description = arg_doc.group(2)
            param_info = {
                'type': param_type,
                'description': param_description,
            }
            if enum is not None:
                param_info['enum'] = enum
            if param.default == inspect.Parameter.empty:
                required.append(name)
            params[name] = ToolParameter(**param_info)
        return cls(name=func.__name__, description=description, parameters=params, required=required, func=func)
    
class ModelConfig(BaseModel):
    pass

class ModelConfigWithTools(ModelConfig):
    tools: list[ToolConfig] = []