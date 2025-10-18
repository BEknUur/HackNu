"""
API routes for the Agentic RAG system.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from sse_starlette.sse import EventSourceResponse
from models.requests import QueryRequest
from models.responses import QueryResponse, AgentResult, HealthResponse
from graph.agent_graph import get_agent_graph
from langchain_core.messages import HumanMessage
from config.settings import settings
import uuid
import time
import json
from datetime import datetime
from typing import Optional
import asyncio


router = APIRouter(prefix=settings.api_v1_prefix, tags=["Agentic RAG"])

# Initialize checkpointer on module load
_checkpointer_initialized = False

async def ensure_checkpointer_initialized():
    """Ensure checkpointer tables are initialized (PostgreSQL only)."""
    global _checkpointer_initialized
    if not _checkpointer_initialized:
        # For SQLite, the checkpointer is automatically initialized
        # when the graph is created, so no additional initialization needed
        _checkpointer_initialized = True


@router.post("/query", response_model=QueryResponse)
async def query_agents(request: QueryRequest):
    """
    Submit a query to the multi-agent RAG system.
    
    The supervisor will analyze the query and delegate to appropriate
    specialized agents (local knowledge, web search, cloud).
    
    Args:
        request: Query request with user question and options
        
    Returns:
        Comprehensive response with final answer and agent details
    """
    start_time = time.time()
    
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get the agent graph
        agent_graph = get_agent_graph()
        
        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content=request.query)]
        }
        
        # Configure graph execution
        config = {
            "configurable": {
                "thread_id": session_id
            },
            "recursion_limit": request.max_iterations + 10  # Allow for agent loops
        }
        
        print(f"Processing query: {request.query[:100]}...")
        
        # Invoke the graph
        result = await agent_graph.ainvoke(initial_state, config)
        
        # Extract messages from result
        messages = result.get("messages", [])
        
        # Get final answer - look for last AI message with actual content
        final_answer = "No response generated"
        reasoning_plan = None
        
        # Extract information from all messages
        agents_used = []
        agent_results = []
        
        for msg in messages:
            # Track tool calls (these represent agent delegations)
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get('name', '')
                    if tool_name and tool_name not in agents_used:
                        agents_used.append(tool_name)
            
            # Track agent responses
            if hasattr(msg, 'name') and msg.name:
                agent_name = msg.name
                
                # Skip supervisor for agent list but capture reasoning
                if agent_name == "supervisor":
                    if hasattr(msg, 'content') and msg.content:
                        # Check if this has reasoning indicators
                        content = str(msg.content)
                        if any(keyword in content for keyword in ["ANALYZE", "PLAN", "DELEGATE", "SYNTHESIZE"]):
                            reasoning_plan = content
                    continue
                
                # Record unique agent usage
                if agent_name not in agents_used:
                    agents_used.append(agent_name)
                    
                # Get agent result
                if hasattr(msg, 'content') and msg.content and hasattr(msg, 'type') and msg.type == "ai":
                    agent_results.append(
                            AgentResult(
                                agent_name=agent_name,
                                result=msg.content[:500] + "..." if len(msg.content) > 500 else msg.content,
                                execution_time_ms=None  # Could be calculated with timestamps
                            )
                        )
        
        # Extract final answer - get the last substantial AI message
        # This could be from supervisor after synthesis or from an agent
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content:
                content = str(msg.content).strip()
                # Skip empty messages and tool messages
                if content and hasattr(msg, 'type') and msg.type == "ai":
                    # Skip messages that are just tool calls without content
                    if not (hasattr(msg, 'tool_calls') and msg.tool_calls and not content):
                        final_answer = content
                        break
        
        # If still no answer, try to get from agent results
        if final_answer == "No response generated" and agent_results:
            # Use the last agent's result as the answer
            final_answer = agent_results[-1].result
        
        # Calculate total time
        total_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response = QueryResponse(
            query=request.query,
            final_answer=final_answer,
            agents_used=agents_used,
            agent_results=agent_results,
            session_id=session_id,
            reasoning_plan=reasoning_plan,
            total_time_ms=total_time_ms,
            timestamp=datetime.now()
        )
        
        print(f"Query processed in {total_time_ms}ms using agents: {agents_used}")
        
        return response
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/chat/stream")
async def stream_chat(query: str, session_id: Optional[str] = None, max_iterations: int = 10):
    """
    Stream chat responses using Server-Sent Events (SSE).
    
    This endpoint enables real-time streaming of agent responses,
    providing a ChatGPT-like conversational experience.
    
    Args:
        query: User question
        session_id: Thread ID for conversation persistence
        max_iterations: Maximum iterations for agent loops
        
    Returns:
        SSE stream of agent responses and updates
    """
    try:
        # Ensure checkpointer is initialized (for PostgreSQL)
        await ensure_checkpointer_initialized()
        
        # Generate thread ID if not provided
        thread_id = session_id or str(uuid.uuid4())
        
        # Get the agent graph
        agent_graph = get_agent_graph()
        
        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content=query)]
        }
        
        # Configure graph execution with thread_id for persistence
        config = {
            "configurable": {
                "thread_id": thread_id
            },
            "recursion_limit": max_iterations + 10
        }
        
        async def event_generator():
            """Generate SSE events from graph stream."""
            try:
                # Send thread_id first
                yield {
                    "event": "thread_id",
                    "data": json.dumps({"thread_id": thread_id})
                }
                
                # Send start event
                yield {
                    "event": "start",
                    "data": json.dumps({"query": query, "timestamp": datetime.now().isoformat()})
                }
                
                print(f"\n🚀 Starting graph stream for query: {query[:100]}")
                
                # Stream graph updates
                chunk_count = 0
                async for chunk in agent_graph.astream(initial_state, config, stream_mode="values"):
                    chunk_count += 1
                    print(f"📦 Chunk {chunk_count}: {type(chunk)}")
                    
                    messages = chunk.get("messages", [])
                    print(f"   Messages count: {len(messages)}")
                    
                    if messages:
                        last_message = messages[-1]
                        print(f"   Last message type: {getattr(last_message, 'type', 'unknown')}")
                        print(f"   Last message name: {getattr(last_message, 'name', None)}")
                        print(f"   Content length: {len(str(getattr(last_message, 'content', '')))}")
                        
                        # Normalize message type for frontend compatibility
                        msg_type = getattr(last_message, "type", "unknown")
                        if "ai" in msg_type.lower():
                            msg_type = "ai"
                        elif "human" in msg_type.lower():
                            msg_type = "human"
                        elif "tool" in msg_type.lower():
                            msg_type = "tool"
                        
                        # Extract message info
                        msg_data = {
                            "type": msg_type,  # Normalized type
                            "content": getattr(last_message, "content", ""),
                            "name": getattr(last_message, "name", None),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Check for tool calls (agent delegation)
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            msg_data["tool_calls"] = [
                                {
                                    "name": tc.get('name', ''),
                                    "args": tc.get('args', {})
                                }
                                for tc in last_message.tool_calls
                            ]
                            print(f"   🤖 Tool calls: {[tc['name'] for tc in msg_data['tool_calls']]}")
                        
                        print(f"   ✅ Yielding message event")
                        yield {
                            "event": "message",
                            "data": json.dumps(msg_data)
                        }
                
                print(f"✨ Stream complete! Total chunks: {chunk_count}")
                
                # Send completion event
                yield {
                    "event": "done",
                    "data": json.dumps({"status": "completed", "thread_id": thread_id})
                }
                
            except Exception as e:
                print(f"❌ Error in stream generator: {str(e)}")
                import traceback
                traceback.print_exc()
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }
        
        return EventSourceResponse(event_generator())
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error streaming chat: {str(e)}"
        )


@router.post("/threads/create")
async def create_thread():
    """
    Create a new conversation thread.
    
    Returns:
        New thread ID and metadata
    """
    thread_id = str(uuid.uuid4())
    return {
        "thread_id": thread_id,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    """
    Get all messages in a conversation thread.
    
    Args:
        thread_id: The thread/conversation ID
        
    Returns:
        List of messages in the thread
    """
    try:
        agent_graph = get_agent_graph()
        
        # Get state for this thread
        config = {"configurable": {"thread_id": thread_id}}
        state = agent_graph.get_state(config)
        
        if not state or not state.values:
            return {
                "thread_id": thread_id,
                "messages": [],
                "message_count": 0
            }
        
        messages = state.values.get("messages", [])
        
        # Format messages for response
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "type": getattr(msg, "type", "unknown"),
                "content": getattr(msg, "content", ""),
                "name": getattr(msg, "name", None),
                "role": "user" if getattr(msg, "type", "") == "human" else "assistant"
            })
        
        return {
            "thread_id": thread_id,
            "messages": formatted_messages,
            "message_count": len(formatted_messages)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving thread messages: {str(e)}"
        )


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """
    Delete a conversation thread.
    
    Note: With SqliteSaver, threads are stored in the database.
    This endpoint would need additional implementation to actually
    remove thread data from the checkpointer.
    
    Args:
        thread_id: The thread/conversation ID to delete
        
    Returns:
        Deletion confirmation
    """
    # Note: SqliteSaver doesn't have a built-in delete method
    # For now, we just return success. In production, you'd need to
    # implement actual deletion from the database
    return {
        "thread_id": thread_id,
        "status": "deleted",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status and available agents
    """
    try:
        # Try to get the graph to verify initialization
        graph = get_agent_graph()
        
        return HealthResponse(
            status="healthy",
            service="Agentic RAG Multi-Agent System",
            version="1.0.0",
            agents_available=[
                "supervisor",
                "local_knowledge_agent",
                "web_search_agent",
                "cloud_agent"
            ]
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            service="Agentic RAG Multi-Agent System",
            version="1.0.0",
            agents_available=[]
        )


@router.get("/graph/visualization")
async def get_graph_visualization():
    """
    Get a visual representation of the agent graph.
    
    Returns:
        PNG image of the graph structure
    """
    try:
        from graph.agent_graph import graph_manager
        
        png_bytes = graph_manager.visualize()
        
        if png_bytes:
            return Response(content=png_bytes, media_type="image/png")
        else:
            raise HTTPException(
                status_code=500,
                detail="Could not generate graph visualization"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating visualization: {str(e)}"
        )


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Agentic RAG Multi-Agent System",
        "version": "1.0.0",
        "endpoints": {
            "query": f"{settings.api_v1_prefix}/query",
            "health": f"{settings.api_v1_prefix}/health",
            "visualization": f"{settings.api_v1_prefix}/graph/visualization",
            "docs": "/docs"
        },
        "agents": [
            "local_knowledge_agent",
            "web_search_agent",
            "cloud_agent"
        ]
    }
