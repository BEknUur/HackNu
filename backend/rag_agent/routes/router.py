from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config.orchestrator import rag_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    query: str
    context: Optional[Dict[str, Any]] = None
    environment: str = "development"


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    query: str
    response: str
    sources: list
    confidence: float
    status: str


@router.post("/query", response_model=QueryResponse)
async def query_rag_system(request: QueryRequest):
    """
    Process a query through the RAG system.
    
    Args:
        request: Query request with query text and optional context
        
    Returns:
        QueryResponse: RAG system response with sources and confidence
    """
    try:
        # Initialize the RAG system if not already done
        if not rag_system.supervisor_agent:
            rag_system.initialize(environment=request.environment)
        
        # Process the query
        result = rag_system.query(
            user_query=request.query,
            context=request.context or {}
        )
        
        return QueryResponse(
            query=result["query"],
            response=result["response"],
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.0),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error processing RAG query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/status")
async def get_system_status():
    """
    Get the current status of the RAG system.
    
    Returns:
        Dict: System status information
    """
    try:
        return {
            "status": "operational",
            "supervisor_agent": rag_system.supervisor_agent is not None,
            "specialist_agents": list(rag_system.specialist_agents.keys()),
            "available_tools": rag_system.config.get_available_tools(),
            "available_agents": rag_system.config.get_available_agents()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.post("/initialize")
async def initialize_system(environment: str = "development"):
    """
    Initialize the RAG system.
    
    Args:
        environment: Environment to initialize for (development, production, testing)
        
    Returns:
        Dict: Initialization status
    """
    try:
        rag_system.initialize(environment=environment)
        return {
            "status": "initialized",
            "environment": environment,
            "message": "RAG system initialized successfully"
        }
    except Exception as e:
        logger.error(f"Error initializing RAG system: {e}")
        raise HTTPException(status_code=500, detail=f"Error initializing system: {str(e)}")


@router.get("/tools/status")
async def get_tools_status():
    """
    Get the status of all tools in the system.
    
    Returns:
        Dict: Status of all tools
    """
    try:
        from tools.vector_search import get_vector_store_status
        from tools.web_search import get_web_search_status
        
        return {
            "vector_search": get_vector_store_status(),
            "web_search": get_web_search_status()
        }
    except Exception as e:
        logger.error(f"Error getting tools status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting tools status: {str(e)}")
