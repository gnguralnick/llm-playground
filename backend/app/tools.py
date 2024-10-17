from app.util import ToolConfig

def test_tool(foo: str):
    """
    A test function that takes a string argument.
    """
    return foo

test_tool_config = ToolConfig.from_func(test_tool)

tools = {
    'test_tool': test_tool_config
}