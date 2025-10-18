"""
Vector Store Management Module

This module handles the creation and management of the FAISS vector store
for document embeddings using Google's embedding model.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages the FAISS vector store for document embeddings."""
    
    def __init__(self, 
                 documents_path: str = "documents",
                 vector_store_path: str = "data/vector_store",
                 embedding_model: str = "models/embedding-001",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the VectorStoreManager.
        
        Args:
            documents_path: Path to documents directory
            vector_store_path: Path to store the FAISS index
            embedding_model: Google embedding model to use
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
        """
        self.documents_path = Path(documents_path)
        self.vector_store_path = Path(vector_store_path)
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create directories if they don't exist
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.embeddings = None
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def initialize_embeddings(self, google_api_key: Optional[str] = None) -> bool:
        """
        Initialize the Google embeddings model.
        
        Args:
            google_api_key: Google API key (if not provided, uses environment variable)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GOOGLE_API_KEY not found in environment variables")
                return False
            
            logger.info(f"Initializing embedding model: {self.embedding_model}")
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=self.embedding_model,
                google_api_key=api_key
            )
            logger.info("Embedding model initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            logger.error("Please ensure your GOOGLE_API_KEY is set correctly in the .env file.")
            return False
    
    def load_documents(self) -> List[Document]:
        """
        Load all documents from the documents directory.
        
        Returns:
            List[Document]: List of loaded documents
        """
        documents = []
        
        if not self.documents_path.exists():
            logger.error(f"Documents path does not exist: {self.documents_path}")
            return documents
        
        # Load all .txt files from the documents directory
        for file_path in self.documents_path.glob("*.txt"):
            try:
                logger.info(f"Loading document: {file_path.name}")
                loader = TextLoader(str(file_path), encoding='utf-8')
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Successfully loaded {len(docs)} pages from {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading document {file_path.name}: {e}")
        
        logger.info(f"Total documents loaded: {len(documents)}")
        return documents
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Process documents by splitting them into chunks.
        
        Args:
            documents: List of documents to process
            
        Returns:
            List[Document]: List of processed document chunks
        """
        if not documents:
            logger.warning("No documents to process")
            return []
        
        logger.info("Processing documents into chunks...")
        try:
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} document chunks")
            
            # Add metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            return []
    
    def create_vector_store(self, documents: List[Document]) -> bool:
        """
        Create FAISS vector store from documents.
        
        Args:
            documents: List of document chunks
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.embeddings:
            logger.error("Embeddings not initialized. Call initialize_embeddings() first.")
            return False
        
        if not documents:
            logger.error("No documents provided for vector store creation")
            return False
        
        try:
            logger.info("Creating FAISS vector store... This may take a few moments.")
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            logger.info("FAISS vector store created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating FAISS vector store: {e}")
            return False
    
    def save_vector_store(self) -> bool:
        """
        Save the vector store to disk.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.vector_store:
            logger.error("No vector store to save")
            return False
        
        try:
            logger.info(f"Saving vector store to: {self.vector_store_path}")
            self.vector_store.save_local(str(self.vector_store_path))
            logger.info("Vector store saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            return False
    
    def load_vector_store(self) -> bool:
        """
        Load the vector store from disk.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.embeddings:
            logger.error("Embeddings not initialized. Call initialize_embeddings() first.")
            return False
        
        try:
            vector_store_file = self.vector_store_path / "index.faiss"
            if not vector_store_file.exists():
                logger.warning(f"Vector store not found at: {vector_store_file}")
                return False
            
            logger.info(f"Loading vector store from: {self.vector_store_path}")
            self.vector_store = FAISS.load_local(
                str(self.vector_store_path), 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("Vector store loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False
    
    def search_documents(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List[Dict]: List of search results with metadata
        """
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return []
        
        try:
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_vector_store_info(self) -> Dict[str, Any]:
        """
        Get information about the vector store.
        
        Returns:
            Dict: Information about the vector store
        """
        if not self.vector_store:
            return {"status": "not_initialized"}
        
        try:
            # Get embedding dimension
            embedding_dim = "unknown"
            try:
                test_embedding = self.embeddings.embed_query("test")
                embedding_dim = len(test_embedding)
            except Exception:
                pass
            
            return {
                "status": "initialized",
                "index_type": type(self.vector_store).__name__,
                "embedding_dimension": embedding_dim,
                "total_vectors": self.vector_store.index.ntotal if hasattr(self.vector_store, 'index') else "unknown"
            }
        except Exception as e:
            logger.error(f"Error getting vector store info: {e}")
            return {"status": "error", "error": str(e)}
    
    def initialize_full_pipeline(self, google_api_key: Optional[str] = None) -> bool:
        """
        Initialize the complete pipeline: embeddings, load documents, process, create vector store, and save.
        
        Args:
            google_api_key: Google API key (if not provided, uses environment variable)
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Starting full vector store initialization pipeline...")
        
        # Step 1: Initialize embeddings
        if not self.initialize_embeddings(google_api_key):
            return False
        
        # Step 2: Load documents
        documents = self.load_documents()
        if not documents:
            logger.error("No documents loaded")
            return False
        
        # Step 3: Process documents
        processed_docs = self.process_documents(documents)
        if not processed_docs:
            logger.error("No documents processed")
            return False
        
        # Step 4: Create vector store
        if not self.create_vector_store(processed_docs):
            return False
        
        # Step 5: Save vector store
        if not self.save_vector_store():
            return False
        
        logger.info("Vector store initialization pipeline completed successfully!")
        return True


def create_vector_store_from_documents(
    documents_path: str = "documents",
    vector_store_path: str = "data/vector_store",
    google_api_key: Optional[str] = None
) -> bool:
    """
    Convenience function to create vector store from documents.
    
    Args:
        documents_path: Path to documents directory
        vector_store_path: Path to store the FAISS index
        google_api_key: Google API key
        
    Returns:
        bool: True if successful, False otherwise
    """
    manager = VectorStoreManager(
        documents_path=documents_path,
        vector_store_path=vector_store_path
    )
    
    return manager.initialize_full_pipeline(google_api_key)


if __name__ == "__main__":
    # Example usage
    success = create_vector_store_from_documents()
    if success:
        print("Vector store created successfully!")
    else:
        print("Failed to create vector store.")
