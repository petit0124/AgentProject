import os
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

def get_tavily_search_tool():
    """Returns the Tavily Web Search tool."""
    return TavilySearchResults(
        max_results=5,
        include_answer=True,
        include_raw_content=True,
        include_images=False,
    )

@tool
def web_fetch(url: str) -> str:
    """
    Fetches the content of a specific URL. 
    Use this when you need detailed content from a specific search result.
    """
    # Tavily also has a extract/fetch API but standard search results often contain enough info.
    # However, for deep diving, we might want to use a specific fetcher or just rely on Tavily's context.
    # For this implementation, we will use a simple HTTP client or Tavily's extract if available in the SDK.
    # Since the user specifically asked for "web fetch", let's simulate a fetch or use langchain's WebBaseLoader
    
    from langchain_community.document_loaders import WebBaseLoader
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        return "\n\n".join([d.page_content for d in docs])[:10000] # Limit content length
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"
