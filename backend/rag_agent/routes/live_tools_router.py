"""
Live Tools Router for Gemini Live Integration

This router provides endpoints for Gemini Live to call RAG tools
(vector_search and web_search) as function calls.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import sys
from pathlib import Path

# Add the backend directory to path
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from rag_agent.tools.vector_search import vector_search_tool
from rag_agent.tools.web_search import web_search_tool
from rag_agent.config.orchestrator import rag_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag/live", tags=["RAG Live Tools"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ToolCallRequest(BaseModel):
    """Request model for tool calls from Gemini Live."""
    tool_name: str
    parameters: Dict[str, Any]


class ToolCallResponse(BaseModel):
    """Response model for tool calls."""
    tool_name: str
    result: str
    success: bool
    error: Optional[str] = None


class BatchToolCallRequest(BaseModel):
    """Request model for batch tool calls."""
    calls: List[ToolCallRequest]


class BatchToolCallResponse(BaseModel):
    """Response model for batch tool calls."""
    results: List[ToolCallResponse]


# ============================================================================
# FUNCTION SCHEMAS FOR GEMINI
# ============================================================================

def get_function_declarations():
    """
    Get Gemini-compatible function declarations for RAG tools.
    
    These will be registered with Gemini Live so it knows when to call our tools.
    """
    return [
        {
            "name": "vector_search",
            "description": "Search through local company knowledge base, internal documents, policies, and procedures using semantic search. Use this for questions about company information, internal policies, procedures, or any information stored in the company's knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information in the knowledge base. Be specific and include context."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 3, max: 10)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "web_search",
            "description": "Search the web for current information, recent news, online data, and public information. Use this for questions about current events, recent developments, public information, or anything not in the internal knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find information on the web. Be specific about what you're looking for."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    ]


# ============================================================================
# TOOL EXECUTION VIA SUPERVISOR AGENT
# ============================================================================

def execute_via_supervisor(user_query: str, tool_hint: Optional[str] = None) -> str:
    """
    Execute query through the supervisor agent.
    
    The supervisor will:
    1. Analyze the query
    2. Decide which specialist agent(s) to use
    3. Call the appropriate agents with tools
    4. Synthesize the results
    
    Args:
        user_query: The user's query
        tool_hint: Optional hint about which tool to prefer
        
    Returns:
        str: The supervisor's response with tool results
    """
    try:
        # Initialize the RAG system if not already done
        if not rag_system.supervisor_agent:
            logger.info("Initializing RAG system...")
            rag_system.initialize(environment="production")
            logger.info("RAG system initialized successfully")
        
        logger.info(f"🧠 Routing query to SUPERVISOR AGENT: '{user_query}'")
        if tool_hint:
            logger.info(f"   Tool hint: {tool_hint}")
        
        # Query through the supervisor agent
        result = rag_system.query(
            user_query=user_query,
            context={"tool_hint": tool_hint} if tool_hint else {}
        )
        
        logger.info(f"✅ Supervisor agent completed successfully")
        logger.info(f"   Response length: {len(result['response'])} chars")
        logger.info(f"   Sources used: {len(result.get('sources', []))}")
        
        return result['response']
        
    except Exception as e:
        logger.error(f"❌ Supervisor agent error: {e}", exc_info=True)
        raise


def execute_vector_search(query: str, top_k: int = 3) -> str:
    """
    Execute vector search via supervisor agent.
    
    Instead of directly calling the tool, this routes through the supervisor
    which will delegate to the local_knowledge_agent.
    """
    logger.info(f"📥 Vector search request received")
    logger.info(f"   Query: '{query}', top_k={top_k}")
    
    # Create a query that hints at using vector search
    user_query = f"Search the company knowledge base for: {query}"
    return execute_via_supervisor(user_query, tool_hint="vector_search")


def execute_web_search(query: str, max_results: int = 5) -> str:
    """
    Execute web search via supervisor agent.
    
    Instead of directly calling the tool, this routes through the supervisor
    which will delegate to the web_search_agent.
    """
    logger.info(f"🌐 Web search request received")
    logger.info(f"   Query: '{query}', max_results={max_results}")
    
    # Create a query that hints at using web search
    user_query = f"Search the web for current information about: {query}"
    return execute_via_supervisor(user_query, tool_hint="web_search")


TOOL_EXECUTORS = {
    "vector_search": execute_vector_search,
    "web_search": execute_web_search,
}


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/function-declarations")
async def get_function_declarations_endpoint():
    """
    Get function declarations for Gemini Live.
    
    Returns:
        Dict: Function declarations in Gemini-compatible format
    """
    try:
        return {
            "status": "success",
            "functions": get_function_declarations()
        }
    except Exception as e:
        logger.error(f"Error getting function declarations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tool-call", response_model=ToolCallResponse)
async def execute_tool_call(request: ToolCallRequest):
    """
    Execute a single tool call from Gemini Live.
    
    Args:
        request: Tool call request with tool name and parameters
        
    Returns:
        ToolCallResponse: Tool execution result
    """
    try:
        tool_name = request.tool_name
        parameters = request.parameters
        
        logger.info(f"Received tool call: {tool_name} with params: {parameters}")
        
        # Check if tool exists
        if tool_name not in TOOL_EXECUTORS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown tool: {tool_name}. Available tools: {list(TOOL_EXECUTORS.keys())}"
            )
        
        # Execute tool
        executor = TOOL_EXECUTORS[tool_name]
        result = executor(**parameters)
        
        return ToolCallResponse(
            tool_name=tool_name,
            result=result,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool call: {e}")
        return ToolCallResponse(
            tool_name=request.tool_name,
            result="",
            success=False,
            error=str(e)
        )


@router.post("/batch-tool-calls", response_model=BatchToolCallResponse)
async def execute_batch_tool_calls(request: BatchToolCallRequest):
    """
    Execute multiple tool calls in batch.
    
    Args:
        request: Batch of tool calls
        
    Returns:
        BatchToolCallResponse: Results for all tool calls
    """
    results = []
    
    for call in request.calls:
        try:
            tool_name = call.tool_name
            parameters = call.parameters
            
            if tool_name not in TOOL_EXECUTORS:
                results.append(ToolCallResponse(
                    tool_name=tool_name,
                    result="",
                    success=False,
                    error=f"Unknown tool: {tool_name}"
                ))
                continue
            
            executor = TOOL_EXECUTORS[tool_name]
            result = executor(**parameters)
            
            results.append(ToolCallResponse(
                tool_name=tool_name,
                result=result,
                success=True
            ))
            
        except Exception as e:
            logger.error(f"Error in batch tool call {call.tool_name}: {e}")
            results.append(ToolCallResponse(
                tool_name=call.tool_name,
                result="",
                success=False,
                error=str(e)
            ))
    
    return BatchToolCallResponse(results=results)


@router.get("/health")
async def health_check():
    """
    Check health status of live tools.
    
    Returns:
        Dict: Health status of all tools
    """
    try:
        from rag_agent.tools.vector_search import get_vector_store_status
        from rag_agent.tools.web_search import get_web_search_status
        
        return {
            "status": "healthy",
            "tools": {
                "vector_search": get_vector_store_status(),
                "web_search": get_web_search_status()
            }
        }
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

