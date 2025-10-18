#!/usr/bin/env python3
"""
Hybrid Search Solution - Combine semantic and keyword search
Based on documentation research and best practices
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add the backend directory to the path
current_dir = Path(__file__).parent
rag_agent_dir = current_dir.parent
backend_dir = rag_agent_dir.parent
sys.path.insert(0, str(backend_dir))

def hybrid_search_solution():
    """Implement hybrid search combining semantic and keyword matching."""
    print("\n" + "="*100)
    print("🔀 HYBRID SEARCH SOLUTION")
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
    
    # Initialize manager
    manager = VectorStoreManager(
        documents_path=documents_path,
        vector_store_path=vector_store_path,
        embedding_model=langchain_config.embedding_model
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
    
    def hybrid_search(query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword matching.
        """
        # 1. Semantic search
        semantic_results = manager.search_documents(query, k=k*2)  # Get more results
        
        # 2. Keyword search
        keyword_results = []
        for result in semantic_results:
            content = result['content'].lower()
            query_terms = query.lower().split()
            
            # Calculate keyword match score
            keyword_score = 0
            for term in query_terms:
                if term in content:
                    keyword_score += content.count(term)
            
            # Add keyword score to result
            result['keyword_score'] = keyword_score
            keyword_results.append(result)
        
        # 3. Combine scores (weighted average)
        for result in keyword_results:
            semantic_score = result['similarity_score']
            keyword_score = result['keyword_score']
            
            # Weighted combination (70% semantic, 30% keyword)
            combined_score = (semantic_score * 0.7) + (keyword_score * 0.3)
            result['combined_score'] = combined_score
        
        # 4. Sort by combined score
        keyword_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return keyword_results[:k]
    
    # Test hybrid search
    print(f"\n🧪 Testing hybrid search...")
    
    test_queries = [
        "What equipment does Zaman Bank provide?",
        "equipment technology Zaman Bank",
        "laptop monitor VPN software"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 80)
        
        results = hybrid_search(query, k=3)
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                semantic_score = result['similarity_score']
                keyword_score = result['keyword_score']
                combined_score = result['combined_score']
                content = result['content'][:150].replace('\n', ' ')
                
                print(f"   {i}. Combined: {combined_score:.4f} (Semantic: {semantic_score:.4f}, Keyword: {keyword_score})")
                print(f"      Content: {content}...")
                print()
        else:
            print("❌ No results found")
    
    print("\n" + "="*100)
    print("🎉 Hybrid search solution complete!")
    print("="*100)

if __name__ == "__main__":
    hybrid_search_solution()
