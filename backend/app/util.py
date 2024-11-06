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
    FILE = 'file'
    TOOL_CALL = 'tool_call'
    TOOL_RESULT = 'tool_result'
    
class ModelAPI(str, Enum):
    OPENAI = 'OPENAI'
    ANTHROPIC = 'ANTHROPIC'
    
class ToolAPI(str, Enum):
    TAVILY = 'TAVILY'
    
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