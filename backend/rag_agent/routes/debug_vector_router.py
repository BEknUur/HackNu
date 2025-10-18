"""
Debug Vector Search Router - For testing and debugging vector search
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from rag_agent.tools.vector_search import vector_search_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag/debug", tags=["RAG Debug"])


class VectorSearchDebugRequest(BaseModel):
    query: str
    top_k: int = 5


class VectorSearchDebugResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    status: str = "success"


@router.post("/vector-search", response_model=VectorSearchDebugResponse)
async def debug_vector_search(request: VectorSearchDebugRequest):
    """
    Debug endpoint to test vector search and see actual chunks returned with similarity scores.
    """
    try:
        logger.info(f"🔍 DEBUG: Vector search for: '{request.query}'")
        
        # Get vector store manager directly for detailed results
        from rag_agent.utils.vector_store import VectorStoreManager
        from rag_agent.config.langchain import langchain_config
        
        config = langchain_config
        manager = VectorStoreManager(
            documents_path=config.documents_path,
            vector_store_path=config.vector_store_path,
            embedding_model=config.embedding_model
        )
        
        # Initialize embeddings
        manager.initialize_embeddings(config.google_api_key)
        
        # Load vector store
        success = manager.load_vector_store()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to load vector store")
        
        # Search with detailed results
        results = manager.search_documents(request.query, k=request.top_k)
        
        logger.info(f"✅ DEBUG: Found {len(results)} results")
        
        # Format results with all details
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append({
                "rank": i,
                "content": result["content"],
                "source": result["metadata"].get("source", "unknown"),
                "similarity_score": result["similarity_score"],
                "chunk_id": result["metadata"].get("chunk_id", "unknown"),
                "total_chunks": result["metadata"].get("total_chunks", "unknown")
            })
        
        return VectorSearchDebugResponse(
            query=request.query,
            results=formatted_results,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"❌ DEBUG: Error in vector search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in vector search: {str(e)}")


@router.get("/vector-store-info")
async def get_vector_store_info():
    """
    Get information about the vector store.
    """
    try:
        from rag_agent.tools.vector_search import VectorSearchTool
        from rag_agent.config.langchain import langchain_config
        
        config = langchain_config
        tool = VectorSearchTool(
            vector_store_path=config.vector_store_path,
            google_api_key=config.google_api_key
        )
        
        # Check if vector store is loaded
        is_available = tool.vector_store is not None
        
        return {
            "status": "operational" if is_available else "not_loaded",
            "vector_store_path": config.vector_store_path,
            "is_available": is_available,
            "embedding_model": config.embedding_model
        }
        
    except Exception as e:
        logger.error(f"Error getting vector store info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

