"""
Web Search Agent - specialized in finding current online information.
"""

from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.web_search import search_web, search_web_news
from config.settings import settings


def create_web_search_agent():
    """
    Create an agent specialized in web search.
    
    This agent has access to web search tools and is optimized
    for finding current, online information, news, and public data.
    
    Returns:
        A compiled LangGraph ReAct agent
    """
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0  # More deterministic for factual search
    )
    
    # Create agent with tools
    agent = create_react_agent(
        llm,
        tools=[search_web, search_web_news],
        prompt=(
            "You are a WEB RESEARCH SPECIALIST.\n\n"
            "YOUR ROLE:\n"
            "- Search the web for current, relevant information\n"
            "- Find recent news, online data, and public information\n"
            "- Provide accurate summaries of web findings\n"
            "- Include source URLs for verification\n\n"
            "TOOLS AVAILABLE:\n"
            "- search_web: For general web searches\n"
            "- search_web_news: For recent news and current events\n\n"
            "INSTRUCTIONS:\n"
            "- Choose the appropriate search tool based on the query\n"
            "- For news or current events, use search_web_news\n"
            "- For other information, use search_web\n"
            "- Synthesize information from multiple sources when available\n"
            "- Always include URLs for reference\n"
            "- Prioritize recent and authoritative sources\n\n"
            "DO NOT:\n"
            "- Make up information not found in search results\n"
            "- Provide outdated information when recent data is available\n"
            "- Cite sources that weren't in your search results"
        ),
        name="web_search_agent"
    )
    
    return agent
