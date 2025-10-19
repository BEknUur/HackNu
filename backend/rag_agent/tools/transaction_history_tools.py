"""
Transaction History Tools for RAG Agent

This module provides LangChain tools for querying transaction history
and analytics. Users can view past transactions, get spending statistics,
and analyze their financial activity.

Tools:
- get_my_transactions: View transaction history with filters
- get_transaction_stats: Get spending and income statistics
- get_account_transactions: View transactions for a specific account
- get_transaction_details: Get details of a single transaction
"""

from langchain_core.tools import tool
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from services.transaction import service as transaction_service
from services.transaction.schemas import TransactionHistoryFilter


# Global context for user_id and db session
_transaction_history_context: Dict[str, Any] = {}


def set_transaction_history_context(user_id: int, db):
    """
    Set the context for transaction history tools.
    
    This must be called before using any transaction history tools to provide
    the user_id and database session.
    
    Args:
        user_id: The ID of the user making the request
        db: SQLAlchemy database session
    """
    global _transaction_history_context
    _transaction_history_context = {"user_id": user_id, "db": db}


@tool
def get_my_transactions(limit: int = 10, transaction_type: Optional[str] = None) -> str:
    """
    View recent transaction history for the current user.
    
    This tool shows the user's recent transactions across all accounts,
    with optional filtering by transaction type. Useful for checking
    recent activity or finding specific types of transactions.
    
    Args:
        limit: Maximum number of transactions to show (default: 10, max: 50)
        transaction_type: Filter by type ('deposit', 'withdrawal', 'transfer', 'purchase')
        
    Returns:
        A formatted list of recent transactions with dates, types, amounts,
        and descriptions.
        
    Examples:
        User: "Show my last 10 transactions"
        User: "What are my recent transactions?"
        User: "Show my last 5 purchases"
        User: "What deposits did I make recently?"
        User: "Show my transaction history"
    """
    try:
        user_id = _transaction_history_context.get("user_id")
        db = _transaction_history_context.get("db")
        
        if not user_id or not db:
            return "Error: Transaction history context not set. Please try again."
        
        # Limit the number of transactions
        limit = min(limit, 50)
        
        # Build filters
        filters = TransactionHistoryFilter(
            transaction_type=transaction_type
        )
        
        # Get transactions
        transactions = transaction_service.get_user_transactions(
            user_id, db, filters, include_deleted=False, skip=0, limit=limit
        )
        
        if not transactions:
            if transaction_type:
                return f"You don't have any {transaction_type} transactions yet."
            return "You don't have any transactions yet."
        
        # Format transaction list
        response = f"Your last {len(transactions)} transaction(s)"
        if transaction_type:
            response += f" ({transaction_type}s)"
        response += ":\n\n"
        
        for txn in transactions:
            # Format date
            date_str = txn.created_at.strftime('%Y-%m-%d %H:%M')
            
            # Format type
            type_emoji = {
                'deposit': '💵',
                'withdrawal': '💸',
                'transfer': '↔️',
                'purchase': '🛒'
            }.get(txn.transaction_type, '💳')
            
            # Format description
            desc = f" - {txn.description}" if txn.description else ""
            
            response += f"{type_emoji} {date_str} | {txn.transaction_type.title()}: "
            response += f"{txn.amount} {txn.currency}{desc}\n"
            response += f"   Account: #{txn.account_id}"
            
            if txn.transaction_type == 'transfer' and txn.to_account_id:
                response += f" → #{txn.to_account_id}"
            elif txn.transaction_type == 'purchase' and txn.product_id:
                response += f" | Product: #{txn.product_id}"
            
            response += "\n\n"
        
        return response
        
    except Exception as e:
        return f"Error getting transactions: {str(e)}"


@tool
def get_transaction_stats(currency: str = "USD", days: int = 30) -> str:
    """
    Get spending and income statistics for a specified time period.
    
    This tool analyzes the user's financial activity and provides statistics
    including total deposits, withdrawals, transfers, and purchases. Useful
    for understanding spending patterns and financial behavior.
    
    Args:
        currency: Currency to calculate stats for (default: 'USD')
        days: Number of days to analyze (default: 30, max: 365)
        
    Returns:
        A formatted report with statistics on deposits, withdrawals, transfers,
        purchases, and net balance change.
        
    Examples:
        User: "How much did I spend this month?"
        User: "What are my transaction statistics?"
        User: "Show my spending for the last 30 days"
        User: "How much did I deposit this week?"
        User: "What's my net balance change?"
    """
    try:
        user_id = _transaction_history_context.get("user_id")
        db = _transaction_history_context.get("db")
        
        if not user_id or not db:
            return "Error: Transaction history context not set. Please try again."
        
        # Limit days
        days = min(days, 365)
        
        # Calculate date range
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)
        
        # Get statistics
        stats = transaction_service.get_user_transaction_stats(
            user_id, currency, db, date_from, date_to
        )
        
        # Format response
        response = f"📊 Transaction Statistics ({days} days, {currency}):\n\n"
        response += f"Total Transactions: {stats.total_transactions}\n\n"
        
        response += f"💵 Deposits:\n"
        response += f"   Count: {stats.total_deposits_count}\n"
        response += f"   Amount: {stats.total_deposits_amount} {currency}\n\n"
        
        response += f"💸 Withdrawals:\n"
        response += f"   Count: {stats.total_withdrawals_count}\n"
        response += f"   Amount: {stats.total_withdrawals_amount} {currency}\n\n"
        
        response += f"↔️ Transfers:\n"
        response += f"   Sent: {stats.total_transfers_sent_count} ({stats.total_transfers_sent_amount} {currency})\n"
        response += f"   Received: {stats.total_transfers_received_count} ({stats.total_transfers_received_amount} {currency})\n\n"
        
        response += f"🛒 Purchases:\n"
        response += f"   Count: {stats.total_purchases_count}\n"
        response += f"   Amount: {stats.total_purchases_amount} {currency}\n\n"
        
        # Calculate net change
        net_in = float(stats.total_deposits_amount) + float(stats.total_transfers_received_amount)
        net_out = float(stats.total_withdrawals_amount) + float(stats.total_transfers_sent_amount) + float(stats.total_purchases_amount)
        net_change = net_in - net_out
        
        response += f"📈 Net Balance Change: {net_change:+.2f} {currency}\n"
        
        if net_change > 0:
            response += "   ✅ You've increased your balance!"
        elif net_change < 0:
            response += "   ⚠️ You've decreased your balance."
        else:
            response += "   ➡️ Your balance is unchanged."
        
        return response
        
    except Exception as e:
        return f"Error getting transaction statistics: {str(e)}"


@tool
def get_account_transactions(account_id: int, limit: int = 10) -> str:
    """
    View transaction history for a specific account.
    
    This tool shows all transactions related to a specific account,
    including transactions where the account was the source or destination.
    Useful for account-specific transaction analysis.
    
    Args:
        account_id: The ID of the account to view transactions for
        limit: Maximum number of transactions to show (default: 10, max: 50)
        
    Returns:
        A formatted list of transactions for the specified account.
        
    Examples:
        User: "Show transactions for account 1"
        User: "What transactions happened in my savings account?"
        User: "Show history for account 2"
        User: "What activity is there in account 3?"
    """
    try:
        user_id = _transaction_history_context.get("user_id")
        db = _transaction_history_context.get("db")
        
        if not user_id or not db:
            return "Error: Transaction history context not set. Please try again."
        
        # Limit the number of transactions
        limit = min(limit, 50)
        
        # Get account transactions
        transactions = transaction_service.get_account_transactions(
            account_id, user_id, db, include_deleted=False, skip=0, limit=limit
        )
        
        if not transactions:
            return f"No transactions found for account #{account_id}."
        
        # Format transaction list
        response = f"Transaction history for Account #{account_id} ({len(transactions)} transaction(s)):\n\n"
        
        for txn in transactions:
            # Format date
            date_str = txn.created_at.strftime('%Y-%m-%d %H:%M')
            
            # Format type with emoji
            type_emoji = {
                'deposit': '💵',
                'withdrawal': '💸',
                'transfer': '↔️',
                'purchase': '🛒'
            }.get(txn.transaction_type, '💳')
            
            # Determine if this is incoming or outgoing
            direction = ""
            if txn.transaction_type == 'transfer':
                if txn.account_id == account_id:
                    direction = " (Sent)"
                elif txn.to_account_id == account_id:
                    direction = " (Received)"
            
            # Format description
            desc = f" - {txn.description}" if txn.description else ""
            
            response += f"{type_emoji} {date_str} | {txn.transaction_type.title()}{direction}: "
            response += f"{txn.amount} {txn.currency}{desc}\n\n"
        
        return response
        
    except Exception as e:
        return f"Error getting account transactions: {str(e)}"


@tool
def get_transaction_details(transaction_id: int) -> str:
    """
    Get complete details of a specific transaction.
    
    This tool provides full information about a single transaction including
    all fields, timestamps, and related accounts/products.
    
    Args:
        transaction_id: The ID of the transaction to view
        
    Returns:
        A formatted string with complete transaction information.
        
    Examples:
        User: "Show transaction #123"
        User: "What are the details of transaction 5?"
        User: "Tell me about my last transaction"
    """
    try:
        user_id = _transaction_history_context.get("user_id")
        db = _transaction_history_context.get("db")
        
        if not user_id or not db:
            return "Error: Transaction history context not set. Please try again."
        
        # Get transaction
        transaction = transaction_service.get_transaction(transaction_id, db)
        
        # Verify user has access to this transaction
        from services.account import service as account_service
        account = account_service.get_account(transaction.account_id, db)
        
        if account.user_id != user_id:
            # Check if it's a transfer and user owns the destination account
            if transaction.to_account_id:
                to_account = account_service.get_account(transaction.to_account_id, db)
                if to_account.user_id != user_id:
                    return "Error: You don't have permission to view this transaction."
            else:
                return "Error: You don't have permission to view this transaction."
        
        # Format transaction details
        type_emoji = {
            'deposit': '💵',
            'withdrawal': '💸',
            'transfer': '↔️',
            'purchase': '🛒'
        }.get(transaction.transaction_type, '💳')
        
        details = f"{type_emoji} Transaction #{transaction.id} Details:\n\n"
        details += f"Type: {transaction.transaction_type.title()}\n"
        details += f"Amount: {transaction.amount} {transaction.currency}\n"
        details += f"From Account: #{transaction.account_id}\n"
        
        if transaction.to_account_id:
            details += f"To Account: #{transaction.to_account_id}\n"
        
        if transaction.product_id:
            details += f"Product: #{transaction.product_id}\n"
        
        if transaction.description:
            details += f"Description: {transaction.description}\n"
        
        details += f"\n📅 Created: {transaction.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        details += f"🔄 Updated: {transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return details
        
    except Exception as e:
        return f"Error getting transaction details: {str(e)}"
