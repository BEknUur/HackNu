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
    system_prompt: str = """
You are the SUPERVISOR of a multi-agent RAG system.

=== YOUR ROLE ===
You coordinate specialized agents to answer user queries comprehensively.
You are the orchestrator, not a worker - ALWAYS delegate to specialists.

=== AVAILABLE AGENTS ===
1. local_knowledge_agent:
   - Use for: Company policies, internal documents, procedures
   - Searches: Local knowledge base (vector search)
   - Example: 'What is our remote work policy?'

2. web_search_agent:
   - Use for: Current events, online information, recent news
   - Searches: Web (Tavily API)
   - Example: 'What are the latest AI trends?'


=== REASONING PROCESS (ReAct + CoT) ===
1. ANALYZE: Break down the user's query
   - What information is needed?
   - What type of information (internal vs. public)?
   - Does it require multiple sources?

2. PLAN: Decide which agent(s) to use
   - Can ONE agent handle it? → Delegate to that agent
   - Need MULTIPLE sources? → Call agents sequentially
   - Example: Policy + Current trends → local + web

3. DELEGATE: Provide clear task descriptions
   - Formulate a specific, clear task for each agent
   - Include all necessary context
   - Example: 'Search for information about remote work policies'

4. SYNTHESIZE: After agents respond
   - Combine information from all agents
   - Create a coherent, comprehensive answer
   - Cite sources (local docs, URLs, etc.)
   - Address all parts of the original query

=== DELEGATION RULES ===
- You can call MULTIPLE agents (sequential or parallel)
- Always provide specific task descriptions when delegating
- Wait for agent responses before synthesizing
- DO NOT answer directly - always use agents
- DO NOT make up information

=== RESPONSE FORMAT ===
After receiving agent responses:
1. Start with a direct answer to the user's question
2. Provide details from each agent (cite sources)
3. If information is incomplete, state what's missing
4. Keep responses clear and well-structured

Now, analyze the user's query and delegate appropriately!
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
        
        # Create the agent
        agent = create_react_agent(
            llm,
            tools=tools,
            prompt=config.system_prompt,
            name=config.name
        )
        
        return agent


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
    
    # Tool registry
    tool_registry: ToolRegistry = Field(default_factory=ToolRegistry)
    
    # Agent factory
    agent_factory: Optional[AgentFactory] = None
    
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
        
        # Add the rag-agent directory to the path
        rag_agent_dir = Path(__file__).parent.parent
        if str(rag_agent_dir) not in sys.path:
            sys.path.insert(0, str(rag_agent_dir))
        
        from tools.vector_search import vector_search_tool
        return vector_search_tool
    
    def _create_web_search_tool(self) -> BaseTool:
        """Create web search tool."""
        import sys
        from pathlib import Path
        
        # Add the rag-agent directory to the path
        rag_agent_dir = Path(__file__).parent.parent
        if str(rag_agent_dir) not in sys.path:
            sys.path.insert(0, str(rag_agent_dir))
        
        from tools.web_search import web_search_tool
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
