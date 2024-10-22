from typing import Callable, Any
from pydantic import BaseModel, Field, model_validator
from app.util import ToolAPI
import inspect
from enum import Enum
import re

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
    api_key: str | None = Field(exclude=True, default=None)
    api_provider: ToolAPI | None = None
    requires_api_key: bool = False
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self.requires_api_key and self.api_key is None:
            raise ValueError('This tool requires an API key')
        if self.requires_api_key:
            kwds['api_key'] = self.api_key
        return self.func.__call__(*args, **kwds)
    
    def set_api_key(self, api_key: str):
        self.api_key = api_key
    
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
    def from_name(cls, name):
        from app.tools import get_tools
        tool = get_tools().get(name)
        if tool is None:
            raise ValueError(f'No tool found with name {name}')
        return cls(name=name, description=tool.description, parameters=tool.parameters, required=tool.required, func=tool.func)
    
    @classmethod
    def from_func(cls, func):
        sig = inspect.signature(func)
        params = {}
        required = []
        doc: str = func.__doc__
        description = doc.split('Args:')[0].strip()
        for name, param in sig.parameters.items():
            if name == 'api_key' or name == 'api_provider':
                continue
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
        kwargs = {
            'name': func.__name__,
            'description': description,
            'parameters': params,
            'required': required,
            'func': func
        }
        if 'api_key' in sig.parameters:
            kwargs['requires_api_key'] = True
            if 'api_provider' not in sig.parameters:
                raise ValueError('API key requires an API provider')
            kwargs['api_provider'] = sig.parameters['api_provider'].default
        return cls(**kwargs)