#!/usr/bin/env python3
"""
Detailed Vector Search Test - Check chunks and similarity scores
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
current_dir = Path(__file__).parent
rag_agent_dir = current_dir.parent
backend_dir = rag_agent_dir.parent
sys.path.insert(0, str(backend_dir))

def test_detailed_search():
    """Test vector search with detailed output."""
    print("\n" + "="*100)
    print("🔍 DETAILED VECTOR SEARCH TEST")
    print("="*100)
    
    from rag_agent.utils.vector_store import VectorStoreManager
    from rag_agent.config.langchain import langchain_config
    import os
    
    # Get config
    config = langchain_config
    documents_path = "rag_agent/documents"
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    print(f"\n📁 Configuration:")
    print(f"   Documents path: {documents_path}")
    print(f"   Vector store path: {config.vector_store_path}")
    print(f"   Embedding model: {config.embedding_model}")
    print(f"   Google API Key: {'✅ Found' if google_api_key else '❌ Missing'}")
    
    # Initialize manager
    manager = VectorStoreManager(
        documents_path=documents_path,
        vector_store_path=config.vector_store_path,
        embedding_model=config.embedding_model
    )
    
    # Initialize embeddings
    print(f"\n🔄 Initializing embeddings...")
    success = manager.initialize_embeddings(google_api_key)
    if not success:
        print("❌ Failed to initialize embeddings")
        return
    print("✅ Embeddings initialized")
    
    # Load vector store
    print(f"\n🔄 Loading vector store...")
    success = manager.load_vector_store()
    if not success:
        print("❌ Failed to load vector store")
        return
    print("✅ Vector store loaded")
    
    # Test queries
    test_queries = [
        "equipment technology Zaman Bank",
        "laptop monitor VPN software",
        "what does company provide employees",
        "EQUIPMENT AND TECHNOLOGY",
        "Zaman Bank provides",
    ]
    
    for query in test_queries:
        print(f"\n{'='*100}")
        print(f"📝 QUERY: '{query}'")
        print(f"{'='*100}")
        
        try:
            results = manager.search_documents(query, k=3)
            
            if not results:
                print("❌ No results found")
                continue
            
            for i, result in enumerate(results, 1):
                print(f"\n  🔷 Result {i}:")
                print(f"     Similarity Score: {result['similarity_score']:.4f}")
                print(f"     Source: {result['metadata'].get('source', 'unknown')}")
                print(f"     Chunk ID: {result['metadata'].get('chunk_id', 'unknown')}/{result['metadata'].get('total_chunks', 'unknown')}")
                print(f"     Content Preview:")
                content = result['content']
                # Show first 300 chars
                print(f"     {content[:300]}...")
                print()
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("="*100)
    print("🎉 Test complete!")
    print("="*100)

if __name__ == "__main__":
    test_detailed_search()

