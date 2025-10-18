"""
LangGraph Configuration Module

This module provides flexible configuration for LangGraph agent orchestration,
supporting dynamic tool registration and multi-agent workflows.
"""

from typing import Dict, Any, Optional, List, Callable, Type
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool


class AgentConfig(BaseModel):
    """Base configuration for agents."""
    name: str
    description: str
    enabled: bool = True
    tools: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    max_iterations: int = 5
    temperature: float = 0.3
    
    class Config:
        extra = "allow"


class SupervisorAgentConfig(AgentConfig):
    """Configuration for supervisor agent."""
    name: str = "supervisor"
    description: str = "Orchestrates and delegates tasks to specialized agents"
    tools: List[str] = ["vector_search", "web_search"]  # Supervisor has access to all tools
    system_prompt: str = """
You are an intelligent RAG (Retrieval-Augmented Generation) assistant that helps answer questions using available tools.

=== AVAILABLE TOOLS ===
1. vector_search:
   - Use for: Company policies, internal documents, procedures, local knowledge
   - Searches: Local knowledge base using semantic search
   - Example: "What is our remote work policy?"

2. web_search:
   - Use for: Current events, online information, recent news, public information
   - Searches: Web using Tavily API
   - Example: "Find information about ZamanBank", "What are the latest AI trends?"

=== DECISION PROCESS ===
1. ANALYZE the user's query:
   - Is this about internal company information? → Use vector_search
   - Is this about external/public information? → Use web_search
   - Is this about a specific company, product, or current event? → Use web_search
   - Need both internal and external info? → Use both tools

2. EXECUTE:
   - Call the appropriate tool(s) with clear, specific queries
   - Extract relevant information from tool results

3. SYNTHESIZE:
   - Provide a comprehensive answer based on tool results
   - Cite sources (document names, URLs, etc.)
   - If information is not found, state this clearly
   - DO NOT make up information

=== RESPONSE FORMAT ===
- Start with a direct answer to the user's question
- Include specific details and facts from the tool results
- Cite sources when available
- Keep responses clear and well-structured

Now, analyze the user's query and use the appropriate tools to answer it!
"""


class LocalKnowledgeAgentConfig(AgentConfig):
    """Configuration for local knowledge agent."""
    name: str = "local_knowledge_agent"
    description: str = "Searches through local knowledge base and company documents"
    tools: List[str] = ["vector_search"]
    system_prompt: str = """
You are a LOCAL KNOWLEDGE AGENT specialized in searching company documents and policies.

Your role:
- Search through internal documents, policies, and procedures
- Provide accurate information from the company knowledge base
- Cite specific documents and sections when possible
- If information is not found, clearly state this

Always use the vector_search tool to find relevant information.
"""


class WebSearchAgentConfig(AgentConfig):
    """Configuration for web search agent."""
    name: str = "web_search_agent"
    description: str = "Searches the web for current information and news"
    tools: List[str] = ["web_search"]
    system_prompt: str = """
You are a WEB SEARCH AGENT specialized in finding current information online.

Your role:
- Search the web for current events, news, and public information
- Provide up-to-date information with proper citations
- Focus on recent and relevant sources
- If information is not available or outdated, clearly state this

Always use the web_search tool to find current information.
"""




class ToolRegistry:
    """Registry for managing tools dynamically."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_factories: Dict[str, Callable] = {}
    
    def register_tool(self, name: str, tool: BaseTool):
        """Register a tool instance."""
        self._tools[name] = tool
    
    def register_tool_factory(self, name: str, factory: Callable):
        """Register a tool factory function."""
        self._tool_factories[name] = factory
    
    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by name."""
        if name in self._tools:
            return self._tools[name]
        elif name in self._tool_factories:
            tool = self._tool_factories[name]()
            self._tools[name] = tool
            return tool
        else:
            raise ValueError(f"Tool '{name}' not found in registry")
    
    def get_tools(self, names: List[str]) -> List[BaseTool]:
        """Get multiple tools by names."""
        return [self.get_tool(name) for name in names]
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(set(self._tools.keys()) | set(self._tool_factories.keys()))


class AgentFactory:
    """Factory for creating agents from configuration."""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self._agent_types: Dict[str, Type[AgentConfig]] = {
            "supervisor": SupervisorAgentConfig,
            "local_knowledge": LocalKnowledgeAgentConfig,
            "web_search": WebSearchAgentConfig,
        }
    
    def register_agent_type(self, name: str, config_class: Type[AgentConfig]):
        """Register a new agent type."""
        self._agent_types[name] = config_class
    
    def create_agent(self, agent_type: str, llm: Any, **overrides) -> Any:
        """Create an agent from configuration."""
        if agent_type not in self._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        config_class = self._agent_types[agent_type]
        config = config_class(**overrides)
        
        # Get tools for this agent
        tools = self.tool_registry.get_tools(config.tools)
        
        # Create a real LangGraph ReAct agent
        # Use messages_modifier instead of state_modifier (correct parameter name in LangGraph)
        return create_react_agent(
            model=llm,
            tools=tools,
            messages_modifier=config.system_prompt
        )


class GraphConfig(BaseModel):
    """Configuration for LangGraph workflows."""
    
    # Agent configurations
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    
    # Workflow settings
    max_iterations: int = 10
    enable_parallel_execution: bool = True
    enable_conditional_routing: bool = True
    
    # Error handling
    retry_attempts: int = 3
    fallback_agent: Optional[str] = None
    
    def add_agent(self, name: str, agent_config: AgentConfig):
        """Add an agent configuration."""
        self.agents[name] = agent_config
    
    def get_agent_config(self, name: str) -> AgentConfig:
        """Get agent configuration by name."""
        if name not in self.agents:
            raise ValueError(f"Agent '{name}' not found in configuration")
        return self.agents[name]


class LangGraphConfig(BaseModel):
    """Main LangGraph configuration."""
    
    # Graph configuration
    graph: GraphConfig = Field(default_factory=GraphConfig)
    
    # Tool registry - using Any to avoid Pydantic schema issues
    tool_registry: Any = Field(default_factory=ToolRegistry)
    
    # Agent factory - using Any to avoid Pydantic schema issues
    agent_factory: Optional[Any] = None
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, **data):
        super().__init__(**data)
        self.agent_factory = AgentFactory(self.tool_registry)
        self._setup_default_agents()
        self._setup_default_tools()
    
    def _setup_default_agents(self):
        """Setup default agent configurations."""
        self.graph.add_agent("supervisor", SupervisorAgentConfig())
        self.graph.add_agent("local_knowledge", LocalKnowledgeAgentConfig())
        self.graph.add_agent("web_search", WebSearchAgentConfig())
    
    def _setup_default_tools(self):
        """Setup default tool factories."""
        # Register tool factories that will be implemented in tools module
        self.tool_registry.register_tool_factory("vector_search", self._create_vector_search_tool)
        self.tool_registry.register_tool_factory("web_search", self._create_web_search_tool)
    
    def _create_vector_search_tool(self) -> BaseTool:
        """Create vector search tool."""
        import sys
        from pathlib import Path
        
        # Add the backend directory to the path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        from rag_agent.tools.vector_search import vector_search_tool
        return vector_search_tool
    
    def _create_web_search_tool(self) -> BaseTool:
        """Create web search tool."""
        import sys
        from pathlib import Path
        
        # Add the backend directory to the path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        from rag_agent.tools.web_search import web_search_tool
        return web_search_tool
    
    
    def create_supervisor_agent(self, llm: Any) -> Any:
        """Create the supervisor agent."""
        return self.agent_factory.create_agent("supervisor", llm)
    
    def create_specialist_agent(self, agent_type: str, llm: Any) -> Any:
        """Create a specialist agent."""
        return self.agent_factory.create_agent(agent_type, llm)
    
    def add_custom_tool(self, name: str, tool: BaseTool):
        """Add a custom tool to the registry."""
        self.tool_registry.register_tool(name, tool)
    
    def add_custom_agent(self, name: str, config: AgentConfig):
        """Add a custom agent configuration."""
        self.graph.add_agent(name, config)
        self.agent_factory.register_agent_type(name, type(config))

langraph_config = LangGraphConfig()
