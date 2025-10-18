"""
Document loader and processor for creating the vector store.
"""

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config.settings import settings
import os


def load_documents_from_directory(directory_path: str = "data/documents"):
    """
    Load documents from a directory.
    
    Args:
        directory_path: Path to directory containing documents
        
    Returns:
        List of loaded documents
    """
    print(f"Loading documents from {directory_path}...")
    
    documents = []
    
    # Load text files
    try:
        text_loader = DirectoryLoader(
            directory_path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True
        )
        text_docs = text_loader.load()
        documents.extend(text_docs)
        print(f"Loaded {len(text_docs)} text files")
    except Exception as e:
        print(f"Error loading text files: {e}")
    
    # Load PDF files
    try:
        pdf_loader = DirectoryLoader(
            directory_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True
        )
        pdf_docs = pdf_loader.load()
        documents.extend(pdf_docs)
        print(f"Loaded {len(pdf_docs)} PDF files")
    except Exception as e:
        print(f"Error loading PDF files: {e}")
    
    print(f"Total documents loaded: {len(documents)}")
    return documents


def split_documents(documents: list, chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Split documents into smaller chunks.
    
    Args:
        documents: List of documents to split
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of document chunks
    """
    print(f"Splitting documents into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    splits = text_splitter.split_documents(documents)
    print(f"Created {len(splits)} document chunks")
    
    return splits


def create_vector_store(documents: list, save_path: str = None):
    """
    Create a FAISS vector store from documents.
    
    Args:
        documents: List of document chunks
        save_path: Path to save the vector store
        
    Returns:
        FAISS vector store
    """
    print("Creating vector store with embeddings...")
    
    # Initialize embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key
    )
    
    # Create vector store
    vector_store = FAISS.from_documents(documents, embeddings)
    
    print(f"Vector store created with {len(documents)} documents")
    
    # Save if path provided
    if save_path:
        os.makedirs(save_path, exist_ok=True)
        vector_store.save_local(save_path)
        print(f"Vector store saved to {save_path}")
    
    return vector_store


def prepare_knowledge_base(
    documents_dir: str = "data/documents",
    vector_store_path: str = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
    """
    Complete pipeline to prepare the knowledge base.
    
    Args:
        documents_dir: Directory containing documents
        vector_store_path: Path to save vector store
        chunk_size: Size of document chunks
        chunk_overlap: Overlap between chunks
        
    Returns:
        Created vector store
    """
    print("\n" + "="*50)
    print("PREPARING KNOWLEDGE BASE")
    print("="*50 + "\n")
    
    # Use default path if not provided
    if vector_store_path is None:
        vector_store_path = settings.vector_store_path
    
    # Load documents
    documents = load_documents_from_directory(documents_dir)
    
    if not documents:
        print("WARNING: No documents found. Creating empty vector store.")
        documents = [Document(
            page_content="This is a placeholder document. Add your documents to data/documents/",
            metadata={"source": "placeholder"}
        )]
    
    # Split documents
    splits = split_documents(documents, chunk_size, chunk_overlap)
    
    # Create vector store
    vector_store = create_vector_store(splits, vector_store_path)
    
    print("\n" + "="*50)
    print("KNOWLEDGE BASE READY")
    print("="*50 + "\n")
    
    return vector_store


if __name__ == "__main__":
    """Run this script to prepare the knowledge base."""
    prepare_knowledge_base()
