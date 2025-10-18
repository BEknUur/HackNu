#!/usr/bin/env python3
"""
Semantic Chunking Solution - Document structure-aware chunking
Based on LangChain best practices and documentation research
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# Add the backend directory to the path
current_dir = Path(__file__).parent
rag_agent_dir = current_dir.parent
backend_dir = rag_agent_dir.parent
sys.path.insert(0, str(backend_dir))

def semantic_chunking_solution():
    """Implement semantic chunking based on document structure."""
    print("\n" + "="*100)
    print("🧠 SEMANTIC CHUNKING SOLUTION")
    print("="*100)
    
    from rag_agent.utils.vector_store import VectorStoreManager
    from rag_agent.config.langchain import langchain_config
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
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
        import shutil
        shutil.rmtree(vector_store_dir)
        print("✅ Existing vector store deleted")
    
    # Load documents
    print(f"\n📄 Loading documents...")
    manager = VectorStoreManager(
        documents_path=documents_path,
        vector_store_path=vector_store_path,
        embedding_model=langchain_config.embedding_model
    )
    
    documents = manager.load_documents()
    if not documents:
        print("❌ No documents found")
        return
    print(f"✅ Loaded {len(documents)} documents")
    
    # SEMANTIC CHUNKING: Split by document sections
    print(f"\n🧠 Applying semantic chunking...")
    semantic_chunks = []
    
    for doc in documents:
        content = doc.page_content
        source = doc.metadata.get('source', 'unknown')
        
        # Split by major sections (numbered sections)
        sections = re.split(r'\n(\d+\.\s+[A-Z][A-Z\s]+)', content)
        
        current_section = ""
        section_title = ""
        
        for i, part in enumerate(sections):
            if i == 0:
                # Document header
                current_section = part
            elif re.match(r'\d+\.\s+[A-Z][A-Z\s]+', part):
                # Save previous section if it exists
                if current_section.strip():
                    chunk = Document(
                        page_content=current_section.strip(),
                        metadata={
                            **doc.metadata,
                            'section_title': section_title,
                            'chunk_type': 'semantic_section'
                        }
                    )
                    semantic_chunks.append(chunk)
                
                # Start new section
                section_title = part.strip()
                current_section = part
            else:
                # Content of current section
                current_section += part
        
        # Add the last section
        if current_section.strip():
            chunk = Document(
                page_content=current_section.strip(),
                metadata={
                    **doc.metadata,
                    'section_title': section_title,
                    'chunk_type': 'semantic_section'
                }
            )
            semantic_chunks.append(chunk)
    
    print(f"✅ Created {len(semantic_chunks)} semantic chunks")
    
    # Show chunk previews
    print(f"\n📋 Semantic Chunk Preview:")
    for i, chunk in enumerate(semantic_chunks[:8]):  # Show first 8 chunks
        section_title = chunk.metadata.get('section_title', 'Header')
        content_preview = chunk.page_content[:100].replace('\n', ' ')
        print(f"   Chunk {i+1} [{section_title}]: {content_preview}...")
    
    # Initialize embeddings
    print(f"\n🔄 Initializing embeddings...")
    success = manager.initialize_embeddings(google_api_key)
    if not success:
        print("❌ Failed to initialize embeddings")
        return
    print("✅ Embeddings initialized")
    
    # Create vector store
    print(f"\n🔄 Creating FAISS vector store...")
    success = manager.create_vector_store(semantic_chunks)
    if not success:
        print("❌ Failed to create vector store")
        return
    print("✅ Vector store created successfully")
    
    # Save vector store
    print(f"\n💾 Saving vector store to disk...")
    success = manager.save_vector_store()
    if not success:
        print("❌ Failed to save vector store")
        return
    print("✅ Vector store saved successfully")
    
    # Test search with optimized queries
    print(f"\n🧪 Testing search with optimized queries...")
    
    test_queries = [
        "EQUIPMENT AND TECHNOLOGY OF Zaman Bank",
        "company provides laptop monitor VPN",
        "what equipment does Zaman Bank provide",
        "laptop computer monitor software licenses"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        results = manager.search_documents(query, k=3)
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                score = result['similarity_score']
                section = result['metadata'].get('section_title', 'Unknown')
                content = result['content'][:150].replace('\n', ' ')
                print(f"   {i}. Score: {score:.4f} [{section}] - {content}...")
        else:
            print("❌ No results found")
    
    print("\n" + "="*100)
    print("🎉 Semantic chunking solution complete!")
    print("="*100)

if __name__ == "__main__":
    semantic_chunking_solution()
