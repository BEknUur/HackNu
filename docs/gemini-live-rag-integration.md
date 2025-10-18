# Gemini Live + RAG Integration

## Overview

This document describes the integration between **Gemini Live** (frontend multimodal chat) and the **Agentic RAG System** (backend with vector_search and web_search tools).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│                  (Voice/Camera/Screen)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React Native/Expo)                  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              live-chat.tsx                                │  │
│  │  - Gemini Live Connection                                │  │
│  │  - Audio/Video/Screen Capture                            │  │
│  │  - RAG Tools Integration                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         use-live-api-with-rag.ts                         │  │
│  │  - Connects to Gemini Live                               │  │
│  │  - Registers RAG tools with Gemini                       │  │
│  │  - Handles tool calls                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              use-rag-tools.ts                            │  │
│  │  - Loads function declarations                           │  │
│  │  - Intercepts Gemini tool calls                          │  │
│  │  - Routes calls to backend                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           rag-tools-client.ts                            │  │
│  │  - HTTP client for backend                               │  │
│  │  - GET function declarations                             │  │
│  │  - POST tool calls                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         /api/rag/live/function-declarations              │  │
│  │  Returns: Tool schemas for Gemini                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         /api/rag/live/tool-call                          │  │
│  │  Executes: vector_search or web_search                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  ┌────────────────────┬───────────────────────────────────┐   │
│  │  vector_search_tool│       web_search_tool             │   │
│  │  - FAISS Vector DB │       - Tavily API                │   │
│  │  - Company Docs    │       - Web Search                │   │
│  └────────────────────┴───────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Flow

### 1. Connection Flow

```
User clicks "Connect"
   ↓
Frontend loads RAG function declarations from backend
   ↓
Frontend registers tools with Gemini Live config
   ↓
Gemini connects with tools registered
   ↓
"🧠 RAG" indicator shows green (healthy)
```

### 2. Query Flow (Example: "What is our remote work policy?")

```
User speaks: "What is our remote work policy?"
   ↓
Audio → Gemini Live API
   ↓
Gemini analyzes query → Decides to use vector_search tool
   ↓
Gemini sends tool_call event → { name: "vector_search", args: { query: "remote work policy" } }
   ↓
Frontend intercepts tool_call event
   ↓
Frontend → POST /api/rag/live/tool-call
   ↓
Backend executes vector_search_tool
   ↓
FAISS searches documents → Returns relevant chunks
   ↓
Backend → Returns results to frontend
   ↓
Frontend → Sends tool response to Gemini
   ↓
Gemini synthesizes answer with tool results
   ↓
Gemini speaks answer to user (audio output)
```

### 3. Multi-Tool Flow (Example: "What's our policy and latest AI trends?")

```
User asks hybrid question
   ↓
Gemini decides to use BOTH tools
   ↓
Tool Call 1: vector_search({ query: "company policy" })
   ↓
Tool Call 2: web_search({ query: "latest AI trends" })
   ↓
Both execute in parallel
   ↓
Results combined
   ↓
Gemini synthesizes comprehensive answer
```

## Key Components

### Backend

#### 1. `live_tools_router.py`
- **Endpoint**: `/api/rag/live/function-declarations`
  - Returns Gemini-compatible tool schemas
  
- **Endpoint**: `/api/rag/live/tool-call`
  - Executes vector_search or web_search
  - Returns formatted results

- **Endpoint**: `/api/rag/live/health`
  - Checks tool health status

#### 2. Tool Executors
- `execute_vector_search(query, top_k)` → Searches local knowledge base
- `execute_web_search(query, max_results)` → Searches web via Tavily

### Frontend

#### 1. `rag-tools-client.ts`
- HTTP client for backend communication
- `getFunctionDeclarations()` - Load tool schemas
- `executeToolCall()` - Execute tool on backend

#### 2. `use-rag-tools.ts`
- React hook for RAG tools
- Loads function declarations on mount
- Handles tool_call events from Gemini
- Routes to backend and returns results

#### 3. `use-live-api-with-rag.ts`
- Enhanced useLiveAPI with RAG support
- Registers tools with Gemini config
- Manages RAG tools state

#### 4. `live-chat.tsx`
- Main chat UI
- Shows RAG indicator (🧠 RAG - green when healthy)
- Enhanced system prompts with tool instructions

## Configuration

### Backend

Add to `.env`:
```bash
GOOGLE_API_KEY=your-google-api-key
TAVILY_API_KEY=your-tavily-api-key
```

### Frontend

Add to `.env`:
```bash
EXPO_PUBLIC_GEMINI_API_KEY=your-google-api-key
EXPO_PUBLIC_BACKEND_URL=http://46.101.175.118:8000
```

## Usage

### Start Backend
```bash
cd backend
docker compose up --build
```

### Initialize Vector Store (First Time)
```bash
docker compose exec backend python /backend/rag_agent/scripts/initialize_vector_db.py
```

### Start Frontend
```bash
cd frontend
npm install
npm start
```

### Using the Chat

1. **Open Live Chat tab**
2. **Check RAG indicator**: 🧠 RAG (should be green)
3. **Click "Connect"**
4. **Start talking!**

### Example Questions

**For Vector Search (Internal Knowledge):**
- "What is our remote work policy?"
- "Tell me about our travel policy"
- "What are the company guidelines for..."

**For Web Search (External Knowledge):**
- "What are the latest AI trends?"
- "Find information about ZamanBank"
- "What's happening in Kazakhstan?"

**For Both:**
- "Compare our remote work policy with industry standards"
- "What's our policy on AI and what are the latest AI developments?"

## Tool Schemas

### vector_search
```json
{
  "name": "vector_search",
  "description": "Search through local company knowledge base...",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "top_k": {
        "type": "integer",
        "description": "Number of results (default: 3)"
      }
    },
    "required": ["query"]
  }
}
```

### web_search
```json
{
  "name": "web_search",
  "description": "Search the web for current information...",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "max_results": {
        "type": "integer",
        "description": "Max results (default: 5)"
      }
    },
    "required": ["query"]
  }
}
```

## Debugging

### Check Backend Tools Status
```bash
curl http://46.101.175.118:8000/api/rag/live/health
```

### Check Function Declarations
```bash
curl http://46.101.175.118:8000/api/rag/live/function-declarations
```

### Test Tool Call
```bash
curl -X POST http://46.101.175.118:8000/api/rag/live/tool-call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "vector_search", "parameters": {"query": "remote work"}}'
```

### Frontend Console Logs
Look for:
- `[RAG Tools] Loading function declarations...`
- `[RAG Tools] Loaded tools: vector_search, web_search`
- `[RAG Tools] Executing tool: vector_search`
- `[RAG Tools] Tool result: ...`

## Troubleshooting

### RAG Indicator is Red (⚠️)
- Check backend is running
- Verify vector store is initialized
- Check TAVILY_API_KEY is set

### Tools Not Being Called
- Check system prompts include tool instructions
- Verify tools are registered in config
- Check Gemini model supports function calling

### Tool Calls Failing
- Check backend logs: `docker compose logs backend`
- Verify API keys are valid
- Test tool endpoints directly with curl

## Benefits

✅ **Real-time voice interaction** with company knowledge  
✅ **Multimodal**: Voice + Camera + Screen sharing  
✅ **Smart tool selection**: Gemini decides when to use which tool  
✅ **Source citation**: Know where information comes from  
✅ **Live streaming**: Responses in real-time  
✅ **Multilingual**: Supports English and Russian  

## Next Steps

- [ ] Add more tools (calendar, email, database queries)
- [ ] Implement conversation memory
- [ ] Add user authentication and personalization
- [ ] Track tool usage analytics
- [ ] Add tool call visualization in UI

