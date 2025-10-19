# 🎯 GEMINI LIVE + RAG ARCHITECTURE - COMPLETE ANALYSIS

## 📊 Executive Summary

Your system has **3 distinct RAG pipelines**, each serving different purposes. Gemini Live currently acts as a **middleware layer** that bridges Google's Multimodal Live API with your RAG tools (vector_search, web_search).

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. Live Chat (live-chat.tsx)                                           │
│     • Uses: useLiveAPIWithRAG hook                                      │
│     • Connects to: Gemini Live API (multimodal)                         │
│     • Audio, Video, Screen sharing                                      │
│     • Tool Declarations: vector_search, web_search                      │
│     │                                                                    │
│     └─► When Gemini decides to call a tool:                            │
│         POST /api/rag/live/query ◄─────────────────────────┐           │
│                                                              │           │
│  2. Explore Chat (explore.tsx)                             │           │
│     • Traditional text chat                                 │           │
│     • Direct connection to backend                          │           │
│     • Full banking capabilities                             │           │
│     │                                                        │           │
│     └─► POST /api/rag/transaction/query                    │           │
│                                                              │           │
└──────────────────────────────────────────────────────────────┴───────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 1. LIVE QUERY ROUTER - /api/rag/live/query                      │  │
│  │    File: backend/rag_agent/routes/live_query_router.py           │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │ Purpose: Middleware for Gemini Live tool calls                   │  │
│  │ Tools: 2 (vector_search, web_search)                            │  │
│  │ Context: NO user context, NO database session                    │  │
│  │                                                                   │  │
│  │ Flow:                                                            │  │
│  │   1. Receives query from Gemini Live                            │  │
│  │   2. Extracts tool_name from context                            │  │
│  │   3. Routes directly to tool (bypasses LangGraph)               │  │
│  │   4. Returns formatted response to Gemini                        │  │
│  │                                                                   │  │
│  │ Key Code:                                                        │  │
│  │   if tool_name == "vector_search":                              │  │
│  │       vector_tool = get_vector_search_tool()                    │  │
│  │       response_text = vector_tool.search(query)                 │  │
│  │   elif tool_name == "web_search":                               │  │
│  │       web_tool = get_web_search_tool()                          │  │
│  │       response_text = web_tool.search(query)                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 2. MAIN RAG ROUTER - /api/rag/query                             │  │
│  │    File: backend/rag_agent/routes/router.py                      │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │ Purpose: Basic RAG queries with LangGraph orchestration          │  │
│  │ Tools: 2 (vector_search, web_search)                            │  │
│  │ Context: NO user context, NO database session                    │  │
│  │                                                                   │  │
│  │ Flow:                                                            │  │
│  │   1. Receives query                                             │  │
│  │   2. Initializes RAG system if needed                           │  │
│  │   3. Passes to rag_system.query()                               │  │
│  │   4. Supervisor agent decides which tools to use                 │  │
│  │   5. Returns response with sources                               │  │
│  │                                                                   │  │
│  │ Key Code:                                                        │  │
│  │   result = rag_system.query(                                    │  │
│  │       user_query=request.query,                                 │  │
│  │       context=request.context or {}                             │  │
│  │   )                                                              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 3. TRANSACTION RAG ROUTER - /api/rag/transaction/query ⭐       │  │
│  │    File: backend/rag_agent/routes/transaction_router.py          │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │ Purpose: FULL BANKING SYSTEM with ALL TOOLS                     │  │
│  │ Tools: 26 (vector_search, web_search + 24 banking tools)        │  │
│  │ Context: ✅ User context, ✅ Database session, ✅ ALL contexts  │  │
│  │                                                                   │  │
│  │ Flow:                                                            │  │
│  │   1. Receives query + user_id                                   │  │
│  │   2. Sets ALL tool contexts (transaction, account, cart, etc.)  │  │
│  │   3. Passes to rag_system.query()                               │  │
│  │   4. Supervisor agent has access to ALL 26 tools                 │  │
│  │   5. Can perform banking operations                              │  │
│  │                                                                   │  │
│  │ Key Code:                                                        │  │
│  │   set_transaction_context(user_id=request.user_id, db=db)      │  │
│  │   set_account_context(user_id=request.user_id, db=db)          │  │
│  │   set_transaction_history_context(user_id, db)                  │  │
│  │   set_product_context(user_id, db)                              │  │
│  │   set_cart_context(user_id, db)                                 │  │
│  │                                                                   │  │
│  │   result = rag_system.query(user_query, context)                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT ORCHESTRATION LAYER                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  RAG System (orchestrator.py)                                           │
│  └─► Supervisor Agent (LangGraph ReAct Agent)                          │
│       • Created from: langraph.py configuration                         │
│       • System prompt: Decides which tools to use                       │
│       • Has access to tools registered in ToolRegistry                  │
│       │                                                                  │
│       └─► Tool Registry (langraph.py)                                  │
│           • vector_search: Searches company documents                   │
│           • web_search: Searches the web via Tavily                     │
│           • [26 banking tools registered for transaction endpoint]      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 DEEP DIVE: How Gemini Live Integration Works

### 1. Frontend: useLiveAPIWithRAG Hook

**File:** `frontend/hooks/use-live-api-with-rag.ts`

#### What It Does:
- **Extends** the base `useLiveAPI` hook with RAG capabilities
- **Declares tools** to Gemini Live API during configuration
- **Listens** for tool calls from Gemini
- **Calls** your backend when Gemini wants to use a tool

#### Tool Declaration (Lines 93-127):
```typescript
const ragConfig: LiveConnectConfig = {
  ...newConfig,
  tools: [
    {
      functionDeclarations: [
        {
          name: "vector_search",
          description: "Search company internal documents...",
          parameters: {
            type: "object",
            properties: {
              query: { type: "string", description: "..." }
            },
            required: ["query"]
          }
        },
        {
          name: "web_search",
          description: "Search the web for current information...",
          parameters: {
            type: "object",
            properties: {
              query: { type: "string", description: "..." }
            },
            required: ["query"]
          }
        }
      ]
    }
  ]
};
```

**This tells Gemini:** "Hey, you have 2 tools available: vector_search and web_search"

#### Tool Call Handler (Lines 137-214):
```typescript
const onToolCall = async (toolCall: any) => {
  const functionCalls = toolCall.functionCalls || [];
  const functionResponses = [];

  for (const fc of functionCalls) {
    const { name, args, id } = fc;
    
    // Call YOUR backend
    const response = await fetch(
      `${config.backendURL}${config.endpoints.rag.live.query}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: args.query,
          context: {
            tool_name: name,  // "vector_search" or "web_search"
            session_id: Date.now().toString(),
          }
        }),
      }
    );

    const data = await response.json();
    
    // Send result back to Gemini
    functionResponses.push({
      id,
      name,
      response: {
        result: data.response,
        sources: data.sources,
        confidence: data.confidence,
        agents_used: data.agents_used,
      }
    });
  }

  // Tell Gemini "here are the tool results"
  liveAPI.client.sendToolResponse({ functionResponses });
};

client.on('toolcall', onToolCall);
```

**Flow:**
1. User speaks: "What is Zaman Bank's remote work policy?"
2. Gemini Live hears this and decides: "I need to use vector_search"
3. Gemini emits `toolcall` event with: `{ name: "vector_search", args: { query: "remote work policy" } }`
4. Hook intercepts this and POSTs to `/api/rag/live/query`
5. Backend executes the search
6. Hook sends results back to Gemini
7. Gemini speaks the response to the user

---

### 2. Backend: Live Query Router

**File:** `backend/rag_agent/routes/live_query_router.py`

#### Architecture Decision: Direct Tool Routing (Not Full LangGraph)

```python
@router.post("/query", response_model=LiveQueryResponse)
async def live_query(request: LiveQueryRequest):
    tool_name = request.context.get("tool_name", "vector_search")
    query = request.query
    
    # DIRECT TOOL ROUTING (no supervisor agent)
    if tool_name == "vector_search":
        vector_tool = get_vector_search_tool()
        response_text = vector_tool.search(
            query=query,
            k=3,
            use_reranking=True,
            use_hyde=True,
            use_hybrid=True
        )
        agents_used.append("vector_search")
        
    elif tool_name == "web_search":
        web_tool = get_web_search_tool()
        response_text = web_tool.search(
            query=query,
            max_results=3,
            search_depth="advanced"
        )
        agents_used.append("web_search")
    
    return LiveQueryResponse(
        response=response_text,
        sources=sources,
        confidence=confidence,
        agents_used=agents_used,
        status="success"
    )
```

#### Why Direct Routing Instead of Supervisor Agent?

**Current Design:**
- ✅ **Fast**: Direct tool call, no LLM reasoning overhead
- ✅ **Predictable**: Gemini already decided which tool to use
- ✅ **Simple**: No complex agent orchestration needed
- ❌ **Limited**: Can't combine multiple tools
- ❌ **No Banking**: No access to transaction/account tools

**Why Gemini Decides (Not Your Supervisor):**
- Gemini Live AI sees the user's voice/video/screen input
- Gemini reads the tool descriptions you provided
- Gemini decides: "This question needs vector_search"
- Gemini calls the tool
- Your backend **executes** the tool
- You send results back
- Gemini **synthesizes** the final response with voice

**This is MIDDLEWARE PATTERN:**
```
User Speech 
  → Gemini Live (decides which tool) 
  → Your Backend (executes tool) 
  → Results back to Gemini 
  → Gemini speaks response
```

---

### 3. Comparison: Live vs Regular RAG

| Aspect | Gemini Live `/api/rag/live/query` | Regular RAG `/api/rag/query` | Transaction RAG `/api/rag/transaction/query` |
|--------|-----------------------------------|------------------------------|---------------------------------------------|
| **Decision Maker** | Gemini Live AI | Your Supervisor Agent | Your Supervisor Agent |
| **Tool Routing** | Direct (predetermined by Gemini) | LangGraph orchestration | LangGraph orchestration |
| **Tools Available** | 2 (vector, web) | 2 (vector, web) | 26 (all tools) |
| **Agent Used** | None (middleware) | Supervisor Agent | Supervisor Agent |
| **Context Setting** | ❌ No | ❌ No | ✅ Yes (all contexts) |
| **Database Access** | ❌ No | ❌ No | ✅ Yes |
| **Banking Operations** | ❌ Can't do | ❌ Can't do | ✅ Full access |
| **Response Generation** | Gemini Live AI | Your Supervisor Agent | Your Supervisor Agent |
| **Voice Output** | ✅ Yes (multimodal) | ❌ No | ❌ No |
| **Use Case** | Voice conversations about knowledge | Text chat about knowledge | **Full banking + knowledge** |

---

## 🎯 What "Live is Middleware" Means

### Current Architecture:

```python
# live_query_router.py is a THIN LAYER that:

1. Receives tool call from Gemini ──► { tool_name: "vector_search", query: "..." }
2. Routes to tool directly      ──► get_vector_search_tool().search(query)
3. Returns results              ──► { response: "...", sources: [...] }
4. Gemini synthesizes voice     ──► 🔊 "According to company policy..."
```

**It's middleware because:**
- ❌ Doesn't use your Supervisor Agent
- ❌ Doesn't do multi-tool orchestration
- ❌ Doesn't have reasoning capabilities
- ✅ Just executes what Gemini tells it to execute
- ✅ Acts as a bridge between Gemini and your tools

---

## 🔧 How Regular AI Chat (Explore.tsx) Works

**File:** `frontend/app/(tabs)/explore.tsx`

```typescript
// Line 108: Uses TRANSACTION endpoint (has all 26 tools)
const response = await fetch(`${config.backendURL}/api/rag/transaction/query`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  },
  body: JSON.stringify({
    query: userMessage.content,
    user_id: userId,  // ← Provides user context
    context: { session_id: sessionId },
    environment: 'production'
  })
});
```

**Backend Flow:**
```python
# transaction_router.py

1. Set ALL contexts:
   set_transaction_context(user_id=request.user_id, db=db)
   set_account_context(user_id=request.user_id, db=db)
   set_transaction_history_context(user_id, db)
   set_product_context(user_id, db)
   set_cart_context(user_id, db)

2. Initialize RAG system:
   rag_system.initialize(environment=request.environment)

3. Query with supervisor:
   result = rag_system.query(
       user_query=request.query,
       context=context
   )
   # Supervisor agent has access to ALL 26 tools
   # Can call: get_account_balance, deposit_money, transfer_money, etc.

4. Return response with transaction status
```

**This is FULL RAG with Agent Orchestration:**
```
User Text
  → Transaction Router (sets context)
  → RAG System
  → Supervisor Agent (decides which tools)
  → Execute tools (can access DB)
  → Agent synthesizes response
  → Return to user
```

---

## 🏗️ Agent Configuration Deep Dive

**File:** `backend/rag_agent/config/langraph.py`

### Supervisor Agent Configuration (Lines 27-74):

```python
class SupervisorAgentConfig(AgentConfig):
    name: str = "supervisor"
    description: str = "Orchestrates and delegates tasks to specialized agents"
    tools: List[str] = ["vector_search", "web_search"]
    
    system_prompt: str = """
You are an intelligent RAG assistant for ZAMAN BANK.

=== CRITICAL PRIORITY RULES ===
🎯 ALWAYS TRY vector_search FIRST for ANY query related to Zaman Bank
🎯 ONLY use web_search if vector_search returns insufficient results

=== AVAILABLE TOOLS ===
1. vector_search (PRIORITY #1):
   - Use for: ALL questions about Zaman Bank, company policies, internal documents
   
2. web_search (FALLBACK ONLY):
   - Use ONLY if vector_search doesn't provide sufficient information

=== DECISION WORKFLOW ===
1. ALWAYS start with vector_search for ANY query
2. If vector_search provides good results → Use those results
3. If vector_search results are insufficient → THEN consider web_search
"""
```

### Agent Creation (Lines 165-183):

```python
class AgentFactory:
    def create_agent(self, agent_type: str, llm: Any, **overrides) -> Any:
        config_class = self._agent_types[agent_type]
        config = config_class(**overrides)
        
        # Get tools for this agent
        tools = self.tool_registry.get_tools(config.tools)
        
        # Create a real LangGraph ReAct agent
        return create_react_agent(
            llm,
            tools=tools,
            prompt=config.system_prompt,
            name=config.name
        )
```

**This creates a TRUE LangGraph ReAct Agent:**
- ✅ Has reasoning capabilities
- ✅ Can decide which tool(s) to use
- ✅ Can use multiple tools in sequence
- ✅ Synthesizes final response

---

## 🔄 RAG System Orchestration

**File:** `backend/rag_agent/config/orchestrator.py`

```python
class RAGSystem:
    def initialize(self, environment: str = "development"):
        # Initialize supervisor agent
        self.supervisor_agent = self.config.get_supervisor_agent()
        
        # Initialize specialist agents
        for agent_type in ["local_knowledge", "web_search"]:
            self.specialist_agents[agent_type] = self.config.get_specialist_agent(agent_type)
    
    def query(self, user_query: str, context: Optional[Dict[str, Any]] = None):
        # Process through supervisor agent
        response = self.supervisor_agent.invoke({
            "messages": [HumanMessage(content=user_query)]
        })
        
        # LangGraph returns: {"messages": [HumanMessage, AIMessage, ToolMessage, ...]}
        # Extract response and sources
        
        return {
            "query": user_query,
            "response": response_content,
            "sources": sources,
            "confidence": 0.8
        }
```

**LangGraph Flow:**
```
User Query
  ↓
Supervisor Agent receives HumanMessage
  ↓
Agent reasons: "I need to search company docs"
  ↓
Agent calls: vector_search(query="...")
  ↓
Tool executes and returns ToolMessage
  ↓
Agent receives results
  ↓
Agent reasons: "I have enough info" or "I need web_search too"
  ↓
Agent generates final AIMessage response
  ↓
Return to user
```

---

## 📊 Comparison Table: All Three Systems

| Feature | Live Query Router | Main RAG Router | Transaction RAG Router |
|---------|------------------|-----------------|----------------------|
| **File** | `live_query_router.py` | `router.py` | `transaction_router.py` |
| **Endpoint** | `/api/rag/live/query` | `/api/rag/query` | `/api/rag/transaction/query` |
| **Used By** | Gemini Live (voice chat) | Not currently used | Explore chat (text) |
| **Tool Count** | 2 | 2 | **26** |
| **Uses RAG System** | ❌ No (direct routing) | ✅ Yes | ✅ Yes |
| **Uses Supervisor** | ❌ No | ✅ Yes | ✅ Yes |
| **Uses LangGraph** | ❌ No | ✅ Yes | ✅ Yes |
| **Tool Decision** | Gemini Live AI | Supervisor Agent | Supervisor Agent |
| **Context Setting** | ❌ None | ❌ None | ✅ All 5 contexts |
| **Database Access** | ❌ No | ❌ No | ✅ Yes |
| **Banking Ops** | ❌ No | ❌ No | ✅ Yes |
| **Multimodal** | ✅ Yes (voice/video) | ❌ No | ❌ No |
| **Response Voice** | Gemini synthesizes | N/A | N/A |
| **Speed** | Fast (direct) | Medium (agent) | Medium (agent) |
| **Capability** | Knowledge only | Knowledge only | **Full banking** |

---

## 🚀 What This Means for Your System

### Current State:

#### 1. **Gemini Live (Voice Chat)**
- **Purpose:** Multimodal conversation about company knowledge
- **Strength:** Voice/video/screen interaction
- **Limitation:** No banking operations
- **Architecture:** Gemini makes decisions → Your backend executes → Gemini responds

#### 2. **Explore Chat (Text Chat)**
- **Purpose:** Full banking operations via text
- **Strength:** Access to all 26 tools
- **Limitation:** Text only, no voice
- **Architecture:** Your Supervisor Agent makes all decisions

### The Pipeline Difference:

```
GEMINI LIVE PIPELINE:
User Voice → Gemini AI → Tool Call → Your Backend (executes) → Results → Gemini → Voice Response
         [Gemini decides]                [You execute]           [Gemini synthesizes]

EXPLORE CHAT PIPELINE:
User Text → Your Backend → Supervisor Agent → Tool Calls → Database → Response → User
                      [Your agent decides]     [Your agent executes]  [Your agent synthesizes]
```

---

## 💡 Key Insights

### 1. **Gemini Live is NOT using your Supervisor Agent**
- Gemini Live AI is the "supervisor"
- Your backend is just a tool executor
- This is by design for real-time voice interaction

### 2. **Live Query Router is Intentionally Simple**
- Direct routing = lower latency
- Gemini already decided which tool to use
- No need for agent reasoning overhead

### 3. **Transaction Router is the Full System**
- Uses Supervisor Agent for decisions
- Has all 26 tools registered
- Can perform banking operations
- This is your "production RAG system"

### 4. **Tool Registration Happens in LangGraph Config**
```python
# langraph.py defines what tools each agent type can access
SupervisorAgentConfig.tools = ["vector_search", "web_search"]

# But when used via transaction_router, ALL contexts are set
# So tools like get_account_balance() can access the database
```

---

## 🎯 Recommendations

### Option 1: Keep Current Architecture (Recommended)
- **Gemini Live:** Knowledge Q&A with voice (current)
- **Explore Chat:** Full banking with text (current)
- **Benefit:** Each system optimized for its use case

### Option 2: Upgrade Gemini Live to Full Banking
To give Gemini Live access to banking tools, you would need to:

1. **Update Tool Declarations** (frontend):
```typescript
// use-live-api-with-rag.ts
functionDeclarations: [
  { name: "vector_search", ... },
  { name: "web_search", ... },
  { name: "get_account_balance", ... },  // Add 24 more
  { name: "deposit_money", ... },
  // ... all 26 tools
]
```

2. **Route to Transaction Endpoint**:
```typescript
const response = await fetch(
  `${config.backendURL}/api/rag/transaction/query`,  // Change from live/query
  {
    method: 'POST',
    body: JSON.stringify({
      query: args.query,
      user_id: userId,  // Need user context
      context: { tool_name: name }
    })
  }
);
```

3. **Challenges:**
- Need to pass user authentication to Gemini Live
- Tool response format more complex
- Latency may increase (agent reasoning)
- Voice confirmation for transactions?

---

## 📝 Summary

### Your Initial Question:
> "The main pipeline was to take the input from the RAG Live Query and send it there"

### Answer:
**YES and NO:**

- **YES:** Gemini Live DOES call `/api/rag/live/query` 
- **BUT:** This endpoint is a **simplified middleware**
- **IT DOES NOT:** Use your full RAG system (rag_system.query)
- **IT DOES:** Direct routing to vector_search or web_search

### The Real "Main Pipeline":
The **transaction router** (`/api/rag/transaction/query`) is your **main RAG pipeline** because it:
- ✅ Uses the full RAG system
- ✅ Uses Supervisor Agent
- ✅ Uses LangGraph orchestration
- ✅ Has all 26 tools
- ✅ Can perform banking operations

### Gemini Live's Role:
Gemini Live is a **specialized interface** for multimodal interaction:
- Gemini provides: Voice, video, screen understanding, natural conversation
- Your backend provides: Company knowledge, web search
- Together: Voice-enabled knowledge assistant

### Explore Chat's Role:
Explore chat is your **full-featured RAG assistant**:
- Uses your Supervisor Agent for all decisions
- Has access to all banking tools
- Can perform transactions
- Text-based interface

---

## 🔧 Configuration Files Reference

| File | Purpose |
|------|---------|
| `frontend/hooks/use-live-api-with-rag.ts` | Gemini Live integration with RAG tools |
| `frontend/app/(tabs)/live-chat.tsx` | Live voice chat UI |
| `frontend/app/(tabs)/explore.tsx` | Text chat UI (uses transaction endpoint) |
| `backend/rag_agent/routes/live_query_router.py` | Middleware for Gemini Live tool calls |
| `backend/rag_agent/routes/router.py` | Basic RAG endpoint |
| `backend/rag_agent/routes/transaction_router.py` | **Full banking RAG endpoint** ⭐ |
| `backend/rag_agent/config/langraph.py` | Agent configurations and tool registry |
| `backend/rag_agent/config/orchestrator.py` | RAG system orchestrator |
| `backend/rag_agent/config/langchain.py` | LLM configurations |

---

## ✅ Your System is Well-Architected!

You have:
- ✅ Separation of concerns (Live vs Transaction)
- ✅ Proper middleware pattern for Gemini Live
- ✅ Full LangGraph orchestration for complex queries
- ✅ All 26 tools properly registered
- ✅ Context management for banking operations
- ✅ Multi-agent support (Supervisor + Specialists)

The architecture makes sense for the different use cases! 🎉

