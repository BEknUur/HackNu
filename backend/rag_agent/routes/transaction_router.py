"""
Transaction-aware RAG Router

This module provides API endpoints for RAG queries with transaction capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add the backend directory to path
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from rag_agent.config.orchestrator import rag_system
from rag_agent.tools import (
    set_transaction_context,
    set_account_context,
    set_transaction_history_context,
    set_product_context,
    set_cart_context,
)
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag/transaction", tags=["RAG-Transactions"])


class TransactionQueryRequest(BaseModel):
    """Request model for RAG queries with transaction support."""
    query: str
    user_id: int = Field(..., description="User ID performing the transaction")
    context: Optional[Dict[str, Any]] = None
    environment: str = "development"


class TransactionQueryResponse(BaseModel):
    """Response model for RAG queries with transaction support."""
    query: str
    response: str
    sources: list
    confidence: float
    status: str
    transaction_executed: bool = False


@router.post("/query", response_model=TransactionQueryResponse)
async def query_with_transactions(
    request: TransactionQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Process a query through the RAG system with transaction capabilities.
    
    This endpoint allows the RAG agent to perform financial transactions
    on behalf of a user.
    
    Args:
        request: Query request with query text, user_id, and optional context
        db: Database session
        
    Returns:
        TransactionQueryResponse: RAG system response with transaction status
        
    Examples:
        POST /api/rag/transaction/query
        {
            "query": "Deposit $500 to account 1",
            "user_id": 1,
            "environment": "production"
        }
    """
    try:
        # Set context for ALL tool categories
        set_transaction_context(user_id=request.user_id, db=db)
        set_account_context(user_id=request.user_id, db=db)
        set_transaction_history_context(user_id=request.user_id, db=db)
        set_product_context(user_id=request.user_id, db=db)
        set_cart_context(user_id=request.user_id, db=db)
        
        if not rag_system.supervisor_agent:
            rag_system.initialize(environment=request.environment)
        
        # Add user information to context
        context = request.context or {}
        context["user_id"] = request.user_id
        
        # Process the query
        result = rag_system.query(
            user_query=request.query,
            context=context
        )
        
        # Check if a transaction was executed
        transaction_executed = any(
            tool_name in ["deposit_money", "withdraw_money", "transfer_money", "purchase_product"]
            for source in result.get("sources", [])
            if isinstance(source, dict) and "tool" in source
            for tool_name in [source.get("tool", "")]
        )
        
        return TransactionQueryResponse(
            query=result["query"],
            response=result["response"],
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.0),
            status="success",
            transaction_executed=transaction_executed
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing transaction query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/capabilities")
async def get_transaction_capabilities():
    """
    Get the available transaction capabilities of the RAG system.
    
    Returns:
        Dict: Available transaction tools and their descriptions
    """
    return {
        "status": "available",
        "transaction_tools": [
            {
                "name": "deposit_money",
                "description": "Deposit money into an account",
                "parameters": {
                    "account_id": "int (required)",
                    "amount": "float (required, positive)",
                    "currency": "str (USD, EUR, KZT, default: USD)",
                    "description": "str (optional)"
                },
                "examples": [
                    "Deposit $500 to account 1",
                    "Add 1000 KZT to my account 2"
                ]
            },
            {
                "name": "withdraw_money",
                "description": "Withdraw money from an account",
                "parameters": {
                    "account_id": "int (required)",
                    "amount": "float (required, positive)",
                    "currency": "str (USD, EUR, KZT, default: USD)",
                    "description": "str (optional)"
                },
                "examples": [
                    "Withdraw $200 from account 1",
                    "Take out 500 KZT from account 2"
                ]
            },
            {
                "name": "transfer_money",
                "description": "Transfer money between accounts",
                "parameters": {
                    "from_account_id": "int (required)",
                    "to_account_id": "int (required)",
                    "amount": "float (required, positive)",
                    "currency": "str (USD, EUR, KZT, default: USD)",
                    "description": "str (optional)"
                },
                "examples": [
                    "Transfer $100 from account 1 to account 2",
                    "Send 5000 KZT from account 3 to account 4"
                ]
            },
            {
                "name": "purchase_product",
                "description": "Purchase a product using account funds",
                "parameters": {
                    "account_id": "int (required)",
                    "product_id": "int (required)",
                    "amount": "float (required, positive)",
                    "currency": "str (USD, EUR, KZT, default: USD)",
                    "description": "str (optional)"
                },
                "examples": [
                    "Buy product 5 for $50 from account 1",
                    "Purchase product 10 for 15000 KZT using account 2"
                ]
            }
        ],
        "notes": [
            "All transactions require user authentication",
            "User can only perform transactions on their own accounts",
            "Currency defaults to USD if not specified",
            "Amounts must be positive numbers"
        ]
    }


@router.post("/test")
async def test_transaction_query(
    query: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Test endpoint for transaction queries without actually executing them.
    
    This endpoint simulates transaction processing to help test query understanding.
    
    Args:
        query: The natural language query to test
        user_id: User ID for the test
        db: Database session
        
    Returns:
        Dict: Analysis of how the query would be processed
    """
    try:
        # Basic query analysis
        query_lower = query.lower()
        
        detected_action = None
        if "deposit" in query_lower or "add money" in query_lower:
            detected_action = "deposit_money"
        elif "withdraw" in query_lower or "take out" in query_lower:
            detected_action = "withdraw_money"
        elif "transfer" in query_lower or "send money" in query_lower:
            detected_action = "transfer_money"
        elif "buy" in query_lower or "purchase" in query_lower:
            detected_action = "purchase_product"
        
        return {
            "query": query,
            "user_id": user_id,
            "detected_action": detected_action,
            "would_execute": detected_action is not None,
            "message": f"Query would trigger '{detected_action}' tool" if detected_action else "No transaction detected in query",
            "note": "This is a test endpoint. Use /query for actual execution."
        }
        
    except Exception as e:
        logger.error(f"Error testing transaction query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
