"""
Transaction Tools for RAG System

This module provides LangChain tools for handling financial transactions
through natural language interactions with the RAG agent.
"""

import os
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Add the backend directory to path
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database import get_db
from services.transaction.service import (
    create_deposit,
    create_withdrawal,
    create_transfer,
    create_purchase
)
from services.transaction.schemas import (
    TransactionDeposit,
    TransactionWithdrawal,
    TransactionTransfer,
    TransactionPurchase
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global context for user_id and database session
# This will be set by the API endpoint before using the tools
_transaction_context = {
    "user_id": None,
    "db": None
}


def set_transaction_context(user_id: int, db):
    """Set the transaction context for the current session."""
    _transaction_context["user_id"] = user_id
    _transaction_context["db"] = db


def get_transaction_context():
    """Get the current transaction context."""
    if not _transaction_context["user_id"]:
        raise ValueError("Transaction context not set. User ID is required.")
    if not _transaction_context["db"]:
        raise ValueError("Transaction context not set. Database session is required.")
    return _transaction_context


@tool
def deposit_money(
    account_id: int,
    amount: float,
    currency: str = "KZT",
    description: Optional[str] = None
) -> str:
    """
    Deposit money into a user's account.
    
    Use this tool when the user wants to add money to their account.
    
    Args:
        account_id: The ID of the account to deposit money into (required)
        amount: The amount of money to deposit (must be positive, required)
        currency: The currency code - only 'KZT' is supported (default: 'KZT')
        description: Optional description of the deposit
        
    Returns:
        A success message with transaction details or an error message
        
    Examples:
        - "Deposit 50000 KZT to account 1"
        - "Add 100000 KZT to my account 2"
        - "Deposit 450000 KZT to account 3 for salary"
    """
    try:
        context = get_transaction_context()
        user_id = context["user_id"]
        db = context["db"]
        
        # Validate amount
        if amount <= 0:
            return f"❌ Error: Amount must be positive. You provided: {amount}"
        
        # Create deposit data
        deposit_data = TransactionDeposit(
            account_id=account_id,
            amount=Decimal(str(amount)),
            currency=currency.upper(),
            description=description or f"Deposit via AI assistant"
        )
        
        # Execute deposit
        result = create_deposit(deposit_data, user_id, db)
        
        return f"""✅ Deposit successful!
Transaction ID: {result.id}
Amount: {amount} {currency}
Account ID: {account_id}
New Balance: Check account details for updated balance
Description: {description or 'Deposit via AI assistant'}"""
        
    except ValueError as e:
        return f"❌ Validation Error: {str(e)}"
    except Exception as e:
        logger.error(f"Deposit error: {str(e)}")
        return f"❌ Error processing deposit: {str(e)}"


@tool
def withdraw_money(
    account_id: int,
    amount: float,
    currency: str = "KZT",
    description: Optional[str] = None
) -> str:
    """
    Withdraw money from a user's account.
    
    Use this tool when the user wants to withdraw or take money out of their account.
    
    Args:
        account_id: The ID of the account to withdraw money from (required)
        amount: The amount of money to withdraw (must be positive, required)
        currency: The currency code - only 'KZT' is supported (default: 'KZT')
        description: Optional description of the withdrawal
        
    Returns:
        A success message with transaction details or an error message
        
    Examples:
        - "Withdraw 20000 KZT from account 1"
        - "Take out 50000 KZT from my account 2"
        - "Withdraw 100000 KZT from account 3"
    """
    try:
        context = get_transaction_context()
        user_id = context["user_id"]
        db = context["db"]
        
        # Validate amount
        if amount <= 0:
            return f"❌ Error: Amount must be positive. You provided: {amount}"
        
        # Create withdrawal data
        withdrawal_data = TransactionWithdrawal(
            account_id=account_id,
            amount=Decimal(str(amount)),
            currency=currency.upper(),
            description=description or f"Withdrawal via AI assistant"
        )
        
        # Execute withdrawal
        result = create_withdrawal(withdrawal_data, user_id, db)
        
        return f"""✅ Withdrawal successful!
Transaction ID: {result.id}
Amount: {amount} {currency}
Account ID: {account_id}
New Balance: Check account details for updated balance
Description: {description or 'Withdrawal via AI assistant'}"""
        
    except ValueError as e:
        return f"❌ Validation Error: {str(e)}"
    except Exception as e:
        logger.error(f"Withdrawal error: {str(e)}")
        return f"❌ Error processing withdrawal: {str(e)}"


@tool
def transfer_money(
    from_account_id: int,
    to_account_id: int,
    amount: float,
    currency: str = "KZT",
    description: Optional[str] = None
) -> str:
    """
    Transfer money from one account to another account.
    
    Use this tool when the user wants to send money to another account or person.
    IMPORTANT: If user doesn't specify source account, call get_my_accounts first and use the [DEFAULT_ACCOUNT_ID] from the response.
    
    Args:
        from_account_id: The ID of the source account (required). If not specified by user, use DEFAULT_ACCOUNT_ID from get_my_accounts
        to_account_id: The ID of the destination account (required). Parse from user input: "account 1", "account ID 1", "account number one" all mean to_account_id=1
        amount: The amount of money to transfer (must be positive, required). Parse from user: "6000", "6000 KZT", "6000 tenge", "6000T" all mean amount=6000
        currency: The currency code - only 'KZT' is supported (default: 'KZT')
        description: Optional description of the transfer
        
    Returns:
        A success message with transaction details or an error message
        
    Examples:
        - "Send 6000 tenge to account 1" → get_my_accounts, then transfer_money(from_account_id=<DEFAULT_ACCOUNT_ID>, to_account_id=1, amount=6000, currency="KZT")
        - "Transfer 100000 KZT to account 2" → get_my_accounts, then transfer_money(from_account_id=<DEFAULT_ACCOUNT_ID>, to_account_id=2, amount=100000, currency="KZT")
        - "Send 50000 from account 3 to account 4" → transfer_money(from_account_id=3, to_account_id=4, amount=50000, currency="KZT")
    """
    try:
        context = get_transaction_context()
        user_id = context["user_id"]
        db = context["db"]
        
        # Validate amount
        if amount <= 0:
            return f"❌ Error: Amount must be positive. You provided: {amount}"
        
        # Validate accounts are different
        if from_account_id == to_account_id:
            return f"❌ Error: Cannot transfer to the same account (Account {from_account_id})"
        
        # Create transfer data
        transfer_data = TransactionTransfer(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=Decimal(str(amount)),
            currency=currency.upper(),
            description=description or f"Transfer via AI assistant"
        )
        
        # Execute transfer
        result = create_transfer(transfer_data, user_id, db)
        
        return f"""✅ Transfer successful!
Transaction ID: {result.id}
Amount: {amount} {currency}
From Account: {from_account_id}
To Account: {to_account_id}
Description: {description or 'Transfer via AI assistant'}"""
        
    except ValueError as e:
        return f"❌ Validation Error: {str(e)}"
    except Exception as e:
        logger.error(f"Transfer error: {str(e)}")
        return f"❌ Error processing transfer: {str(e)}"


@tool
def purchase_product(
    account_id: int,
    product_id: int,
    amount: float,
    currency: str = "USD",
    description: Optional[str] = None
) -> str:
    """
    Purchase a product using money from a user's account.
    
    Use this tool when the user wants to buy a product or make a purchase.
    
    Args:
        account_id: The ID of the account to charge (required)
        product_id: The ID of the product to purchase (required)
        amount: The purchase amount (must be positive, required)
        currency: The currency code - 'USD', 'EUR', or 'KZT' (default: 'USD')
        description: Optional description of the purchase
        
    Returns:
        A success message with transaction details or an error message
        
    Examples:
        - "Buy product 5 for $50 from account 1"
        - "Purchase product 10 using account 2 for 15000 KZT"
        - "Buy item 3 for 30 euros from my account 4"
    """
    try:
        context = get_transaction_context()
        user_id = context["user_id"]
        db = context["db"]
        
        # Validate amount
        if amount <= 0:
            return f"❌ Error: Amount must be positive. You provided: {amount}"
        
        # Create purchase data
        purchase_data = TransactionPurchase(
            account_id=account_id,
            product_id=product_id,
            amount=Decimal(str(amount)),
            currency=currency.upper(),
            description=description or f"Product purchase via AI assistant"
        )
        
        # Execute purchase
        result = create_purchase(purchase_data, user_id, db)
        
        return f"""✅ Purchase successful!
Transaction ID: {result.id}
Product ID: {product_id}
Amount: {amount} {currency}
Account ID: {account_id}
Description: {description or 'Product purchase via AI assistant'}"""
        
    except ValueError as e:
        return f"❌ Validation Error: {str(e)}"
    except Exception as e:
        logger.error(f"Purchase error: {str(e)}")
        return f"❌ Error processing purchase: {str(e)}"


# Tool registry for easy access
TRANSACTION_TOOLS = [
    deposit_money,
    withdraw_money,
    transfer_money,
    purchase_product
]


def get_transaction_tools():
    """Get all transaction tools."""
    return TRANSACTION_TOOLS
