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
    # Supervisor has access to ALL tools
    tools: List[str] = [
        # RAG tools
        "vector_search", 
        "web_search",
        # Account tools
        "get_account_balance",
        "get_my_accounts",
        "get_account_details",
        # Transaction action tools
        "deposit_money",
        "withdraw_money",
        "transfer_money",
        "purchase_product",
        # Transaction history tools
        "get_my_transactions",
        "get_transaction_stats",
        "get_account_transactions",
        "get_transaction_details",
        # Product tools
        "search_products",
        "get_product_details",
        "get_products_by_category",
        "get_featured_products",
        # Cart tools
        "add_to_cart",
        "get_my_cart",
        "remove_from_cart",
        "checkout_cart",
        "clear_cart",
    ]
    system_prompt: str = """
You are an intelligent assistant for ZAMAN BANK with access to comprehensive banking tools.

=== AVAILABLE TOOLS ===

📚 KNOWLEDGE SEARCH:
- vector_search: Search Zaman Bank's internal knowledge base and documents
- web_search: Search the web for current information

💰 ACCOUNT MANAGEMENT:
- get_my_accounts: List all user's accounts with balances
- get_account_balance: Check balance of a specific account
- get_account_details: Get complete account information

💳 TRANSACTIONS:
- deposit_money: Deposit money into an account
- withdraw_money: Withdraw money from an account
- transfer_money: Transfer money between accounts
- get_my_transactions: View user's transaction history
- get_account_transactions: View transactions for specific account
- get_transaction_stats: Get transaction statistics
- get_transaction_details: Get details of a specific transaction

🛍️ SHOPPING:
- search_products: Search for products
- get_product_details: Get product information
- get_products_by_category: Browse products by category
- get_featured_products: View featured products
- add_to_cart: Add product to cart
- get_my_cart: View shopping cart
- remove_from_cart: Remove item from cart
- checkout_cart: Purchase items in cart
- clear_cart: Empty shopping cart
- purchase_product: Quick purchase without cart

=== INSTRUCTIONS ===
1. For account/balance questions → Use get_my_accounts or get_account_balance
2. For transaction history → Use get_my_transactions
3. For Zaman Bank information → Use vector_search
4. For current events → Use web_search
5. For shopping → Use product and cart tools
6. Always provide clear, helpful responses with specific data

When user asks "how much money do I have", use get_my_accounts to show all accounts!
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
        # RAG tools
        self.tool_registry.register_tool_factory("vector_search", self._create_vector_search_tool)
        self.tool_registry.register_tool_factory("web_search", self._create_web_search_tool)
        
        # Account tools
        self.tool_registry.register_tool_factory("get_account_balance", self._create_account_balance_tool)
        self.tool_registry.register_tool_factory("get_my_accounts", self._create_my_accounts_tool)
        self.tool_registry.register_tool_factory("get_account_details", self._create_account_details_tool)
        
        # Transaction action tools
        self.tool_registry.register_tool_factory("deposit_money", self._create_deposit_tool)
        self.tool_registry.register_tool_factory("withdraw_money", self._create_withdraw_tool)
        self.tool_registry.register_tool_factory("transfer_money", self._create_transfer_tool)
        self.tool_registry.register_tool_factory("purchase_product", self._create_purchase_tool)
        
        # Transaction history tools
        self.tool_registry.register_tool_factory("get_my_transactions", self._create_my_transactions_tool)
        self.tool_registry.register_tool_factory("get_transaction_stats", self._create_transaction_stats_tool)
        self.tool_registry.register_tool_factory("get_account_transactions", self._create_account_transactions_tool)
        self.tool_registry.register_tool_factory("get_transaction_details", self._create_transaction_details_tool)
        
        # Product tools
        self.tool_registry.register_tool_factory("search_products", self._create_search_products_tool)
        self.tool_registry.register_tool_factory("get_product_details", self._create_product_details_tool)
        self.tool_registry.register_tool_factory("get_products_by_category", self._create_products_by_category_tool)
        self.tool_registry.register_tool_factory("get_featured_products", self._create_featured_products_tool)
        
        # Cart tools
        self.tool_registry.register_tool_factory("add_to_cart", self._create_add_to_cart_tool)
        self.tool_registry.register_tool_factory("get_my_cart", self._create_my_cart_tool)
        self.tool_registry.register_tool_factory("remove_from_cart", self._create_remove_from_cart_tool)
        self.tool_registry.register_tool_factory("checkout_cart", self._create_checkout_cart_tool)
        self.tool_registry.register_tool_factory("clear_cart", self._create_clear_cart_tool)
    
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
    
    # Account tools
    def _create_account_balance_tool(self) -> BaseTool:
        """Create account balance tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.account_tools import get_account_balance
        return get_account_balance
    
    def _create_my_accounts_tool(self) -> BaseTool:
        """Create my accounts tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.account_tools import get_my_accounts
        return get_my_accounts
    
    def _create_account_details_tool(self) -> BaseTool:
        """Create account details tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.account_tools import get_account_details
        return get_account_details
    
    # Transaction action tools
    def _create_deposit_tool(self) -> BaseTool:
        """Create deposit tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.transaction_tools import deposit_money
        return deposit_money
    
    def _create_withdraw_tool(self) -> BaseTool:
        """Create withdraw tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.transaction_tools import withdraw_money
        return withdraw_money
    
    def _create_transfer_tool(self) -> BaseTool:
        """Create transfer tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.transaction_tools import transfer_money
        return transfer_money
    
    def _create_purchase_tool(self) -> BaseTool:
        """Create purchase tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.transaction_tools import purchase_product
        return purchase_product
    
    # Transaction history tools
    def _create_my_transactions_tool(self) -> BaseTool:
        """Create my transactions tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.transaction_history_tools import get_my_transactions
        return get_my_transactions
    
    def _create_transaction_stats_tool(self) -> BaseTool:
        """Create transaction stats tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.transaction_history_tools import get_transaction_stats
        return get_transaction_stats
    
    def _create_account_transactions_tool(self) -> BaseTool:
        """Create account transactions tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.transaction_history_tools import get_account_transactions
        return get_account_transactions
    
    def _create_transaction_details_tool(self) -> BaseTool:
        """Create transaction details tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.transaction_history_tools import get_transaction_details
        return get_transaction_details
    
    # Product tools
    def _create_search_products_tool(self) -> BaseTool:
        """Create search products tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.product_tools import search_products
        return search_products
    
    def _create_product_details_tool(self) -> BaseTool:
        """Create product details tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.product_tools import get_product_details
        return get_product_details
    
    def _create_products_by_category_tool(self) -> BaseTool:
        """Create products by category tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.product_tools import get_products_by_category
        return get_products_by_category
    
    def _create_featured_products_tool(self) -> BaseTool:
        """Create featured products tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.product_tools import get_featured_products
        return get_featured_products
    
    # Cart tools
    def _create_add_to_cart_tool(self) -> BaseTool:
        """Create add to cart tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.cart_tools import add_to_cart
        return add_to_cart
    
    def _create_my_cart_tool(self) -> BaseTool:
        """Create my cart tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.cart_tools import get_my_cart
        return get_my_cart
    
    def _create_remove_from_cart_tool(self) -> BaseTool:
        """Create remove from cart tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.cart_tools import remove_from_cart
        return remove_from_cart
    
    def _create_checkout_cart_tool(self) -> BaseTool:
        """Create checkout cart tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.cart_tools import checkout_cart
        return checkout_cart
    
    def _create_clear_cart_tool(self) -> BaseTool:
        """Create clear cart tool."""
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rag_agent.tools.cart_tools import clear_cart
        return clear_cart
    
    
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
