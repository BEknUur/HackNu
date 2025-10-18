"""
Cloud Agent - specialized in querying cloud resources (stub implementation).
"""

from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.cloud_tools import query_cloud_storage, query_cloud_database, list_cloud_resources
from config.settings import settings


def create_cloud_agent():
    """
    Create an agent specialized in cloud resource queries.
    
    This agent has access to cloud tools for querying AWS, Azure,
    and other cloud services. This is a stub implementation.
    
    Returns:
        A compiled LangGraph ReAct agent
    """
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0
    )
    
    # Create agent with tools
    agent = create_react_agent(
        llm,
        tools=[query_cloud_storage, query_cloud_database, list_cloud_resources],
        prompt=(
            "You are a CLOUD INFRASTRUCTURE SPECIALIST.\n\n"
            "YOUR ROLE:\n"
            "- Query cloud resources (AWS, Azure, GCP)\n"
            "- Access cloud storage, databases, and compute resources\n"
            "- Provide information about cloud infrastructure\n\n"
            "TOOLS AVAILABLE:\n"
            "- query_cloud_storage: Access cloud storage (S3, Azure Blob, etc.)\n"
            "- query_cloud_database: Query cloud databases\n"
            "- list_cloud_resources: List available cloud resources\n\n"
            "INSTRUCTIONS:\n"
            "- Use appropriate tools to access cloud resources\n"
            "- Provide structured information about cloud assets\n"
            "- Handle cloud-specific queries efficiently\n\n"
            "NOTE: This is currently a stub implementation. "
            "Extend with actual cloud API integrations as needed."
        ),
        name="cloud_agent"
    )
    
    return agent
