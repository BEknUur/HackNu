"""
Vector Store Management Module

This module handles the creation and management of the FAISS vector store
for document embeddings using Google's embedding model.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import google.generativeai as genai
from rank_bm25 import BM25Okapi
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages the FAISS vector store for document embeddings."""
    
    def __init__(self, 
                 documents_path: str = "documents",
                 vector_store_path: str = "data/vector_store",
                 embedding_model: str = "models/embedding-001",
                 chunk_size: int = 400,
                 chunk_overlap: int = 100):
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
        self.reranker_llm = None
        self.bm25 = None
        self.bm25_docs = []  # Store documents for BM25
        self.all_chunks = []  # Store all chunks for hybrid search
        # Optimized text splitter for better PDF handling with semantic separators
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Multiple line breaks (sections)
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentences
                "! ",      # Exclamations
                "? ",      # Questions
                ";",       # Semi-colons
                ",",       # Commas
                " ",       # Words
                ""         # Characters
            ],
            keep_separator=True,  # Keep separators for better context
            add_start_index=True,  # Track position in document
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
            
            # Initialize reranker LLM
            try:
                genai.configure(api_key=api_key)
                # Try gemini-1.5-pro first, fallback if not available
                try:
                    self.reranker_llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-flash",
                        temperature=0.0,
                        google_api_key=api_key
                    )
                except:
                    # Fallback to gemini-pro
                    self.reranker_llm = ChatGoogleGenerativeAI(
                        model="models/gemini-pro",
                        temperature=0.0,
                        google_api_key=api_key
                    )
            except Exception as e:
                logger.warning(f"Could not initialize reranker: {e}. Reranking will be disabled.")
                self.reranker_llm = None
            
            logger.info("Embedding model and reranker initialized successfully")
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
        
        # Load all .pdf files from the documents directory with proper processing
        for file_path in self.documents_path.glob("*.pdf"):
            try:
                logger.info(f"Loading PDF document: {file_path.name}")
                loader = PyPDFLoader(str(file_path))
                docs = loader.load()
                
                # Proper PDF preprocessing - preserve structure
                for doc in docs:
                    content = doc.page_content
                    
                    # Clean PDF artifacts but PRESERVE structure
                    # Remove only excessive spaces within lines, keep paragraph breaks
                    lines = content.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        # Clean each line but keep it as a line
                        cleaned_line = ' '.join(line.split())
                        if cleaned_line:  # Only add non-empty lines
                            cleaned_lines.append(cleaned_line)
                    
                    # Rejoin with single newlines to preserve paragraphs
                    content = '\n'.join(cleaned_lines)
                    
                    # Add enhanced metadata for better retrieval
                    doc.metadata.update({
                        'document_type': 'pdf',
                        'filename': file_path.name,
                        'file_path': str(file_path),
                        'source': str(file_path),
                        'processed': True
                    })
                    
                    doc.page_content = content
                
                documents.extend(docs)
                logger.info(f"Successfully loaded and preprocessed {len(docs)} pages from {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading PDF document {file_path.name}: {e}")
        
        logger.info(f"Total documents loaded: {len(documents)}")
        return documents
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Process documents by splitting them into chunks with enhanced metadata.
        
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
            
            # Enhanced metadata for better retrieval
            for i, chunk in enumerate(chunks):
                # Get source information
                source = chunk.metadata.get('source', 'Unknown')
                filename = chunk.metadata.get('filename', 'Unknown')
                document_type = chunk.metadata.get('document_type', 'text')
                
                # Add enhanced metadata
                chunk.metadata.update({
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "chunk_index": i,
                    "source_file": filename,
                    "document_type": document_type,
                    "chunk_length": len(chunk.page_content),
                    "is_pdf": document_type == 'pdf',
                    "processed": True
                })
                
                # Add content preview for debugging
                chunk.metadata["content_preview"] = chunk.page_content[:100] + "..." if len(chunk.page_content) > 100 else chunk.page_content
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            return []
    
    def create_vector_store(self, documents: List[Document]) -> bool:
        """
        Create FAISS vector store and BM25 index from documents.
        
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
            # Create FAISS vector store
            logger.info("Creating FAISS vector store... This may take a few moments.")
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            logger.info("FAISS vector store created successfully")
            
            # Create BM25 index for hybrid search
            logger.info("Creating BM25 index for hybrid search...")
            self.all_chunks = documents
            self.bm25_docs = [doc.page_content for doc in documents]
            
            # Tokenize documents for BM25 (simple word-based tokenization)
            tokenized_docs = [doc.lower().split() for doc in self.bm25_docs]
            self.bm25 = BM25Okapi(tokenized_docs)
            logger.info(f"BM25 index created with {len(self.bm25_docs)} documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
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
    
    def _expand_query_with_hyde(self, query: str) -> str:
        """
        Expand query using HyDE (Hypothetical Document Embeddings).
        Generate a hypothetical answer to improve search quality.
        
        Args:
            query: Original query
            
        Returns:
            str: Expanded query with hypothetical answer
        """
        if not self.reranker_llm:
            return query
        
        try:
            hyde_prompt = f"""Given the following question, write a detailed, factual answer as if you were responding from a company knowledge base.
Keep it concise (2-3 sentences) and focused on facts.

Question: {query}

Answer:"""
            
            response = self.reranker_llm.invoke(hyde_prompt)
            hypothetical_answer = response.content.strip()
            
            # Combine original query with hypothetical answer
            expanded_query = f"{query} {hypothetical_answer}"
            logger.info(f"Query expanded with HyDE (original: {len(query)} chars, expanded: {len(expanded_query)} chars)")
            
            return expanded_query
            
        except Exception as e:
            logger.warning(f"HyDE expansion failed: {e}. Using original query.")
            return query
    
    def _bm25_search(self, query: str, k: int = 10) -> List[int]:
        """
        Perform BM25 search and return document indices.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List[int]: Indices of top documents
        """
        if not self.bm25:
            return []
        
        try:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25.get_scores(tokenized_query)
            
            # Get top k indices
            top_indices = np.argsort(bm25_scores)[::-1][:k]
            
            return top_indices.tolist()
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def _hybrid_search(self, query: str, k: int = 5, vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and BM25.
        
        Args:
            query: Search query
            k: Number of results to return
            vector_weight: Weight for vector search (0-1), BM25 gets (1-vector_weight)
            
        Returns:
            List[Dict]: Combined search results
        """
        if not self.vector_store or not self.bm25:
            logger.warning("Hybrid search not available. Falling back to vector search only.")
            return []
        
        try:
            # Get more candidates for combination
            fetch_k = k * 3
            
            # 1. Vector search
            vector_results = self.vector_store.similarity_search_with_score(query, k=fetch_k)
            
            # 2. BM25 search
            bm25_indices = self._bm25_search(query, k=fetch_k)
            
            # 3. Combine scores
            combined_scores = {}
            
            # Add vector search results (FAISS uses distance, lower is better)
            for doc, score in vector_results:
                doc_text = doc.page_content
                # Normalize vector score to 0-1 range (invert distance)
                normalized_vector_score = 1 / (1 + score)  # Convert distance to similarity
                
                if doc_text not in combined_scores:
                    combined_scores[doc_text] = {
                        'doc': doc,
                        'vector_score': normalized_vector_score,
                        'bm25_score': 0.0,
                        'raw_vector_score': score
                    }
                else:
                    combined_scores[doc_text]['vector_score'] = normalized_vector_score
                    combined_scores[doc_text]['raw_vector_score'] = score
            
            # Add BM25 results
            for idx in bm25_indices:
                if idx < len(self.all_chunks):
                    doc = self.all_chunks[idx]
                    doc_text = doc.page_content
                    
                    # Get BM25 score for this document
                    tokenized_query = query.lower().split()
                    bm25_score = self.bm25.get_scores(tokenized_query)[idx]
                    normalized_bm25_score = 1 / (1 + np.exp(-bm25_score / 10))  # Sigmoid normalization
                    
                    if doc_text not in combined_scores:
                        combined_scores[doc_text] = {
                            'doc': doc,
                            'vector_score': 0.0,
                            'bm25_score': normalized_bm25_score,
                            'raw_vector_score': 999.0  # High distance for missing docs
                        }
                    else:
                        combined_scores[doc_text]['bm25_score'] = normalized_bm25_score
            
            # 4. Calculate hybrid scores
            results = []
            for doc_text, scores in combined_scores.items():
                hybrid_score = (
                    vector_weight * scores['vector_score'] +
                    (1 - vector_weight) * scores['bm25_score']
                )
                
                results.append({
                    'content': doc_text,
                    'metadata': scores['doc'].metadata,
                    'similarity_score': scores['raw_vector_score'],
                    'bm25_score': scores['bm25_score'],
                    'vector_score': scores['vector_score'],
                    'hybrid_score': hybrid_score
                })
            
            # Sort by hybrid score (descending)
            results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            logger.info(f"Hybrid search completed. Combined {len(results)} results.")
            return results[:k * 2]  # Return more for reranking
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    def _rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank search results using Gemini for improved relevance.
        
        Args:
            query: Original search query
            results: List of search results to rerank
            top_k: Number of top results to return after reranking
            
        Returns:
            List[Dict]: Reranked results with relevance scores
        """
        if not self.reranker_llm or not results:
            return results[:top_k]
        
        try:
            # Prepare reranking prompt
            docs_text = "\n\n".join([
                f"Document {i+1}:\n{r['content'][:500]}..."  # Limit to 500 chars for efficiency
                for i, r in enumerate(results)
            ])
            
            rerank_prompt = f"""Given the user query and candidate documents, score each document's relevance to the query on a scale of 0-10.
Output ONLY a Python list of scores, nothing else. Format: [score1, score2, score3, ...]

Query: {query}

Documents:
{docs_text}

Scores (0-10):"""
            
            # Get reranking scores
            response = self.reranker_llm.invoke(rerank_prompt)
            scores_text = response.content.strip()
            
            # Parse scores
            import ast
            try:
                scores = ast.literal_eval(scores_text)
                if not isinstance(scores, list):
                    raise ValueError("Not a list")
            except:
                # Fallback: try to extract numbers
                import re
                scores = [float(s) for s in re.findall(r'\d+\.?\d*', scores_text)]
            
            # Ensure we have correct number of scores
            if len(scores) != len(results):
                logger.warning(f"Reranking returned {len(scores)} scores for {len(results)} documents. Using original ranking.")
                return results[:top_k]
            
            # Combine scores with results
            for i, result in enumerate(results):
                result['rerank_score'] = scores[i]
                # Combine vector similarity and rerank score
                result['combined_score'] = (1 - result['similarity_score']) * 0.4 + (scores[i] / 10) * 0.6
            
            # Sort by combined score (descending)
            reranked = sorted(results, key=lambda x: x.get('combined_score', 0), reverse=True)
            
            logger.info(f"Reranking completed. Top score: {reranked[0].get('combined_score', 0):.3f}")
            return reranked[:top_k]
            
        except Exception as e:
            logger.warning(f"Reranking failed: {e}. Using original ranking.")
            return results[:top_k]
    
    def search_documents(self, query: str, k: int = 5, use_reranking: bool = True, 
                        use_hyde: bool = True, use_hybrid: bool = True) -> List[Dict[str, Any]]:
        """
        Search for similar documents with advanced features: HyDE, Hybrid Search, and Reranking.
        
        Args:
            query: Search query
            k: Number of results to return
            use_reranking: Whether to use Gemini reranking
            use_hyde: Whether to use HyDE query expansion
            use_hybrid: Whether to use hybrid search (BM25 + Vector)
            
        Returns:
            List[Dict]: List of search results with metadata
        """
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return []
        
        try:
            # Step 1: Query Expansion with HyDE
            search_query = query
            if use_hyde and self.reranker_llm:
                search_query = self._expand_query_with_hyde(query)
            
            # Step 2: Perform search (Hybrid or Vector only)
            if use_hybrid and self.bm25:
                # Hybrid search (BM25 + Vector)
                formatted_results = self._hybrid_search(search_query, k=k, vector_weight=0.6)
            else:
                # Vector search only
                fetch_k = k * 3 if use_reranking else k
                results = self.vector_store.similarity_search_with_score(search_query, k=fetch_k)
                
                # Format results
                formatted_results = []
                for doc, score in results:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": float(score)
                    })
            
            if not formatted_results:
                return []
            
            # Step 3: Apply reranking if enabled
            if use_reranking and formatted_results and self.reranker_llm:
                formatted_results = self._rerank_results(query, formatted_results, top_k=k)
            else:
                formatted_results = formatted_results[:k]
            
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
