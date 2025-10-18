#!/usr/bin/env python3
"""
Simple Vector Database Initialization Script

This script initializes the FAISS vector database from the documents
using Google embeddings. Run this script to create the vector store
before using the RAG system.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path so we can import our modules
current_dir = Path(__file__).parent
rag_agent_dir = current_dir.parent
backend_dir = rag_agent_dir.parent
sys.path.insert(0, str(backend_dir))

def main():
    """Simple initialization function."""
    print("🚀 Initializing Vector Database")
    print("=" * 40)
    
    # Check for Google API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ Error: GOOGLE_API_KEY not set")
        print("Set it with: export GOOGLE_API_KEY='your-key-here'")
        return False
    
    print("✅ Google API key found")
    
    # Set up paths
    documents_path = current_dir.parent / "documents"
    vector_store_path = current_dir.parent / "data" / "vector_store"
    
    # Check documents exist
    if not documents_path.exists():
        print(f"❌ Documents directory not found: {documents_path}")
        return False
    
    doc_files = list(documents_path.glob("*.txt"))
    if not doc_files:
        print(f"❌ No .txt files found in {documents_path}")
        return False
    
    print(f"📄 Found {len(doc_files)} documents:")
    for doc_file in doc_files:
        print(f"   - {doc_file.name}")
    
    print("\n🔄 Creating vector store...")
    
    try:
        # Import and use the vector store utility
        from utils.vector_store import create_vector_store_from_documents
        
        success = create_vector_store_from_documents(
            documents_path=str(documents_path),
            vector_store_path=str(vector_store_path),
            google_api_key=google_api_key
        )
        
        if success:
            print("✅ Vector database created successfully!")
            print(f"📁 Saved to: {vector_store_path}")
            
            # Simple test
            print("\n🧪 Testing search...")
            try:
                from tools.vector_search import vector_search_tool
                result = vector_search_tool.invoke({"query": "company policies"})
                print(f"Test result: {result[:100]}...")
                print("✅ Search is working!")
            except Exception as e:
                print(f"⚠️  Search test failed: {e}")
            
            return True
        else:
            print("❌ Failed to create vector database")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Done!")
    else:
        print("\n💥 Failed!")
        sys.exit(1)
