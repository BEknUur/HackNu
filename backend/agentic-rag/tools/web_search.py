"""
Web search tool using Tavily API.
"""

from langchain_core.tools import tool
from tavily import TavilyClient
from config.settings import settings


# Initialize Tavily client
tavily_client = TavilyClient(api_key=settings.tavily_api_key)


@tool
def search_web(query: str, max_results: int = 3) -> str:
    """
    Search the web for current information using Tavily.
    
    Use this tool to find recent news, current events, online information,
    or any data that requires up-to-date web search.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return (default: 3)
        
    Returns:
        Formatted string with web search results including titles, content, and URLs
    """
    try:
        # Perform Tavily search
        response = tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )
        
        results = response.get('results', [])
        
        if not results:
            return "No web results found for the query."
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'N/A')
            content = result.get('content', 'N/A')
            url = result.get('url', 'N/A')
            score = result.get('score', 0)
            
            formatted_results.append(
                f"--- Web Result {i} (Relevance: {score:.2f}) ---\n"
                f"Title: {title}\n"
                f"Content: {content}\n"
                f"URL: {url}\n"
            )
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error performing web search: {str(e)}"


@tool
def search_web_news(query: str, max_results: int = 3) -> str:
    """
    Search for recent news articles on the web.
    
    Use this tool specifically for finding recent news and current events.
    
    Args:
        query: The news search query
        max_results: Maximum number of news articles to return (default: 3)
        
    Returns:
        Formatted string with news search results
    """
    try:
        # Perform Tavily search with news focus
        response = tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            topic="news"  # Focus on news
        )
        
        results = response.get('results', [])
        
        if not results:
            return "No recent news found for the query."
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'N/A')
            content = result.get('content', 'N/A')
            url = result.get('url', 'N/A')
            
            formatted_results.append(
                f"--- News Article {i} ---\n"
                f"Title: {title}\n"
                f"Summary: {content}\n"
                f"URL: {url}\n"
            )
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching news: {str(e)}"
