#!/usr/bin/env python3
"""
Comprehensive Test Script for RAG System

This script tests all components of the RAG system:
1. Environment variables
2. Vector search tool
3. Web search tool
4. RAG system orchestrator
5. End-to-end query processing
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_environment():
    """Test environment variables."""
    print_section("1. Testing Environment Variables")
    
    google_key = os.getenv("GOOGLE_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print(f"✓ GOOGLE_API_KEY: {'Set' if google_key else '❌ NOT SET'}")
    print(f"✓ TAVILY_API_KEY: {'Set' if tavily_key else '❌ NOT SET'}")
    
    if not google_key:
        print("\n⚠️  WARNING: GOOGLE_API_KEY not set!")
        print("   Set it with: export GOOGLE_API_KEY='your-key-here'")
        return False
    
    if not tavily_key:
        print("\n⚠️  WARNING: TAVILY_API_KEY not set!")
        print("   Set it with: export TAVILY_API_KEY='your-key-here'")
        return False
    
    print("\n✅ All environment variables are set!")
    return True


def test_vector_search():
    """Test vector search tool."""
    print_section("2. Testing Vector Search Tool")
    
    try:
        from rag_agent.tools.vector_search import get_vector_store_status, vector_search_tool
        
        print("Checking vector store status...")
        status = get_vector_store_status()
        print(f"Status: {status}")
        
        if status.get("status") == "error":
            print("\n⚠️  Vector store not initialized!")
            print("   Run: python backend/rag_agent/scripts/initialize_vector_db.py")
            return False
        
        print("\nTesting vector search...")
        result = vector_search_tool.invoke({"query": "remote work policy"})
        print(f"Result (first 200 chars):\n{result[:200]}...")
        
        print("\n✅ Vector search tool is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing vector search: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_search():
    """Test web search tool."""
    print_section("3. Testing Web Search Tool")
    
    try:
        from rag_agent.tools.web_search import get_web_search_status, web_search_tool
        
        print("Checking web search status...")
        status = get_web_search_status()
        print(f"Status: {status}")
        
        if status.get("status") == "error":
            print(f"\n❌ Web search tool error: {status.get('message')}")
            return False
        
        print("\nTesting web search...")
        result = web_search_tool.invoke({"query": "latest technology news", "max_results": 2})
        print(f"Result (first 300 chars):\n{result[:300]}...")
        
        print("\n✅ Web search tool is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing web search: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_langchain_config():
    """Test LangChain configuration."""
    print_section("4. Testing LangChain Configuration")
    
    try:
        from rag_agent.config.langchain import langchain_config
        
        print("Testing LLM initialization...")
        llm = langchain_config.get_llm()
        print(f"✓ LLM initialized: {type(llm).__name__}")
        
        print("\nTesting embeddings...")
        embeddings = langchain_config.get_embedding()
        print(f"✓ Embeddings initialized: {type(embeddings).__name__}")
        
        print("\nTesting LLM with simple query...")
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Say hello in one word")])
        print(f"✓ LLM response: {response.content[:50]}")
        
        print("\n✅ LangChain configuration is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing LangChain: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_langgraph_config():
    """Test LangGraph configuration."""
    print_section("5. Testing LangGraph Configuration")
    
    try:
        from rag_agent.config.langraph import langraph_config
        from rag_agent.config.langchain import langchain_config
        
        print("Testing tool registry...")
        tools = langraph_config.tool_registry.list_tools()
        print(f"✓ Available tools: {tools}")
        
        print("\nTesting supervisor agent creation...")
        llm = langchain_config.get_llm()
        supervisor = langraph_config.create_supervisor_agent(llm)
        print(f"✓ Supervisor agent created: {type(supervisor).__name__}")
        
        print("\n✅ LangGraph configuration is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing LangGraph: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_system():
    """Test RAG system orchestrator."""
    print_section("6. Testing RAG System Orchestrator")
    
    try:
        from rag_agent.config.orchestrator import rag_system
        
        print("Initializing RAG system...")
        rag_system.initialize(environment="development")
        print("✓ RAG system initialized")
        
        print("\nTesting query processing...")
        test_query = "What is the remote work policy?"
        print(f"Query: {test_query}")
        
        result = rag_system.query(test_query)
        print(f"\nResponse:\n{result['response'][:300]}...")
        print(f"\nSources: {len(result.get('sources', []))} source(s)")
        print(f"Confidence: {result.get('confidence', 0)}")
        
        print("\n✅ RAG system orchestrator is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing RAG system: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_routes():
    """Test API routes (without running server)."""
    print_section("7. Testing API Routes")
    
    try:
        from rag_agent.routes.router import router
        
        print(f"✓ Router imported successfully")
        print(f"✓ Router prefix: {router.prefix}")
        print(f"✓ Number of routes: {len(router.routes)}")
        
        print("\nAvailable routes:")
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                print(f"  - {list(route.methods)[0] if route.methods else 'GET'} {route.path}")
        
        print("\n✅ API routes are properly configured!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing API routes: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "🚀 " * 20)
    print("  RAG SYSTEM COMPREHENSIVE TEST")
    print("🚀 " * 20)
    
    results = {
        "Environment": test_environment(),
        "Vector Search": test_vector_search(),
        "Web Search": test_web_search(),
        "LangChain Config": test_langchain_config(),
        "LangGraph Config": test_langgraph_config(),
        "RAG System": test_rag_system(),
        "API Routes": test_api_routes(),
    }
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    print(f"\n{'=' * 60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'=' * 60}")
    
    if passed == total:
        print("\n🎉 All tests passed! The RAG system is fully operational.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

