from enum import Enum
from pydantic import BaseModel, field_validator, ValidationInfo

class Role(str, Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'
    
class MessageContentType(str, Enum):
    TEXT = 'text'
    IMAGE = 'image'
    
class ModelAPI(str, Enum):
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    
class ConfigItem(BaseModel):
    type: str
    
class RangedFloat(ConfigItem):
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
    type: str = 'string'
    options: list[str]
    val: str
    
    @field_validator('val')
    @classmethod
    def validate_val(cls, value, info: ValidationInfo):
        if value not in info.data['options']:
            raise ValueError(f'Value must be one of {cls.options}')
        return value
    
class ModelConfig(BaseModel):
    pass