from fastapi import APIRouter, Depends
from app import dependencies
from app.tools import get_tools
from app.util import ToolConfig

router = APIRouter(
    prefix="/tools",
    tags=["tools"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(dependencies.get_current_user)]
)

@router.get('/', response_model=list[ToolConfig], response_model_exclude_unset=True)
def read_tools():
    return list(get_tools().values())

@router.get('/{tool_name}', response_model=ToolConfig, response_model_exclude_unset=True)
def read_tool(tool_name: str):
    return get_tools()[tool_name]

@router.post('/{tool_name}', response_model=dict)
def run_tool(tool_name: str, tool_input: dict):
    tool = get_tools()[tool_name]
    return tool.func(tool_input)