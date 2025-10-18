#!/usr/bin/env python3
"""
Test Vector Search - Check what's actually in the vector store
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
current_dir = Path(__file__).parent
rag_agent_dir = current_dir.parent
backend_dir = rag_agent_dir.parent
sys.path.insert(0, str(backend_dir))

def test_vector_search():
    """Test vector search with specific queries."""
    print("🔍 Testing Vector Search")
    print("="*80)
    
    from rag_agent.tools.vector_search import vector_search_tool
    
    test_queries = [
        "equipment and technology",
        "laptop monitor VPN",
        "what does company provide",
        "EQUIPMENT AND TECHNOLOGY OF Zaman Bank",
        "remote work equipment"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        print("-"*80)
        
        try:
            result = vector_search_tool.invoke({"query": query, "top_k": 3})
            print(f"✅ Result:\n{result}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
    
    print("="*80)
    print("🎉 Done!")

if __name__ == "__main__":
    test_vector_search()

