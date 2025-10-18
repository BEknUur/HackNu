"""
Vector search tool for querying local knowledge base.
"""

from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from config.settings import settings
import os


class VectorSearchManager:
    """Manages the vector store for local knowledge search."""
    
    _instance = None
    _vector_store = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorSearchManager, cls).__new__(cls)
        return cls._instance
    
    def initialize(self):
        """Initialize or load the vector store."""
        if self._vector_store is not None:
            return self._vector_store
        
        try:
            # Initialize embeddings
            embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.embedding_model,
                google_api_key=settings.google_api_key
            )
            
            # Try to load existing vector store
            vector_store_path = settings.vector_store_path
            if os.path.exists(vector_store_path) and os.path.exists(f"{vector_store_path}/index.faiss"):
                print(f"Loading existing vector store from {vector_store_path}")
                self._vector_store = FAISS.load_local(
                    vector_store_path,
                    embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                # Create a new empty vector store
                print("Creating new vector store (empty)")
                self._vector_store = FAISS.from_documents(
                    [Document(page_content="Welcome to the knowledge base. Add documents to get started.")],
                    embeddings
                )
                # Save it
                os.makedirs(vector_store_path, exist_ok=True)
                self._vector_store.save_local(vector_store_path)
            
            return self._vector_store
            
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            # Create minimal fallback
            embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.embedding_model,
                google_api_key=settings.google_api_key
            )
            self._vector_store = FAISS.from_documents(
                [Document(page_content="Vector store initialization failed. Please add documents.")],
                embeddings
            )
            return self._vector_store
    
    def get_vector_store(self):
        """Get the vector store, initializing if needed."""
        if self._vector_store is None:
            self.initialize()
        return self._vector_store


# Global vector search manager
vector_search_manager = VectorSearchManager()


@tool
def search_local_knowledge(query: str, top_k: int = 3) -> str:
    """
    Search the local knowledge base using semantic similarity.
    
    Use this tool to find information from internal documents, company policies,
    procedures, or any content that has been indexed in the local knowledge base.
    
    Args:
        query: The search query
        top_k: Number of results to return (default: 3)
        
    Returns:
        Formatted string with search results including content and sources
    """
    try:
        vector_store = vector_search_manager.get_vector_store()
        
        # Perform similarity search
        results = vector_store.similarity_search(query, k=top_k)
        
        if not results:
            return "No relevant information found in the local knowledge base."
        
        # Format results
        formatted_results = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'unknown')
            formatted_results.append(
                f"--- Result {i} ---\n"
                f"Content: {doc.page_content}\n"
                f"Source: {source}\n"
            )
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching local knowledge base: {str(e)}"


@tool
def add_documents_to_knowledge_base(documents: list[str], sources: list[str] = None) -> str:
    """
    Add new documents to the local knowledge base.
    
    Args:
        documents: List of document texts to add
        sources: Optional list of source identifiers for the documents
        
    Returns:
        Confirmation message
    """
    try:
        vector_store = vector_search_manager.get_vector_store()
        
        # Create Document objects
        docs = []
        for i, doc_text in enumerate(documents):
            source = sources[i] if sources and i < len(sources) else f"document_{i}"
            docs.append(Document(
                page_content=doc_text,
                metadata={"source": source}
            ))
        
        # Add to vector store
        vector_store.add_documents(docs)
        
        # Save the updated vector store
        vector_store.save_local(settings.vector_store_path)
        
        return f"Successfully added {len(documents)} document(s) to the knowledge base."
        
    except Exception as e:
        return f"Error adding documents to knowledge base: {str(e)}"
