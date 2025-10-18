"""
Live Query Router - Direct Supervisor Agent Integration

This router provides a SINGLE endpoint for Gemini Live to send raw queries
directly to the Supervisor Agent without pre-selecting tools.

The Supervisor Agent has FULL CONTROL over:
- Query analysis
- Agent selection (local_knowledge, web_search, or both)
- Multi-agent coordination
- Response synthesis
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

from rag_agent.config.orchestrator import rag_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag/live", tags=["RAG Live Query"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for direct queries to Supervisor Agent."""
    query: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for Supervisor Agent queries."""
    query: str
    response: str
    sources: List[Dict[str, Any]]
    confidence: float
    agents_used: List[str]
    reasoning: Optional[str] = None


# ============================================================================
# SUPERVISOR AGENT QUERY ENDPOINT
# ============================================================================

@router.post("/query", response_model=QueryResponse)
async def query_supervisor_agent(request: QueryRequest):
    """
    Send a raw query directly to the Supervisor Agent.
    
    This is the MAIN endpoint for Gemini Live integration.
    
    Flow:
    1. Gemini Live receives user input (voice/text/video)
    2. Gemini Live sends RAW query to this endpoint
    3. Supervisor Agent analyzes and decides which agents to use
    4. Supervisor can use one or multiple agents:
       - local_knowledge_agent (for company docs)
       - web_search_agent (for web info)
       - or BOTH for comprehensive answers
    5. Supervisor synthesizes final response
    6. Returns structured response to Gemini Live
    
    Args:
        request: QueryRequest with raw user query
        
    Returns:
        QueryResponse: Comprehensive answer with sources and metadata
    """
    try:
        logger.info("="*80)
        logger.info("🎯 NEW QUERY RECEIVED")
        logger.info(f"📝 Query: '{request.query}'")
        logger.info(f"👤 User ID: {request.user_id}")
        logger.info(f"🔗 Session ID: {request.session_id}")
        logger.info("="*80)
        
        # Initialize RAG system if not already done
        if not rag_system.supervisor_agent:
            logger.info("🔄 Initializing RAG multi-agent system...")
            rag_system.initialize(environment="production")
            logger.info("✅ RAG system initialized with:")
            logger.info(f"   - Supervisor Agent: {rag_system.supervisor_agent is not None}")
            logger.info(f"   - Specialist Agents: {list(rag_system.specialist_agents.keys())}")
        
        # Process through Supervisor Agent
        logger.info("🧠 SUPERVISOR AGENT: Starting analysis...")
        logger.info("   📊 Chain-of-Thought reasoning in progress...")
        
        result = rag_system.query(
            user_query=request.query,
            context=request.context or {}
        )
        
        # Extract agents used from sources
        agents_used = []
        if result.get("sources"):
            for source in result["sources"]:
                tool_name = source.get("tool", "")
                if "vector_search" in tool_name.lower():
                    if "local_knowledge_agent" not in agents_used:
                        agents_used.append("local_knowledge_agent")
                elif "web_search" in tool_name.lower():
                    if "web_search_agent" not in agents_used:
                        agents_used.append("web_search_agent")
        
        logger.info("✅ SUPERVISOR AGENT: Analysis complete!")
        logger.info(f"   🎯 Agents used: {agents_used or ['supervisor_direct']}")
        logger.info(f"   📚 Sources: {len(result.get('sources', []))} sources")
        logger.info(f"   📊 Confidence: {result.get('confidence', 0):.2f}")
        logger.info("="*80)
        
        return QueryResponse(
            query=result["query"],
            response=result["response"],
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.8),
            agents_used=agents_used or ["supervisor"],
            reasoning=f"Supervisor analyzed query and delegated to: {', '.join(agents_used) if agents_used else 'direct response'}"
        )
        
    except Exception as e:
        logger.error("="*80)
        logger.error(f"❌ ERROR in Supervisor Agent query processing")
        logger.error(f"   Error: {str(e)}")
        logger.error("="*80)
        import traceback
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500, 
            detail=f"Supervisor Agent error: {str(e)}"
        )


@router.post("/query/simple")
async def simple_query(query: str):
    """
    Simplified query endpoint for quick testing.
    
    Args:
        query: Raw query string
        
    Returns:
        Dict: Simple response
    """
    try:
        result = await query_supervisor_agent(QueryRequest(query=query))
        return {
            "query": query,
            "response": result.response,
            "agents_used": result.agents_used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supervisor/status")
async def get_supervisor_status():
    """
    Get status of the Supervisor Agent and multi-agent system.
    
    Returns:
        Dict: Status information
    """
    try:
        is_initialized = rag_system.supervisor_agent is not None
        
        return {
            "status": "operational" if is_initialized else "not_initialized",
            "supervisor_agent": {
                "initialized": is_initialized,
                "type": str(type(rag_system.supervisor_agent)) if is_initialized else None
            },
            "specialist_agents": {
                "available": list(rag_system.specialist_agents.keys()) if is_initialized else [],
                "count": len(rag_system.specialist_agents) if is_initialized else 0
            },
            "configuration": {
                "environment": "production",
                "max_iterations": rag_system.config.max_agent_iterations,
                "parallel_agents": rag_system.config.enable_parallel_agents
            },
            "tools": {
                "available": rag_system.config.get_available_tools(),
                "enabled": True
            }
        }
    except Exception as e:
        logger.error(f"Error getting supervisor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervisor/initialize")
async def initialize_supervisor(environment: str = "production"):
    """
    Manually initialize the Supervisor Agent and multi-agent system.
    
    Args:
        environment: Environment to initialize for (development, production, testing)
        
    Returns:
        Dict: Initialization status
    """
    try:
        logger.info(f"🔄 Manually initializing RAG system for environment: {environment}")
        rag_system.initialize(environment=environment)
        
        return {
            "status": "initialized",
            "environment": environment,
            "supervisor_agent": rag_system.supervisor_agent is not None,
            "specialist_agents": list(rag_system.specialist_agents.keys()),
            "message": "Multi-agent RAG system initialized successfully"
        }
    except Exception as e:
        logger.error(f"Error initializing supervisor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

