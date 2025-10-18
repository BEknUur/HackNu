"""
Orchestrator Configuration Module

This module provides the main orchestrator that coordinates between
LangChain and LangGraph configurations for the RAG system.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from .langchain import langchain_config
from .langraph import langraph_config


class OrchestratorConfig(BaseModel):
    """Main orchestrator configuration that coordinates all components."""
    
    # Component configurations
    langchain_config: Any = Field(default_factory=lambda: langchain_config)
    langraph_config: Any = Field(default_factory=lambda: langraph_config)
    
    # Orchestration settings
    default_llm_provider: str = "google"
    enable_parallel_agents: bool = True
    max_agent_iterations: int = 5
    
    # Response settings
    include_sources: bool = True
    include_confidence_scores: bool = True
    max_response_length: int = 2000
    
    def get_llm(self, provider: Optional[str] = None):
        """Get configured LLM instance."""
        provider = provider or self.default_llm_provider
        return self.langchain_config.get_llm(provider)
    
    def get_supervisor_agent(self, llm_provider: Optional[str] = None):
        """Get the supervisor agent."""
        llm = self.get_llm(llm_provider)
        return self.langraph_config.create_supervisor_agent(llm)
    
    def get_specialist_agent(self, agent_type: str, llm_provider: Optional[str] = None):
        """Get a specialist agent."""
        llm = self.get_llm(llm_provider)
        return self.langraph_config.create_specialist_agent(agent_type, llm)
    
    def add_custom_tool(self, name: str, tool: Any):
        """Add a custom tool to the system."""
        self.langraph_config.add_custom_tool(name, tool)
        # Also add to LangChain config if it's a tool config
        if hasattr(tool, 'name') and hasattr(tool, 'description'):
            self.langchain_config.add_tool(
                name=tool.name,
                description=tool.description,
                enabled=True
            )
    
    def add_custom_agent(self, name: str, agent_config: Any):
        """Add a custom agent to the system."""
        self.langraph_config.add_custom_agent(name, agent_config)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types."""
        return list(self.langraph_config.graph.agents.keys())
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return self.langraph_config.tool_registry.list_tools()
    
    def configure_for_environment(self, environment: str):
        """Configure the system for a specific environment."""
        if environment == "development":
            self.max_agent_iterations = 3
            self.enable_parallel_agents = False
        elif environment == "production":
            self.max_agent_iterations = 10
            self.enable_parallel_agents = True
        elif environment == "testing":
            self.max_agent_iterations = 1
            self.enable_parallel_agents = False


class RAGSystem:
    """Main RAG system class that orchestrates all components."""
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.supervisor_agent = None
        self.specialist_agents = {}
    
    def initialize(self, environment: str = "development"):
        """Initialize the RAG system."""
        self.config.configure_for_environment(environment)
        
        # Initialize supervisor agent
        self.supervisor_agent = self.config.get_supervisor_agent()
        
        # Initialize specialist agents
        for agent_type in ["local_knowledge", "web_search"]:
            self.specialist_agents[agent_type] = self.config.get_specialist_agent(agent_type)
        
        return self
    
    def query(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user query through the RAG system."""
        if not self.supervisor_agent:
            raise RuntimeError("RAG system not initialized. Call initialize() first.")
        
        # Prepare context
        context = context or {}
        context["user_query"] = user_query
        
        # Process through supervisor agent
        response = self.supervisor_agent.invoke({
            "messages": [{"role": "user", "content": user_query}],
            "context": context
        })
        
        # Extract the actual response content
        if isinstance(response, dict) and "messages" in response:
            response_content = response["messages"][0]["content"] if response["messages"] else str(response)
        else:
            response_content = str(response)
        
        return {
            "query": user_query,
            "response": response_content,
            "sources": context.get("sources", []),
            "confidence": context.get("confidence", 0.0)
        }
    
    def add_tool(self, name: str, tool: Any):
        """Add a custom tool to the system."""
        self.config.add_custom_tool(name, tool)
        # Reinitialize agents to include new tool
        self.initialize()
    
    def add_agent(self, name: str, agent_config: Any):
        """Add a custom agent to the system."""
        self.config.add_custom_agent(name, agent_config)
        # Reinitialize to include new agent
        self.initialize()


orchestrator_config = OrchestratorConfig()
rag_system = RAGSystem(orchestrator_config)
