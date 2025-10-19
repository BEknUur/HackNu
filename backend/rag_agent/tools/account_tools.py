"""
Account Information Tools for RAG Agent

This module provides LangChain tools for querying account information
through natural language. Users can check balances, view all accounts,
and get detailed account information.

Tools:
- get_account_balance: Check the balance of a specific account
- get_my_accounts: List all user accounts with balances
- get_account_details: Get complete account information
"""

from langchain_core.tools import tool
from typing import Dict, Any
from services.account import service as account_service


# Global context for user_id and db session
_account_context: Dict[str, Any] = {}


def set_account_context(user_id: int, db):
    """
    Set the context for account tools.
    
    This must be called before using any account tools to provide
    the user_id and database session.
    
    Args:
        user_id: The ID of the user making the request
        db: SQLAlchemy database session
    """
    global _account_context
    _account_context = {"user_id": user_id, "db": db}


@tool
def get_account_balance(account_id: int) -> str:
    """
    Get the current balance of a specific account.
    
    This tool checks the balance and currency of an account that belongs
    to the current user. It will not show balances for accounts owned by
    other users.
    
    Args:
        account_id: The ID of the account to check (must be owned by user)
        
    Returns:
        A formatted string showing the account type, balance, and currency,
        or an error message if the account cannot be accessed.
        
    Examples:
        User: "What's my balance in account 1?"
        User: "How much money is in my savings account 2?"
        User: "Check balance of account 3"
        User: "Show me the balance"
    """
    try:
        user_id = _account_context.get("user_id")
        db = _account_context.get("db")
        
        if not user_id or not db:
            return "Error: Account context not set. Please try again."
        
        # Get account from service layer
        account = account_service.get_account(account_id, db)
        
        # Verify ownership
        if account.user_id != user_id:
            return f"Error: You don't have permission to view account {account_id}. This account belongs to another user."
        
        # Check if account is active
        if account.status != 'active':
            status_msg = f" (Status: {account.status})"
        else:
            status_msg = ""
        
        return f"Account #{account_id} ({account.account_type.title()}): {account.balance} {account.currency}{status_msg}"
        
    except Exception as e:
        return f"Error getting account balance: {str(e)}"


@tool
def get_my_accounts(user_id: int = None) -> str:
    """
    List all accounts belonging to the current user with their balances.
    
    This tool shows all active accounts owned by the user, including
    their type, balance, and currency. It provides a complete overview
    of the user's financial accounts.
    
    Args:
        user_id: Optional user ID (will use context user_id if not provided)
        
    Returns:
        A formatted string listing all accounts with their details,
        including total balance across all accounts in each currency.
        
    Examples:
        User: "Show me all my accounts"
        User: "What accounts do I have?"
        User: "List my bank accounts"
        User: "How much money do I have in total?"
        User: "What's my financial status?"
    """
    try:
        context_user_id = _account_context.get("user_id")
        db = _account_context.get("db")
        
        if not context_user_id or not db:
            return "Error: Account context not set. Please try again."
        
        # Use provided user_id or context user_id
        effective_user_id = user_id if user_id is not None else context_user_id
        
        # Get all user accounts (only active ones)
        accounts = account_service.get_user_accounts(effective_user_id, db, include_deleted=False)
        
        if not accounts:
            return "❌ Error: No active accounts found for this user. Please contact support to activate your account."
        
        # Format account list
        account_lines = []
        currency_totals = {}
        
        for account in accounts:
            # Skip inactive accounts
            if account.status != 'active':
                continue
                
            account_lines.append(
                f"  • Account #{account.id} ({account.account_type.title()}): "
                f"{account.balance} {account.currency}"
            )
            
            # Calculate totals by currency
            currency = account.currency
            if currency not in currency_totals:
                currency_totals[currency] = 0
            currency_totals[currency] += float(account.balance)
        
        # Build response with explicit first account ID
        first_account_id = accounts[0].id if accounts else None
        response = f"You have {len(account_lines)} active account(s):\n"
        if first_account_id:
            response += f"[DEFAULT_ACCOUNT_ID: {first_account_id}]\n\n"
        else:
            response += "\n"
        
        response += "\n".join(account_lines)
        
        # Add totals
        if currency_totals:
            response += "\n\nTotal Balance:\n"
            for currency, total in currency_totals.items():
                response += f"  • {total:.2f} {currency}\n"
        
        return response
        
    except Exception as e:
        return f"Error getting accounts: {str(e)}"


@tool
def get_account_details(account_id: int) -> str:
    """
    Get complete information about a specific account.
    
    This tool provides full details about an account including its type,
    balance, currency, status, creation date, and last update time.
    Useful for getting comprehensive account information.
    
    Args:
        account_id: The ID of the account to get details for
        
    Returns:
        A formatted string with complete account information including
        type, balance, currency, status, and timestamps.
        
    Examples:
        User: "Tell me about account 1"
        User: "What's the full info for my account 2?"
        User: "Show details of account 3"
        User: "Give me information about my savings account"
    """
    try:
        user_id = _account_context.get("user_id")
        db = _account_context.get("db")
        
        if not user_id or not db:
            return "Error: Account context not set. Please try again."
        
        # Get account from service layer
        account = account_service.get_account(account_id, db)
        
        # Verify ownership
        if account.user_id != user_id:
            return f"Error: You don't have permission to view account {account_id}."
        
        # Format account details
        details = f"""Account #{account.id} Details:

📋 Account Type: {account.account_type.title()}
💰 Balance: {account.balance} {account.currency}
📊 Status: {account.status.title()}
📅 Created: {account.created_at.strftime('%Y-%m-%d %H:%M')}
🔄 Last Updated: {account.updated_at.strftime('%Y-%m-%d %H:%M')}
"""
        
        # Add status-specific messages
        if account.status == 'blocked':
            details += "\n⚠️ This account is currently blocked and cannot be used for transactions."
        elif account.status == 'closed':
            details += "\n⚠️ This account has been closed."
        
        return details
        
    except Exception as e:
        return f"Error getting account details: {str(e)}"
