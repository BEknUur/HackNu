import os
import logging
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import sys
from pathlib import Path

# Add the backend directory to path
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from rag_agent.utils.vector_store import VectorStoreManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorSearchTool:
    """Vector search tool for the RAG system."""
    
    def __init__(self, 
                 vector_store_path: str = "data/vector_store",
                 embedding_model: str = "models/embedding-001",
                 google_api_key: Optional[str] = None):
        """
        Initialize the vector search tool.
        
        Args:
            vector_store_path: Path to the FAISS vector store
            embedding_model: Google embedding model to use
            google_api_key: Google API key
        """
        self.vector_store_path = vector_store_path
        self.embedding_model = embedding_model
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. "
                "Please set a valid Google API key to use vector search. "
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
        
        self.vector_store_manager = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the vector store manager."""
        try:
            self.vector_store_manager = VectorStoreManager(
                vector_store_path=self.vector_store_path,
                embedding_model=self.embedding_model
            )
            
            # Initialize embeddings
            if not self.vector_store_manager.initialize_embeddings(self.google_api_key):
                raise RuntimeError("Failed to initialize embeddings. Please check your GOOGLE_API_KEY.")
            
            # Try to load existing vector store
            if not self.vector_store_manager.load_vector_store():
                logger.warning("No existing vector store found. You may need to run the initialization script first.")
                logger.warning("Run: python backend/rag_agent/scripts/initialize_vector_db.py")
                
        except Exception as e:
            logger.error(f"Error initializing vector search tool: {e}")
            raise RuntimeError(f"Failed to initialize vector search: {e}")
    
    def search(self, query: str, k: int = 3) -> str:
        """
        Search for relevant documents using vector similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            str: Formatted search results
        """
        if not self.vector_store_manager or not self.vector_store_manager.vector_store:
            raise RuntimeError(
                "Vector store not available. Please ensure the vector database is initialized. "
                "Run: python backend/rag_agent/scripts/initialize_vector_db.py"
            )
        
        try:
            # Perform vector search
            results = self.vector_store_manager.search_documents(query, k=k)
            
            if not results:
                return f"No relevant documents found for query: '{query}'"
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                content = result['content']
                metadata = result['metadata']
                score = result['similarity_score']
                
                # Extract source information
                source = metadata.get('source', 'Unknown')
                if isinstance(source, str):
                    # Extract filename from path
                    filename = source.split('/')[-1] if '/' in source else source
                else:
                    filename = 'Unknown'
                
                formatted_results.append(
                    f"Result {i} (Similarity: {score:.3f}):\n"
                    f"Source: {filename}\n"
                    f"Content: {content[:200]}{'...' if len(content) > 200 else ''}\n"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error performing vector search: {e}")
            return f"Error searching documents: {str(e)}"
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get information about the vector store."""
        if not self.vector_store_manager:
            return {"status": "not_initialized"}
        
        return self.vector_store_manager.get_vector_store_info()


# Global vector search tool instance
_vector_search_tool_instance = None


def get_vector_search_tool() -> VectorSearchTool:
    """Get the global vector search tool instance."""
    global _vector_search_tool_instance
    if _vector_search_tool_instance is None:
        _vector_search_tool_instance = VectorSearchTool()
    return _vector_search_tool_instance


@tool
def vector_search_tool(query: str) -> str:
    """
    Search through local knowledge base using vector similarity.
    
    This tool searches through company documents, policies, and procedures
    to find relevant information based on semantic similarity.
    
    Args:
        query: The search query to find relevant documents
        
    Returns:
        str: Formatted search results with sources and similarity scores
    """
    tool_instance = get_vector_search_tool()
    return tool_instance.search(query)


@tool
def vector_search_with_metadata(query: str, k: int = 3) -> Dict[str, Any]:
    """
    Search through local knowledge base and return detailed metadata.
    
    Args:
        query: The search query to find relevant documents
        k: Number of results to return
        
    Returns:
        Dict: Detailed search results with metadata
    """
    tool_instance = get_vector_search_tool()
    
    if not tool_instance.vector_store_manager or not tool_instance.vector_store_manager.vector_store:
        return {
            "error": "Vector store not available",
            "results": [],
            "total_results": 0
        }
    
    try:
        results = tool_instance.vector_store_manager.search_documents(query, k=k)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in vector search with metadata: {e}")
        return {
            "error": str(e),
            "results": [],
            "total_results": 0
        }


def get_vector_store_status() -> Dict[str, Any]:
    """
    Get the current status of the vector store.
    
    Returns:
        Dict: Status information about the vector store
    """
    try:
        tool_instance = get_vector_search_tool()
        info = tool_instance.get_store_info()
        
        if info.get("status") == "not_initialized":
            return {
                "status": "error",
                "message": "Vector store is not initialized. Please run the initialization script first.",
                "available": False
            }
        
        if info.get("status") == "error":
            return {
                "status": "error",
                "message": info.get('error', 'Unknown error'),
                "available": False
            }
        
        return {
            "status": "ready",
            "message": "Vector store is ready",
            "available": True,
            "details": {
                "index_type": info.get('index_type', 'unknown'),
                "embedding_dimension": info.get('embedding_dimension', 'unknown'),
                "total_vectors": info.get('total_vectors', 'unknown')
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "available": False
        }


def initialize_vector_store(documents_path: str = "documents",
                           vector_store_path: str = "data/vector_store",
                           google_api_key: Optional[str] = None) -> bool:
    """
    Initialize the vector store from documents.
    
    Args:
        documents_path: Path to documents directory
        vector_store_path: Path to store the FAISS index
        google_api_key: Google API key
        
    Returns:
        bool: True if successful, False otherwise
    """
    from rag_agent.utils.vector_store import create_vector_store_from_documents
    
    try:
        success = create_vector_store_from_documents(
            documents_path=documents_path,
            vector_store_path=vector_store_path,
            google_api_key=google_api_key
        )
        
        if success:
            # Reinitialize the tool instance to use the new vector store
            global _vector_search_tool_instance
            _vector_search_tool_instance = VectorSearchTool(
                vector_store_path=vector_store_path,
                google_api_key=google_api_key
            )
            logger.info("Vector store initialized successfully")
        else:
            logger.error("Failed to initialize vector store")
        
        return success
        
    except Exception as e:
        logger.error(f"Error initializing vector store: {e}")
        return False


# Export the main search function for easy access
def search_documents(query: str, k: int = 3) -> str:
    """
    Convenience function to search documents.
    
    Args:
        query: Search query
        k: Number of results
        
    Returns:
        str: Search results
    """
    return vector_search_tool.invoke({"query": query})


if __name__ == "__main__":
    # Example usage and testing
    print("Testing vector search tool...")
    
    # Check if vector store exists
    status = get_vector_store_status()
    print(f"Vector store status: {status}")
    
    # If not initialized, initialize it
    if "not initialized" in status.lower():
        print("Initializing vector store...")
        success = initialize_vector_store()
        if success:
            print("Vector store initialized successfully!")
        else:
            print("Failed to initialize vector store")
            exit(1)
    
    # Test search with generic query
    test_query = "company policies"
    print(f"\nSearching for: '{test_query}'")
    results = vector_search_tool.invoke({"query": test_query})
    print(f"Results:\n{results}")
