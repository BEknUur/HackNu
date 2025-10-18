from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.vector_search import search_local_knowledge
from config.settings import settings


def create_local_knowledge_agent():
    """
    Create an agent specialized in searching the local knowledge base.
    
    This agent has access to the vector search tool and is optimized
    for finding information in internal documents, policies, and
    company-specific content.
    
    Returns:
        A compiled LangGraph ReAct agent
    """
    
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=1
    )
    
    agent = create_react_agent(
        llm,
        tools=[search_local_knowledge],
        prompt=(
            "You are a LOCAL KNOWLEDGE SPECIALIST.\n\n"
            "YOUR ROLE:\n"
            "- Search the local knowledge base for relevant information\n"
            "- Find information from internal documents, policies, procedures\n"
            "- Provide comprehensive, accurate answers based on local sources\n"
            "- Always cite the source of information when available\n\n"
            "INSTRUCTIONS:\n"
            "- Use the search_local_knowledge tool to find relevant information\n"
            "- If you find relevant information, summarize it clearly\n"
            "- If no relevant information is found, state that explicitly\n"
            "- Include source references in your response\n"
            "- Be thorough but concise\n\n"
            "DO NOT:\n"
            "- Make up information not found in the knowledge base\n"
            "- Provide information from sources outside the knowledge base\n"
            "- Speculate or guess when information is not available"
        ),
        name="local_knowledge_agent"
    )
    
    return agent
