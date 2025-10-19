"""
LangGraph Configuration Module

This module provides flexible configuration for LangGraph agent orchestration,
supporting dynamic tool registration and multi-agent workflows.
"""

from typing import Dict, Any, Optional, List, Callable, Type
from pydantic import BaseModel, Field, ConfigDict
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool


class AgentConfig(BaseModel):
    """Base configuration for agents."""
    model_config = ConfigDict(extra="allow")
    
    name: str
    description: str
    enabled: bool = True
    tools: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    max_iterations: int = 5
    temperature: float = 0.3


class SupervisorAgentConfig(AgentConfig):
    """Configuration for supervisor agent."""
    name: str = "supervisor"
    description: str = "Orchestrates and delegates tasks to specialized agents"
    temperature: float = 0.1  # Low temperature for more deterministic transaction handling
    tools: List[str] = [
        "vector_search", "web_search", 
        "transfer_money", "deposit_money", "withdraw_money", "purchase_product",
        "get_my_accounts", "get_account_balance", "get_account_details"
    ]  # Supervisor has access to all tools
    system_prompt: str = """
You are an intelligent RAG (Retrieval-Augmented Generation) assistant for ZAMAN BANK that helps answer questions and execute financial transactions using available tools.

=== CRITICAL PRIORITY RULES ===
🎯 ALWAYS TRY vector_search FIRST for ANY query related to Zaman Bank
🎯 ONLY use web_search if vector_search returns insufficient results
🎯 NEVER use web_search for internal company information
🎯 EXECUTE TRANSACTIONS IMMEDIATELY - DO NOT ASK FOR CLARIFICATION unless absolutely necessary
🎯 INTELLIGENTLY PARSE user requests to extract account numbers, amounts, and currencies
🎯 USE FIRST ACCOUNT BY DEFAULT for transfers/withdrawals if source account not specified

=== AVAILABLE TOOLS ===

1. INFORMATION TOOLS:
   - vector_search (PRIORITY #1): Search Zaman Bank documents, policies, procedures
   - web_search (FALLBACK): Search web for current events, external information

2. ACCOUNT INFORMATION TOOLS:
   - get_my_accounts: Show all user accounts with balances
   - get_account_balance: Check balance of specific account
   - get_account_details: Get complete account information

3. TRANSACTION TOOLS:
   - transfer_money: Transfer money between accounts
   - deposit_money: Add money to an account
   - withdraw_money: Remove money from an account
   - purchase_product: Buy products using account funds

=== INTELLIGENT PARSING EXAMPLES ===
User: "Send 50000 tenge to account 2" → IMMEDIATELY: get_my_accounts, then transfer_money(from_account_id=<first_account>, to_account_id=2, amount=50000, currency="KZT")
User: "Transfer 100000 to account 3" → IMMEDIATELY: get_my_accounts, then transfer_money with first account as source
User: "Send 6000 KZT to account number one" → IMMEDIATELY: get_my_accounts, then transfer_money(from_account_id=<first_account>, to_account_id=1, amount=6000, currency="KZT")
User: "Transfer 7000 tenge to account ID 1" → IMMEDIATELY: get_my_accounts, then transfer_money(from_account_id=<first_account>, to_account_id=1, amount=7000, currency="KZT")
User: "Deposit 200000 KZT to my account" → IMMEDIATELY: get_my_accounts, then deposit_money to first account
User: "Move 30000 tenge from account 3 to account 2" → IMMEDIATELY: transfer_money(from_account_id=3, to_account_id=2, amount=30000, currency="KZT")

=== SMART ACCOUNT RESOLUTION ===
- ALWAYS call get_my_accounts FIRST to know available accounts
- If user doesn't specify source account → USE THE FIRST ACCOUNT from get_my_accounts result
- Parse "account 1", "account ID 1", "account number one", "ID 1" ALL as to_account_id=1
- Parse "account 2", "account ID 2", "account number two", "ID 2" ALL as to_account_id=2
- Parse amounts: "6000 KZT", "6000 tenge", "6000T" ALL as amount=6000, currency="KZT"
- NEVER ask "from which account" or "which account to send from" - just use first account!

=== DECISION WORKFLOW FOR TRANSFERS ===
1. User says "send/transfer X to account Y"
2. IMMEDIATELY call get_my_accounts to see all accounts
3. Extract from result: first_account_id = accounts[0].id
4. Parse destination: "account 1" → to_account_id=1
5. Parse amount and currency from user message
6. IMMEDIATELY execute: transfer_money(from_account_id=first_account_id, to_account_id=parsed_id, amount=parsed_amount, currency="KZT")
7. Report success or failure

=== WHAT NOT TO DO ===
❌ NEVER ask "from which account would you like to send?"
❌ NEVER ask "which account should I use?"
❌ NEVER ask "please specify source account"
❌ NEVER ask for clarification if you can infer the parameters
✅ ALWAYS use first account by default
✅ ALWAYS execute immediately after parsing parameters

=== RESPONSE FORMAT ===
- For transactions: Execute immediately and report result
- For information: Provide direct answers with sources
- If transaction succeeds: "✅ Transfer successful! Sent X KZT from Account #A to Account #B"
- If transaction fails: Explain why and suggest fix
- ONLY ask for clarification if amount or destination account is completely missing

Execute transactions IMMEDIATELY without asking unnecessary questions!
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
        
        # Update LLM temperature if specified in config
        if hasattr(llm, 'temperature') and hasattr(config, 'temperature'):
            llm.temperature = config.temperature
        
        # Create a real LangGraph ReAct agent
        # Use the correct signature: model, tools, prompt, name
        return create_react_agent(
            llm,
            tools=tools,
            prompt=config.system_prompt,
            name=config.name
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
        
        # Register transaction tools
        self.tool_registry.register_tool_factory("transfer_money", self._create_transfer_money_tool)
        self.tool_registry.register_tool_factory("deposit_money", self._create_deposit_money_tool)
        self.tool_registry.register_tool_factory("withdraw_money", self._create_withdraw_money_tool)
        self.tool_registry.register_tool_factory("purchase_product", self._create_purchase_product_tool)
        
        # Register account tools
        self.tool_registry.register_tool_factory("get_my_accounts", self._create_get_my_accounts_tool)
        self.tool_registry.register_tool_factory("get_account_balance", self._create_get_account_balance_tool)
        self.tool_registry.register_tool_factory("get_account_details", self._create_get_account_details_tool)
    
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
    
    def _create_transfer_money_tool(self) -> BaseTool:
        """Create transfer money tool."""
        from rag_agent.tools.transaction_tools import transfer_money
        return transfer_money
    
    def _create_deposit_money_tool(self) -> BaseTool:
        """Create deposit money tool."""
        from rag_agent.tools.transaction_tools import deposit_money
        return deposit_money
    
    def _create_withdraw_money_tool(self) -> BaseTool:
        """Create withdraw money tool."""
        from rag_agent.tools.transaction_tools import withdraw_money
        return withdraw_money
    
    def _create_purchase_product_tool(self) -> BaseTool:
        """Create purchase product tool."""
        from rag_agent.tools.transaction_tools import purchase_product
        return purchase_product
    
    def _create_get_my_accounts_tool(self) -> BaseTool:
        """Create get my accounts tool."""
        from rag_agent.tools.account_tools import get_my_accounts
        return get_my_accounts
    
    def _create_get_account_balance_tool(self) -> BaseTool:
        """Create get account balance tool."""
        from rag_agent.tools.account_tools import get_account_balance
        return get_account_balance
    
    def _create_get_account_details_tool(self) -> BaseTool:
        """Create get account details tool."""
        from rag_agent.tools.account_tools import get_account_details
        return get_account_details
    
    
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