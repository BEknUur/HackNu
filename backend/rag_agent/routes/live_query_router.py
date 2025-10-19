"""
Gemini Live API Router for RAG Tools

This router provides endpoints specifically designed for Gemini Live API integration.
It handles tool calls (vector_search, web_search) from the frontend live chat.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import sys
from pathlib import Path

# Add the backend directory to path
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from rag_agent.tools.vector_search import get_vector_search_tool, get_vector_store_status
from rag_agent.tools.web_search import get_web_search_tool, get_web_search_status
from rag_agent.config.orchestrator import rag_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag/live", tags=["RAG Live"])


class LiveQueryRequest(BaseModel):
    """Request model for live RAG queries from Gemini."""
    query: str = Field(..., description="The user's query to process")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context including tool_name")


class LiveQueryResponse(BaseModel):
    """Response model for live RAG queries."""
    response: str = Field(..., description="The response from the RAG tool")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Sources used for the response")
    confidence: float = Field(default=0.0, description="Confidence score of the response")
    agents_used: List[str] = Field(default_factory=list, description="List of agents/tools used")
    status: str = Field(default="success", description="Status of the query")


class SupervisorStatus(BaseModel):
    """Status model for the RAG supervisor."""
    status: str
    supervisor_agent: Dict[str, Any]
    specialist_agents: Dict[str, Any]
    configuration: Dict[str, Any]
    tools: Dict[str, Any]


@router.post("/query", response_model=LiveQueryResponse)
async def live_query(request: LiveQueryRequest):
    """
    Process a live query from Gemini Live API using the Supervisor Agent.
    
    This endpoint receives queries from Gemini Live and processes them through
    the full RAG system with Supervisor Agent orchestration - exactly like the
    regular RAG endpoint, ensuring consistent agent logic and decision-making.
    
    Args:
        request: Query request with query text and context
        
    Returns:
        LiveQueryResponse: Response from the Supervisor Agent
    """
    try:
        query = request.query
        logger.info(f"[Live Query] Processing query: {query}")
        
        # Initialize RAG system if needed
        if not rag_system.supervisor_agent:
            logger.info("[Live Query] Initializing RAG system")
            rag_system.initialize(environment="production")
        
        # Prepare context
        context = request.context or {}
        
        # Process query through Supervisor Agent (same as regular RAG)
        logger.info("[Live Query] Sending to Supervisor Agent")
        result = rag_system.query(
            user_query=query,
            context=context
        )
        
        # Extract agents used from sources
        agents_used = []
        for source in result.get("sources", []):
            if isinstance(source, dict) and "tool" in source:
                tool_name = source.get("tool", "")
                if tool_name and tool_name not in agents_used:
                    agents_used.append(tool_name)
        
        logger.info(f"[Live Query] Supervisor responded. Agents used: {agents_used}")
        
        return LiveQueryResponse(
            response=result["response"],
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.8),
            agents_used=agents_used,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"[Live Query] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing live query: {str(e)}"
        )


@router.get("/supervisor/status", response_model=SupervisorStatus)
async def get_supervisor_status():
    """
    Get the status of the RAG system supervisor and tools.
    
    This endpoint is used by the frontend to check if RAG tools are available
    and healthy for Gemini Live API integration.
    
    Returns:
        SupervisorStatus: Current status of the RAG system
    """
    try:
        # Check vector store status
        vector_status = get_vector_store_status()
        
        # Check web search status
        web_status = get_web_search_status()
        
        # Determine if tools are available
        tools_available = []
        if vector_status.get("available"):
            tools_available.append("vector_search")
        if web_status.get("available"):
            tools_available.append("web_search")
        
        # Determine overall status
        overall_status = "operational" if len(tools_available) > 0 else "error"
        
        return SupervisorStatus(
            status=overall_status,
            supervisor_agent={
                "initialized": len(tools_available) > 0,
                "type": "live_api_supervisor"
            },
            specialist_agents={
                "available": tools_available,
                "count": len(tools_available)
            },
            configuration={
                "environment": "live_chat",
                "max_iterations": 5,
                "parallel_agents": False
            },
            tools={
                "available": tools_available,
                "enabled": len(tools_available) > 0,
                "vector_search": vector_status,
                "web_search": web_status
            }
        )
        
    except Exception as e:
        logger.error(f"[Supervisor Status] Error: {e}", exc_info=True)
        # Return error status instead of raising exception
        return SupervisorStatus(
            status="error",
            supervisor_agent={
                "initialized": False,
                "type": None
            },
            specialist_agents={
                "available": [],
                "count": 0
            },
            configuration={
                "environment": "live_chat",
                "max_iterations": 5,
                "parallel_agents": False
            },
            tools={
                "available": [],
                "enabled": False,
                "error": str(e)
            }
        )


@router.post("/supervisor/initialize")
async def initialize_supervisor():
    """
    Initialize the RAG supervisor and tools.
    
    This endpoint can be called to ensure all RAG tools are properly initialized.
    
    Returns:
        Dict: Initialization status
    """
    try:
        # Try to initialize vector search tool
        vector_initialized = False
        web_initialized = False
        
        try:
            vector_tool = get_vector_search_tool()
            vector_status = get_vector_store_status()
            vector_initialized = vector_status.get("available", False)
        except Exception as e:
            logger.warning(f"[Initialize] Vector search initialization warning: {e}")
        
        try:
            web_tool = get_web_search_tool()
            web_status = get_web_search_status()
            web_initialized = web_status.get("available", False)
        except Exception as e:
            logger.warning(f"[Initialize] Web search initialization warning: {e}")
        
        tools_initialized = []
        if vector_initialized:
            tools_initialized.append("vector_search")
        if web_initialized:
            tools_initialized.append("web_search")
        
        return {
            "status": "initialized" if len(tools_initialized) > 0 else "partial",
            "tools_initialized": tools_initialized,
            "vector_search": {
                "initialized": vector_initialized,
                "status": "ready" if vector_initialized else "error"
            },
            "web_search": {
                "initialized": web_initialized,
                "status": "ready" if web_initialized else "error"
            },
            "message": f"Initialized {len(tools_initialized)} tool(s): {', '.join(tools_initialized)}"
        }
        
    except Exception as e:
        logger.error(f"[Initialize] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error initializing supervisor: {str(e)}"
        )


@router.get("/tools/status")
async def get_tools_status():
    """
    Get detailed status of all available tools.
    
    Returns:
        Dict: Detailed status of each tool
    """
    try:
        vector_status = get_vector_store_status()
        web_status = get_web_search_status()
        
        return {
            "status": "operational",
            "tools": {
                "vector_search": {
                    "available": vector_status.get("available", False),
                    "status": vector_status.get("status", "unknown"),
                    "message": vector_status.get("message", ""),
                    "details": vector_status.get("details", {})
                },
                "web_search": {
                    "available": web_status.get("available", False),
                    "status": web_status.get("status", "unknown"),
                    "message": web_status.get("message", "")
                }
            }
        }
        
    except Exception as e:
        logger.error(f"[Tools Status] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tools status: {str(e)}"
        )


@router.post("/test/vector_search")
async def test_vector_search(query: str = "company policy"):
    """
    Test endpoint for vector search.
    
    Args:
        query: Test query
        
    Returns:
        Dict: Test results
    """
    try:
        vector_tool = get_vector_search_tool()
        result = vector_tool.search(query=query, k=2)
        
        return {
            "status": "success",
            "tool": "vector_search",
            "query": query,
            "result": result
        }
    except Exception as e:
        logger.error(f"[Test Vector Search] Error: {e}")
        return {
            "status": "error",
            "tool": "vector_search",
            "query": query,
            "error": str(e)
        }


@router.post("/test/web_search")
async def test_web_search(query: str = "current news"):
    """
    Test endpoint for web search.
    
    Args:
        query: Test query
        
    Returns:
        Dict: Test results
    """
    try:
        web_tool = get_web_search_tool()
        result = web_tool.search(query=query, max_results=2)
        
        return {
            "status": "success",
            "tool": "web_search",
            "query": query,
            "result": result
        }
    except Exception as e:
        logger.error(f"[Test Web Search] Error: {e}")
        return {
            "status": "error",
            "tool": "web_search",
            "query": query,
            "error": str(e)
        }
