from app.util import ToolAPI

def test_tool(foo: str):
    """A test tool that returns the input string.

    Args:
        foo (str): The input string

    Returns:
        str: The input string
    """
    return foo

def web_search(query: str, api_key: str, api_provider = ToolAPI.TAVILY):
    """Search the web for the given query.
    Returns a list of search results, each of the form {'title': str, 'url': str, 'content', 'score'}. Score is a float between 0 and 1 that indicates how relevant the result is to the query.

    Args:
        query (str): The search query
    
    Returns:
        list[dict]: The search results
    """
    from tavily import TavilyClient
    client = TavilyClient(api_key=api_key)

    response = client.search(query)

    return response['results']
    

def get_tools():
    from app.schemas.tools import ToolConfig
    test_tool_config = ToolConfig.from_func(test_tool)
    web_search_tool_config = ToolConfig.from_func(web_search)

    tools = {
        'test_tool': test_tool_config,
        'web_search': web_search_tool_config
    }
    
    return tools