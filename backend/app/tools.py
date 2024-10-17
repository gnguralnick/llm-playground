from app.util import ToolConfig

def test_tool(foo: str):
    """A test tool that returns the input string.

    Args:
        foo (str): The input string

    Returns:
        str: The input string
    """
    return foo

def get_tools():
    test_tool_config = ToolConfig.from_func(test_tool)

    tools = {
        'test_tool': test_tool_config
    }
    
    return tools