from fastapi import APIRouter, Depends, HTTPException
from app import dependencies
from app.schemas.tools import ToolConfig

router = APIRouter(
    prefix="/tools",
    tags=["tools"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(dependencies.get_current_user)]
)

@router.get('/', response_model=list[ToolConfig], response_model_exclude_unset=True)
def read_tools(tools: dict[str, ToolConfig] = Depends(dependencies.get_tools)):
    return list(tools.values())

@router.get('/{tool_name}', response_model=ToolConfig, response_model_exclude_unset=True)
def read_tool(tool_name: str, tools: dict[str, ToolConfig] = Depends(dependencies.get_tools)):
    if tool_name not in tools:
        raise HTTPException(status_code=404, detail='Tool not found')
    return tools[tool_name]

@router.post('/{tool_name}', response_model=dict)
def run_tool(tool_name: str, tool_input: dict, tools: dict[str, ToolConfig] = Depends(dependencies.get_tools)):
    if tool_name not in tools:
        raise HTTPException(status_code=404, detail='Tool not found')
    tool = tools[tool_name]
    return tool.func(tool_input)