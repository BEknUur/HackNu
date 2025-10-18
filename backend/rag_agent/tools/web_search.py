"""
Web search tool using Tavily API for the RAG system.
"""

import os
import logging
from typing import Optional
from langchain_core.tools import tool
from tavily import TavilyClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSearchTool:
    """Web search tool for the RAG system."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the web search tool.
        
        Args:
            api_key: Tavily API key (defaults to TAVILY_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.client = None
        self.mock_mode = False
        self._initialize()
    
    def _initialize(self):
        """Initialize the Tavily client."""
        try:
            if not self.api_key or self.api_key == "mock-tavily-api-key":
                logger.warning("TAVILY_API_KEY not found or is mock. Using mock mode.")
                self.mock_mode = True
                return
            
            self.client = TavilyClient(api_key=self.api_key)
            logger.info("Web search tool initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing web search tool: {e}")
            self.mock_mode = True
    
    def search(self, query: str, max_results: int = 3, search_depth: str = "advanced") -> str:
        """
        Search the web for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: Search depth ("basic" or "advanced")
            
        Returns:
            str: Formatted search results
        """
        if self.mock_mode:
            return f"Mock web search results for query: '{query}'\n\n1. Example.com - {query} Information\n   - URL: https://example.com/{query.replace(' ', '-')}\n   - Content: This is a mock web search result for '{query}'.\n   - Relevance: High\n\n2. Wikipedia - {query}\n   - URL: https://en.wikipedia.org/wiki/{query.replace(' ', '_')}\n   - Content: Mock Wikipedia article about {query}.\n   - Relevance: Medium"
        
        if not self.client:
            return "Web search not available. Please check TAVILY_API_KEY configuration."
        
        try:
            # Perform Tavily search
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth
            )
            
            results = response.get('results', [])
            
            if not results:
                return f"No web results found for query: '{query}'"
            
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
            logger.error(f"Error performing web search: {e}")
            return f"Error performing web search: {str(e)}"
    
    def search_news(self, query: str, max_results: int = 3) -> str:
        """
        Search for recent news articles.
        
        Args:
            query: News search query
            max_results: Maximum number of results
            
        Returns:
            str: Formatted news results
        """
        if not self.client:
            return "Web search not available. Please check TAVILY_API_KEY configuration."
        
        try:
            # Perform Tavily search with news focus
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
                topic="news"
            )
            
            results = response.get('results', [])
            
            if not results:
                return f"No recent news found for query: '{query}'"
            
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
            logger.error(f"Error searching news: {e}")
            return f"Error searching news: {str(e)}"


# Global web search tool instance
_web_search_tool_instance = None


def get_web_search_tool() -> WebSearchTool:
    """Get the global web search tool instance."""
    global _web_search_tool_instance
    if _web_search_tool_instance is None:
        _web_search_tool_instance = WebSearchTool()
    return _web_search_tool_instance


@tool
def web_search_tool(query: str, max_results: int = 3) -> str:
    """
    Search the web for current information using Tavily API.
    
    Use this tool to find recent news, current events, online information,
    or any data that requires up-to-date web search.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return (default: 3)
        
    Returns:
        Formatted string with web search results including titles, content, and URLs
    """
    tool_instance = get_web_search_tool()
    return tool_instance.search(query, max_results)


@tool
def web_search_news_tool(query: str, max_results: int = 3) -> str:
    """
    Search for recent news articles on the web.
    
    Use this tool specifically for finding recent news and current events.
    
    Args:
        query: The news search query
        max_results: Maximum number of news articles to return (default: 3)
        
    Returns:
        Formatted string with news search results
    """
    tool_instance = get_web_search_tool()
    return tool_instance.search_news(query, max_results)


@tool
def get_web_search_status() -> str:
    """
    Get the current status of the web search tool.
    
    Returns:
        str: Status information about the web search tool
    """
    tool_instance = get_web_search_tool()
    
    if not tool_instance.client:
        return "Web search tool is not available. Please check TAVILY_API_KEY configuration."
    
    return "Web search tool is ready and configured."


if __name__ == "__main__":
    # Example usage and testing
    print("Testing web search tool...")
    
    # Check status
    status = get_web_search_status()
    print(f"Web search status: {status}")
    
    # Test search if available
    if "ready" in status.lower():
        test_query = "current technology trends"
        print(f"\nSearching for: '{test_query}'")
        results = web_search_tool.invoke({"query": test_query, "max_results": 2})
        print(f"Results:\n{results}")
    else:
        print("Web search not available. Please set TAVILY_API_KEY environment variable.")
