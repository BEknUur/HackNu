"""
Tools module for the RAG system.
"""

from .vector_search import vector_search_tool, get_vector_store_status
from .web_search import web_search_tool, get_web_search_status

# Transaction action tools
from .transaction_tools import (
    deposit_money,
    withdraw_money,
    transfer_money,
    purchase_product,
    set_transaction_context,
    get_transaction_tools,
)

# Account information tools
from .account_tools import (
    get_account_balance,
    get_my_accounts,
    get_account_details,
    set_account_context,
)

# Transaction history tools
from .transaction_history_tools import (
    get_my_transactions,
    get_transaction_stats,
    get_account_transactions,
    get_transaction_details,
    set_transaction_history_context,
)

# Product browsing tools
from .product_tools import (
    search_products,
    get_product_details,
    get_products_by_category,
    get_featured_products,
    set_product_context,
)

# Shopping cart tools
from .cart_tools import (
    add_to_cart,
    get_my_cart,
    remove_from_cart,
    checkout_cart,
    clear_cart,
    set_cart_context,
)

# Financial goals tools
from .financial_goal_tools import (
    get_my_financial_goals,
    create_financial_goal,
    get_goal_analysis,
    get_financial_summary,
    set_goal_context,
)

__all__ = [
    # RAG tools
    "vector_search_tool",
    "web_search_tool",
    "get_vector_store_status",
    "get_web_search_status",
    
    # Transaction actions
    "deposit_money",
    "withdraw_money",
    "transfer_money",
    "purchase_product",
    "set_transaction_context",
    "get_transaction_tools",
    
    # Account information
    "get_account_balance",
    "get_my_accounts",
    "get_account_details",
    "set_account_context",
    
    # Transaction history
    "get_my_transactions",
    "get_transaction_stats",
    "get_account_transactions",
    "get_transaction_details",
    "set_transaction_history_context",
    
    # Product browsing
    "search_products",
    "get_product_details",
    "get_products_by_category",
    "get_featured_products",
    "set_product_context",
    
    # Shopping cart
    "add_to_cart",
    "get_my_cart",
    "remove_from_cart",
    "checkout_cart",
    "clear_cart",
    "set_cart_context",
    
    # Financial goals
    "get_my_financial_goals",
    "create_financial_goal",
    "get_goal_analysis",
    "get_financial_summary",
    "set_goal_context",
]

