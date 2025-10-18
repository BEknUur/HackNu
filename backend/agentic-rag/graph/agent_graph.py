"""
Main LangGraph agent graph construction.
"""

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from agents.supervisor_agent import create_supervisor_agent
from agents.local_knowledge_agent import create_local_knowledge_agent
from agents.web_search_agent import create_web_search_agent
from agents.cloud_agent import create_cloud_agent
from graph.handoffs import get_all_handoff_tools
import os


class AgentGraphManager:
    """Manages the multi-agent graph instance."""
    
    _instance = None
    _graph = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentGraphManager, cls).__new__(cls)
        return cls._instance
    
    def initialize(self):
        """Initialize the agent graph."""
        if self._graph is not None:
            return self._graph
        
        print("Initializing multi-agent graph...")
        
        # Create all specialized agents
        local_agent = create_local_knowledge_agent()
        web_agent = create_web_search_agent()
        cloud_agent = create_cloud_agent()
        
        # Get handoff tools for supervisor
        handoff_tools = get_all_handoff_tools()
        
        # Create supervisor agent with handoff tools
        supervisor = create_supervisor_agent(handoff_tools)
        
        # Build the graph
        graph_builder = StateGraph(MessagesState)
        
        # Add all nodes
        graph_builder.add_node("supervisor", supervisor)
        graph_builder.add_node("local_knowledge_agent", local_agent)
        graph_builder.add_node("web_search_agent", web_agent)
        graph_builder.add_node("cloud_agent", cloud_agent)
        
        # Define edges
        # Start with supervisor
        graph_builder.add_edge(START, "supervisor")
        
        # All agents return to supervisor after execution
        graph_builder.add_edge("local_knowledge_agent", "supervisor")
        graph_builder.add_edge("web_search_agent", "supervisor")
        graph_builder.add_edge("cloud_agent", "supervisor")
        
        # Initialize conversation persistence checkpointer
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        checkpoint_db = os.path.join(data_dir, 'checkpoints.db')
        
        print(f"Initializing checkpointer...")
        # Use MemorySaver for conversation persistence (in-memory)
        memory = MemorySaver()
        
        # Compile the graph with checkpointer for conversation memory
        self._graph = graph_builder.compile(checkpointer=memory)
        
        print("Multi-agent graph initialized successfully with conversation persistence!")
        return self._graph
    
    def get_graph(self):
        """Get the compiled graph, initializing if needed."""
        if self._graph is None:
            self.initialize()
        return self._graph
    
    def visualize(self):
        """
        Generate a visualization of the graph.
        
        Returns:
            Mermaid diagram as PNG bytes
        """
        graph = self.get_graph()
        try:
            return graph.get_graph().draw_mermaid_png()
        except Exception as e:
            print(f"Error generating visualization: {e}")
            return None


# Global graph manager instance
graph_manager = AgentGraphManager()


def get_agent_graph():
    """
    Get the compiled multi-agent graph.
    
    Returns:
        Compiled LangGraph graph
    """
    return graph_manager.get_graph()


def create_multi_agent_graph():
    """
    Create and return the multi-agent supervisor graph.
    
    This is the main entry point for creating the graph.
    
    Returns:
        Compiled LangGraph graph with supervisor and specialized agents
    """
    return graph_manager.get_graph()
