#!/usr/bin/env python3
"""
Force Reindex Vector Store - Delete and recreate with better chunking
"""

import os
import sys
import shutil
from pathlib import Path

# Add the backend directory to the path
current_dir = Path(__file__).parent
rag_agent_dir = current_dir.parent
backend_dir = rag_agent_dir.parent
sys.path.insert(0, str(backend_dir))

def force_reindex():
    """Force reindex the vector store with better parameters."""
    print("\n" + "="*100)
    print("🔄 FORCE REINDEX VECTOR STORE")
    print("="*100)
    
    from rag_agent.utils.vector_store import VectorStoreManager
    from rag_agent.config.langchain import langchain_config
    import os
    
    # Configuration
    documents_path = "rag_agent/documents"
    vector_store_path = "rag_agent/data/vector_store"
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    print(f"\n📁 Configuration:")
    print(f"   Documents path: {documents_path}")
    print(f"   Vector store path: {vector_store_path}")
    print(f"   Google API Key: {'✅ Found' if google_api_key else '❌ Missing'}")
    
    # Delete existing vector store
    print(f"\n🗑️  Deleting existing vector store...")
    vector_store_dir = Path(vector_store_path)
    if vector_store_dir.exists():
        shutil.rmtree(vector_store_dir)
        print("✅ Existing vector store deleted")
    else:
        print("ℹ️  No existing vector store found")
    
    # Create new vector store with BETTER chunking
    print(f"\n🔄 Creating new vector store with optimized chunking...")
    
    # Use MUCH smaller chunks to ensure EQUIPMENT section is captured
    manager = VectorStoreManager(
        documents_path=documents_path,
        vector_store_path=vector_store_path,
        embedding_model=langchain_config.embedding_model,
        chunk_size=300,  # MUCH smaller chunks!
        chunk_overlap=50  # Less overlap for cleaner chunks!
    )
    
    # Initialize embeddings
    print(f"\n🔄 Initializing embeddings...")
    success = manager.initialize_embeddings(google_api_key)
    if not success:
        print("❌ Failed to initialize embeddings")
        return
    print("✅ Embeddings initialized")
    
    # Load documents
    print(f"\n📄 Loading documents...")
    documents = manager.load_documents()
    if not documents:
        print("❌ No documents found")
        return
    print(f"✅ Loaded {len(documents)} documents")
    
    # Process into chunks
    print(f"\n🔪 Processing documents into chunks...")
    chunks = manager.process_documents(documents)
    print(f"✅ Created {len(chunks)} chunks")
    
    # Show chunk previews
    print(f"\n📋 Chunk Preview:")
    for i, chunk in enumerate(chunks[:6]):  # Show first 6 chunks
        content_preview = chunk.page_content[:100].replace('\n', ' ')
        print(f"   Chunk {i+1}: {content_preview}...")
    
    # Create vector store
    print(f"\n🔄 Creating FAISS vector store...")
    success = manager.create_vector_store(chunks)
    if not success:
        print("❌ Failed to create vector store")
        return
    print("✅ Vector store created successfully")
    
    # Save vector store to disk
    print(f"\n💾 Saving vector store to disk...")
    success = manager.save_vector_store()
    if not success:
        print("❌ Failed to save vector store")
        return
    print("✅ Vector store saved successfully")
    
    # Test search
    print(f"\n🧪 Testing search for EQUIPMENT...")
    results = manager.search_documents("equipment technology Zaman Bank", k=3)
    
    if results:
        print(f"✅ Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            score = result['similarity_score']
            content = result['content'][:150].replace('\n', ' ')
            print(f"   {i}. Score: {score:.4f} - {content}...")
    else:
        print("❌ No results found for EQUIPMENT")
    
    print("\n" + "="*100)
    print("🎉 Force reindex complete!")
    print("="*100)

if __name__ == "__main__":
    force_reindex()
