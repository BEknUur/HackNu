# 🔍 RAG Live Query Architecture Analysis

## Executive Summary

Your system has **TWO different RAG pipelines** with different capabilities:
1. **Live Chat**: Gemini-controlled tool calling → Simple tool executor
2. **Explore Chat**: User query → Full RAG orchestrator with agent reasoning

**The Goal**: Make Live Chat use the same powerful agent orchestration as Explore Chat.

---

## Current Architecture

### 1. Frontend Components

#### A. Live Chat (`/live-chat`)
```
User Voice → Gemini Live API → Tool Calls → Frontend Hook → Backend Tool Executor
```

**Flow:**
1. User speaks to microphone
2. Gemini Live API transcribes + understands
3. Gemini decides to call `vector_search` or `web_search`
4. `useLiveAPIWithRAG` hook intercepts tool call
5. Sends to `/api/rag/live/query` with tool_name
6. Gets simple tool result back
7. Sends to Gemini to synthesize speech

**Limitations:**
- Gemini controls which tool to use
- No agent orchestration
- No access to transaction tools
- Simple 1-tool-per-query execution

#### B. Explore Chat (`/explore`)
```
User Text → Backend RAG Orchestrator → LangGraph Agents → Multiple Tools → Intelligent Response
```

**Flow:**
1. User types message
2. Sent directly to `/api/rag/transaction/query`
3. RAG Supervisor Agent receives query
4. Agent reasons and decides strategy
5. Agent can call MULTIPLE tools in sequence
6. Agent synthesizes final answer
7. Response includes sources, agents used, confidence

**Advantages:**
- Full agent reasoning
- Access to ALL tools (vector, web, transactions, accounts, products)
- Multi-step tool execution
- Intelligent routing and fallbacks
- Source attribution

---

### 2. Backend Routes

#### A. Live Query Route (`/api/rag/live/query`)

**Location**: `backend/rag_agent/routes/live_query_router.py`

**Purpose**: Simple tool executor for Gemini Live API

**How it works:**
```python
@router.post("/query")
async def live_query(request: LiveQueryRequest):
    tool_name = request.context.get("tool_name", "vector_search")
    
    if tool_name == "vector_search":
        vector_tool = get_vector_search_tool()
        response = vector_tool.search(query=query)
    elif tool_name == "web_search":
        web_tool = get_web_search_tool()
        response = web_tool.search(query=query)
    
    return response
```

**Characteristics:**
- ❌ No LangGraph agent
- ❌ No multi-tool reasoning
- ❌ No transaction capabilities
- ✅ Fast and simple
- ✅ Direct tool execution

---

#### B. Transaction Query Route (`/api/rag/transaction/query`)

**Location**: `backend/rag_agent/routes/transaction_router.py`

**Purpose**: Full RAG system with agent orchestration + transaction capabilities

**How it works:**
```python
@router.post("/query")
async def query_with_transactions(request: TransactionQueryRequest):
    # Set all contexts (user_id, db session, etc.)
    set_transaction_context(user_id=request.user_id, db=db)
    set_account_context(user_id=request.user_id, db=db)
    set_product_context(user_id=request.user_id, db=db)
    # ... more contexts
    
    # Initialize orchestrator if needed
    if not rag_system.supervisor_agent:
        rag_system.initialize(environment=request.environment)
    
    # Let the agent orchestrate
    result = rag_system.query(
        user_query=request.query,
        context=context
    )
    
    return result  # Includes: response, sources, confidence, agents_used
```

**Characteristics:**
- ✅ Full LangGraph agent orchestration
- ✅ Supervisor agent + specialist agents
- ✅ Multi-tool reasoning
- ✅ Access to ALL tools:
  - `vector_search` (internal docs)
  - `web_search` (internet)
  - `get_account_info`
  - `get_transaction_history`
  - `deposit_money`
  - `withdraw_money`
  - `transfer_money`
  - `purchase_product`
  - `get_products`
  - `get_cart`
- ✅ Intelligent routing
- ✅ Source attribution
- ✅ Confidence scoring

---

#### C. Regular Query Route (`/api/rag/query`)

**Location**: `backend/rag_agent/routes/router.py`

**Purpose**: Basic RAG without transactions (legacy/simple queries)

**Characteristics:**
- ✅ LangGraph agent orchestration
- ✅ vector_search + web_search
- ❌ No transaction tools
- ❌ No user context

---

### 3. Agent Orchestration (LangGraph)

**Location**: `backend/rag_agent/config/langraph.py`

**Agents Configured:**

1. **Supervisor Agent**
   - Orchestrates and delegates
   - Has access to ALL tools
   - Makes intelligent routing decisions
   - System prompt with priority rules:
     ```
     🎯 ALWAYS TRY vector_search FIRST
     🎯 ONLY use web_search if vector_search insufficient
     🎯 NEVER use web_search for internal info
     ```

2. **Local Knowledge Agent**
   - Specialist in company documents
   - Only has `vector_search` tool

3. **Web Search Agent**
   - Specialist in internet searches
   - Only has `web_search` tool

**How it works:**
```python
class SupervisorAgentConfig:
    tools = ["vector_search", "web_search", "deposit_money", ...]
    system_prompt = """
    You are an intelligent RAG assistant.
    ALWAYS start with vector_search...
    """

# In orchestrator:
supervisor_agent = create_react_agent(
    llm,
    tools=all_tools,
    prompt=config.system_prompt,
    name="supervisor"
)

# Query processing:
result = supervisor_agent.invoke({
    "messages": [HumanMessage(content=user_query)]
})
```

---

## The Problem

Live Chat uses Gemini's tool calling → simple executor, missing out on:
- Agent reasoning
- Multi-tool orchestration
- Transaction capabilities
- Intelligent fallbacks
- Source attribution

---

## The Solution

### Proposed Architecture Change

**Make Live Chat a voice wrapper around the full RAG orchestrator**

#### New Flow:
```
User Voice 
  ↓
Gemini Live (STT)
  ↓
Frontend extracts text
  ↓
Send to /api/rag/transaction/query (SAME AS EXPLORE)
  ↓
Full RAG Orchestrator with agents
  ↓
Response back to frontend
  ↓
Gemini Live (TTS)
  ↓
User hears response
```

#### Key Changes:

1. **Frontend (`use-live-api-with-rag.ts`)**:
   ```typescript
   // BEFORE: Listen for Gemini tool calls
   liveAPI.client.on('toolcall', onToolCall);
   
   // AFTER: Listen for user messages, send to RAG
   liveAPI.client.on('message', async (message) => {
     const userText = message.text;
     
     // Send to full RAG orchestrator
     const response = await fetch(`${config.backendURL}/api/rag/transaction/query`, {
       method: 'POST',
       body: JSON.stringify({
         query: userText,
         user_id: currentUserId,
         environment: 'production'
       })
     });
     
     const ragResult = await response.json();
     
     // Send response back to Gemini to speak
     liveAPI.client.send({ text: ragResult.response });
   });
   ```

2. **Remove Tool Declarations**:
   - Don't send `vector_search` and `web_search` as tools to Gemini
   - Gemini becomes pure STT/TTS interface
   - All intelligence handled by RAG orchestrator

3. **Benefits**:
   - ✅ Same logic as Explore chat
   - ✅ Access to ALL tools
   - ✅ Agent orchestration
   - ✅ Transaction capabilities
   - ✅ Multi-tool reasoning
   - ✅ Consistent behavior across text and voice
   - ✅ Easier to maintain (one RAG logic)

---

## Tool Inventory

### Available to Transaction Router (`/api/rag/transaction/query`):

#### Document & Web Tools:
1. **vector_search** - Internal knowledge base
2. **web_search** - Internet search

#### Account Tools:
3. **get_account_info** - Get user's account details
4. **get_all_accounts** - List all user accounts

#### Transaction Tools:
5. **deposit_money** - Add money to account
6. **withdraw_money** - Remove money from account
7. **transfer_money** - Send between accounts
8. **get_transaction_history** - View past transactions

#### Product Tools:
9. **get_products** - Browse available products
10. **get_product_by_id** - Get specific product
11. **purchase_product** - Buy a product

#### Cart Tools:
12. **get_cart** - View shopping cart
13. **add_to_cart** - Add item to cart
14. **remove_from_cart** - Remove item
15. **clear_cart** - Empty cart
16. **checkout_cart** - Complete purchase

**Total**: 16 intelligent tools orchestrated by LangGraph agents

---

## Implementation Steps

### Phase 1: Modify Live Chat Hook ✅

**File**: `frontend/hooks/use-live-api-with-rag.ts`

```typescript
export function useLiveAPIWithRAG(options: LiveClientOptions): UseLiveAPIWithRAGResults {
  const liveAPI = useLiveAPI(options);
  const [currentUserId, setCurrentUserId] = useState(1);

  // Remove tool declarations setup
  // Remove tool call handler

  // Add message interceptor
  useEffect(() => {
    const onMessage = async (message: any) => {
      if (message.role === 'user') {
        // User spoke something
        const userQuery = message.text;
        
        try {
          // Send to full RAG orchestrator
          const response = await fetch(
            `${config.backendURL}/api/rag/transaction/query`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                query: userQuery,
                user_id: currentUserId,
                environment: 'production'
              }),
            }
          );

          const ragResult = await response.json();
          
          // Send RAG response back to Gemini to speak
          liveAPI.client.send({
            text: ragResult.response,
            end_of_turn: true
          });
          
          console.log('[RAG] Full orchestration:', {
            agents_used: ragResult.agents_used,
            sources: ragResult.sources,
            confidence: ragResult.confidence
          });
        } catch (error) {
          console.error('[RAG] Error:', error);
        }
      }
    };

    liveAPI.client.on('message', onMessage);
    return () => liveAPI.client.off('message', onMessage);
  }, [liveAPI.client, currentUserId]);

  return {
    ...liveAPI,
    setCurrentUserId,
  };
}
```

### Phase 2: Update Live Chat Component ✅

**File**: `frontend/app/(tabs)/live-chat.tsx`

- Add user ID state (get from AsyncStorage)
- Pass user ID to hook
- Show agent metadata in UI (which agents were used)
- Display sources if available

### Phase 3: Test Flow ✅

1. Start backend with all tools initialized
2. Open Live Chat
3. Speak: "What is Zaman Bank's remote work policy?"
4. Expected:
   - Voice transcribed
   - Sent to RAG orchestrator
   - Supervisor agent uses vector_search
   - Response synthesized
   - Spoken back to user
   - UI shows: agents_used = ["supervisor", "vector_search"]

5. Speak: "Deposit $500 to my account"
6. Expected:
   - Orchestrator uses get_account_info + deposit_money
   - Transaction executed
   - Response confirms deposit
   - UI shows: agents_used = ["supervisor"], transaction_executed = true

### Phase 4: Enhance with Context ✅

Add conversation history, session management, and user preferences.

---

## Comparison Table

| Feature | Live Query (Old) | Transaction Query (New) |
|---------|------------------|-------------------------|
| **Agent Orchestration** | ❌ None | ✅ Full LangGraph |
| **Tool Access** | 2 tools | 16+ tools |
| **Multi-step Reasoning** | ❌ No | ✅ Yes |
| **Transactions** | ❌ No | ✅ Yes |
| **Account Access** | ❌ No | ✅ Yes |
| **Source Attribution** | ⚠️ Basic | ✅ Full |
| **Confidence Scores** | ⚠️ Simple | ✅ Intelligent |
| **User Context** | ❌ No | ✅ Yes |
| **Consistency with Text Chat** | ❌ Different | ✅ Same Logic |

---

## Conclusion

By routing Live Chat queries through `/api/rag/transaction/query` instead of the simple tool executor, you get:

1. **Unified Intelligence**: Same agent logic for text and voice
2. **Full Capabilities**: Access to all 16 tools
3. **Better UX**: Consistent behavior across interfaces
4. **Easier Maintenance**: One RAG system to improve
5. **Future-Proof**: Easy to add more tools/agents

**Gemini Live becomes just the interface (STT + TTS), while your RAG orchestrator is the brain** 🧠

---

## Next Steps

1. ✅ Implement message interception in `use-live-api-with-rag.ts`
2. ✅ Test with simple queries
3. ✅ Test with transaction queries
4. ✅ Add conversation history
5. ✅ Add user metadata display
6. ✅ Consider deprecating `/api/rag/live/query` (no longer needed)

