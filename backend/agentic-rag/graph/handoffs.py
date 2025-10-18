"""
Handoff tools for agent delegation.
"""

from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langgraph.graph import MessagesState


def create_handoff_tool(agent_name: str, description: str):
    """
    Create a handoff tool for delegating tasks to a specific agent.
    
    Args:
        agent_name: The name of the agent to delegate to
        description: Description of when to use this agent
        
    Returns:
        A LangChain tool for handoff
    """
    tool_name = f"transfer_to_{agent_name}"
    
    @tool(tool_name, description=description)
    def handoff_tool(
        task_description: Annotated[
            str,
            "Clear, specific description of what the agent should do, including all relevant context"
        ],
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """
        Transfer control to a specialized agent.
        
        Args:
            task_description: What the agent should do
            state: Current graph state
            tool_call_id: Tool call identifier
            
        Returns:
            Command to transition to the specified agent
        """
        # Create tool message indicating successful transfer
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}. Task: {task_description}",
            "name": tool_name,
            "tool_call_id": tool_call_id
        }
        
        return Command(
            goto=agent_name,  # Transition to the specified agent
            update={**state, "messages": state["messages"] + [tool_message]},
            graph=Command.PARENT  # Return to parent graph after execution
        )
    
    return handoff_tool


# Create handoff tools for each specialized agent
transfer_to_local_knowledge = create_handoff_tool(
    agent_name="local_knowledge_agent",
    description=(
        "Delegate to the local knowledge agent for searching internal documents, "
        "company policies, procedures, or any information in the local knowledge base."
    )
)

transfer_to_web_search = create_handoff_tool(
    agent_name="web_search_agent",
    description=(
        "Delegate to the web search agent for finding current online information, "
        "recent news, public data, or any information that requires web search."
    )
)

transfer_to_cloud = create_handoff_tool(
    agent_name="cloud_agent",
    description=(
        "Delegate to the cloud agent for querying cloud resources, "
        "accessing cloud storage, databases, or cloud infrastructure information."
    )
)


def get_all_handoff_tools():
    """
    Get all handoff tools for the supervisor.
    
    Returns:
        List of handoff tools
    """
    return [
        transfer_to_local_knowledge,
        transfer_to_web_search,
        transfer_to_cloud
    ]
