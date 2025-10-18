# RAG Agent System

A flexible, configurable RAG (Retrieval-Augmented Generation) system built with LangChain and LangGraph, featuring vector search and web search capabilities.

## Overview

This RAG system provides:
- **Local Knowledge Search**: Vector-based search through company documents using FAISS and Google embeddings
- **Web Search**: Real-time web search using Tavily API
- **Intelligent Agent Orchestration**: LangGraph-based agent system that routes queries to appropriate tools
- **Flexible Configuration**: Easily extensible with new tools and agents

## Architecture

```
rag_agent/
├── config/          # Configuration for LangChain, LangGraph, and orchestration
├── tools/           # Search tools (vector_search, web_search)
├── utils/           # Utilities (vector store management)
├── routes/          # FastAPI routes
├── schemas/         # Pydantic schemas
├── scripts/         # Initialization scripts
└── documents/       # Document repository for vector search
```

## Prerequisites

- Python 3.12+
- Google API Key (for embeddings and LLM)
- Tavily API Key (for web search)

## Setup

### 1. Install Dependencies

Dependencies are already included in `backend/requirements.txt`:

```bash
pip install -r backend/requirements.txt
```

### 2. Configure Environment Variables

Create or update your `.env` file with:

```bash
# Required: Google API Key for embeddings and LLM
GOOGLE_API_KEY=your-google-api-key-here

# Required: Tavily API Key for web search
TAVILY_API_KEY=your-tavily-api-key-here

# Optional: Environment setting
ENVIRONMENT=development
```

**Get API Keys:**
- Google API Key: https://makersuite.google.com/app/apikey
- Tavily API Key: https://tavily.com/

### 3. Initialize Vector Database

Before using the RAG system, you need to initialize the vector database from your documents:

```bash
# From the backend directory
cd backend
python rag_agent/scripts/initialize_vector_db.py
```

This will:
- Load all `.txt` files from `rag_agent/documents/`
- Create embeddings using Google's embedding model
- Build and save a FAISS vector store to `rag_agent/data/vector_store/`

### 4. Add Your Documents

Place your company documents (`.txt` files) in:
```
backend/rag_agent/documents/
```

Then re-run the initialization script to update the vector database.

## API Usage

### Query Endpoint

**POST** `/api/rag/query`

Send a question to the RAG system:

```json
{
  "query": "What is the remote work policy?",
  "context": {},
  "environment": "development"
}
```

Response:
```json
{
  "query": "What is the remote work policy?",
  "response": "According to our remote work policy document...",
  "sources": [
    {
      "tool": "vector_search",
      "query": {"query": "remote work policy"}
    }
  ],
  "confidence": 0.8,
  "status": "success"
}
```

### System Status

**GET** `/api/rag/status`

Check if the RAG system is operational:

```json
{
  "status": "operational",
  "supervisor_agent": true,
  "specialist_agents": ["local_knowledge", "web_search"],
  "available_tools": ["vector_search", "web_search"],
  "available_agents": ["supervisor", "local_knowledge", "web_search"]
}
```

### Tools Status

**GET** `/api/rag/tools/status`

Check the status of individual tools:

```json
{
  "vector_search": {
    "status": "ready",
    "message": "Vector store is ready",
    "available": true
  },
  "web_search": {
    "status": "ready",
    "message": "Web search tool is ready and configured",
    "available": true
  }
}
```

### Initialize System

**POST** `/api/rag/initialize`

Manually initialize or reinitialize the RAG system:

```json
{
  "environment": "development"
}
```

## How It Works

### 1. Query Flow

1. **User submits a query** → RAG API endpoint
2. **Supervisor Agent** analyzes the query and determines which tools to use:
   - Internal company info → `vector_search`
   - Current events/external info → `web_search`
   - Complex queries → Both tools
3. **Tools execute** and return relevant information
4. **Supervisor Agent** synthesizes the results into a coherent response
5. **Response returned** to user with sources and confidence score

### 2. Vector Search Tool

- Uses FAISS for fast similarity search
- Google's `models/embedding-001` for embeddings
- Searches through local document repository
- Returns top-k most relevant document chunks

### 3. Web Search Tool

- Uses Tavily API for web search
- Provides real-time information
- Returns relevant web pages with summaries
- Supports news-specific searches

### 4. Agent System

Built on LangGraph's `create_react_agent`:
- **Supervisor Agent**: Routes queries to appropriate tools
- **Local Knowledge Agent**: Specializes in document search
- **Web Search Agent**: Specializes in web information retrieval

## Configuration

### LangChain Configuration (`config/langchain.py`)

Configure LLM providers, embeddings, and tools:

```python
from rag_agent.config import langchain_config

# Change default LLM provider
langchain_config.default_provider = "google"

# Get LLM instance
llm = langchain_config.get_llm()

# Get embeddings
embeddings = langchain_config.get_embedding()
```

### LangGraph Configuration (`config/langraph.py`)

Configure agents and tool registry:

```python
from rag_agent.config import langraph_config

# Add custom tool
from langchain_core.tools import tool

@tool
def custom_tool(query: str) -> str:
    """Custom tool description."""
    return "result"

langraph_config.add_custom_tool("custom_tool", custom_tool)
```

### Orchestrator Configuration (`config/orchestrator.py`)

High-level system configuration:

```python
from rag_agent.config import rag_system

# Initialize for specific environment
rag_system.initialize(environment="production")

# Process query
result = rag_system.query("What is our travel policy?")
```

## Troubleshooting

### "Vector store not available" Error

**Solution:** Run the initialization script:
```bash
python backend/rag_agent/scripts/initialize_vector_db.py
```

### "GOOGLE_API_KEY not set" Error

**Solution:** Set your Google API key in `.env`:
```bash
GOOGLE_API_KEY=your-key-here
```

### "TAVILY_API_KEY not set" Error

**Solution:** Set your Tavily API key in `.env`:
```bash
TAVILY_API_KEY=your-key-here
```

### No Documents Found

**Solution:** Add `.txt` files to `backend/rag_agent/documents/` and reinitialize:
```bash
python backend/rag_agent/scripts/initialize_vector_db.py
```

### "create_react_agent() got unexpected keyword arguments" Error

**Solution:** This has been fixed. Ensure you're using the latest version of the code with `messages_modifier` instead of `state_modifier`.

## Development

### Adding New Documents

1. Place `.txt` files in `backend/rag_agent/documents/`
2. Run initialization script:
   ```bash
   python backend/rag_agent/scripts/initialize_vector_db.py
   ```

### Adding Custom Tools

1. Create a new tool function:
   ```python
   from langchain_core.tools import tool
   
   @tool
   def my_custom_tool(query: str) -> str:
       """Tool description for the agent."""
       # Your implementation
       return result
   ```

2. Register the tool:
   ```python
   from rag_agent.config import rag_system
   rag_system.add_tool("my_custom_tool", my_custom_tool)
   ```

### Adding Custom Agents

1. Create an agent configuration:
   ```python
   from rag_agent.config.langraph import AgentConfig
   
   class MyAgentConfig(AgentConfig):
       name: str = "my_agent"
       description: str = "My custom agent"
       tools: List[str] = ["vector_search"]
       system_prompt: str = "You are a custom agent..."
   ```

2. Register the agent:
   ```python
   from rag_agent.config import rag_system
   rag_system.add_agent("my_agent", MyAgentConfig())
   ```

## Testing

Test the vector search tool:
```bash
cd backend
python -m rag_agent.tools.vector_search
```

Test the web search tool:
```bash
cd backend
python -m rag_agent.tools.web_search
```

## Production Deployment

1. **Set environment to production:**
   ```bash
   ENVIRONMENT=production
   ```

2. **Ensure all API keys are set securely**

3. **Initialize vector database:**
   ```bash
   python backend/rag_agent/scripts/initialize_vector_db.py
   ```

4. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Performance Optimization

- **Vector Store**: FAISS is optimized for fast similarity search
- **Caching**: Vector store is loaded once and reused across requests
- **Parallel Agents**: Enable parallel execution in production:
  ```python
  orchestrator_config.enable_parallel_agents = True
  ```

## Security Considerations

- Store API keys in environment variables, never in code
- Use `.env` files for local development
- Use secure secret management in production (e.g., AWS Secrets Manager, HashiCorp Vault)
- Validate and sanitize all user inputs
- Implement rate limiting for API endpoints

## License

Part of the HackNu project.

