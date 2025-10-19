# 🔍 RAG Endpoints Comparison - Which One Does What?

## The 3 RAG Endpoints Explained

You have **3 different RAG endpoints**, but they serve different purposes. Here's the breakdown:

---

## 1️⃣ **RAG** (Basic) - `/api/rag/query`

### Purpose:
**Basic RAG queries with ONLY 2 tools (vector_search, web_search)**

### File:
`/backend/rag_agent/routes/router.py`

### Tools Available:
- ✅ `vector_search` (search company documents)
- ✅ `web_search` (search the web)
- ❌ NO banking tools (no account, transaction, product, cart tools)

### When to Use:
- Simple knowledge queries
- "What is Zaman Bank's policy on X?"
- "Search the web for Y"
- NO account access needed

### Context Set:
- ❌ NO user_id
- ❌ NO database session
- ❌ NO tool contexts

### Request:
```json
POST /api/rag/query
{
  "query": "What is Zaman Bank's mission?",
  "environment": "development"
}
```

### Response:
```json
{
  "query": "What is Zaman Bank's mission?",
  "response": "Based on company documents...",
  "sources": [],
  "confidence": 0.8,
  "status": "success"
}
```

---

## 2️⃣ **RAG Live Query** - `/api/rag/live/query`

### Purpose:
**For Gemini Live voice chat - ONLY 2 tools (vector_search, web_search)**

### File:
`/backend/rag_agent/routes/live_query_router.py`

### Tools Available:
- ✅ `vector_search` (search company documents)
- ✅ `web_search` (search the web)
- ❌ NO banking tools (no account, transaction, product, cart tools)

### When to Use:
- Gemini Live voice/video chat
- Real-time conversations
- Questions about company knowledge or web info
- NO account access needed

### Context Set:
- ⚠️ Has user_id and session_id in request
- ❌ But DOES NOT set tool contexts
- ❌ Banking tools won't work

### Request:
```json
POST /api/rag/live/query
{
  "query": "What are Zaman Bank's products?",
  "user_id": "user123",
  "session_id": "session456"
}
```

### Response:
```json
{
  "query": "What are Zaman Bank's products?",
  "response": "According to our documents...",
  "sources": [],
  "confidence": 0.8,
  "agents_used": ["local_knowledge_agent"],
  "reasoning": "Used vector_search"
}
```

---

## 3️⃣ **RAG-Transactions** - `/api/rag/transaction/query` ⭐

### Purpose:
**FULL BANKING RAG with ALL 26 TOOLS!**

### File:
`/backend/rag_agent/routes/transaction_router.py`

### Tools Available:
- ✅ `vector_search` (2 RAG tools)
- ✅ `web_search`
- ✅ `get_account_balance` (26 banking tools!)
- ✅ `get_my_accounts`
- ✅ `deposit_money`
- ✅ `withdraw_money`
- ✅ `transfer_money`
- ✅ `search_products`
- ✅ `add_to_cart`
- ✅ `checkout_cart`
- ✅ **ALL 26 banking tools**

### When to Use:
- **Banking questions**: "How much money do I have?"
- **Transactions**: "Deposit $500"
- **Shopping**: "Buy iPhone 15"
- **Account management**: "Show my transactions"
- **EVERYTHING that needs user data**

### Context Set:
- ✅ user_id (numeric)
- ✅ database session
- ✅ transaction_context
- ✅ account_context
- ✅ transaction_history_context
- ✅ product_context
- ✅ cart_context
- ✅ **ALL tool contexts are set!**

### Request:
```json
POST /api/rag/transaction/query
{
  "query": "How much money do I have?",
  "user_id": 1,
  "environment": "production"
}
```

### Response:
```json
{
  "query": "How much money do I have?",
  "response": "You have $10,995 in your checking account.",
  "sources": [{"tool": "get_my_accounts", "query": {}}],
  "confidence": 0.9,
  "status": "success",
  "transaction_executed": false
}
```

---

## 🎯 **KEY DIFFERENCES**

| Feature | `/api/rag/query` | `/api/rag/live/query` | `/api/rag/transaction/query` ⭐ |
|---------|------------------|------------------------|--------------------------------|
| **Tools** | 2 (RAG only) | 2 (RAG only) | **26 (All banking tools!)** |
| **User ID** | ❌ No | ⚠️ Yes (but not used) | ✅ Yes (required) |
| **DB Session** | ❌ No | ❌ No | ✅ Yes |
| **Tool Contexts** | ❌ No | ❌ No | ✅ **YES! All set** |
| **Banking Ops** | ❌ Can't access | ❌ Can't access | ✅ **Full access** |
| **Use Case** | Knowledge Q&A | Voice chat | **Banking + Everything** |

---

## 🤔 **Your Question Answered**

### You asked:
> "I have 26 tools, but the RAG Live is just input/output. What about the transaction one?"

### Answer:
**YES! The RAG-Transactions endpoint (`/api/rag/transaction/query`) is THE ONE that uses all 26 tools!**

Here's what happens:

### 1. **Basic RAG** (`/api/rag/query`):
```python
# Only 2 tools registered
tools = ["vector_search", "web_search"]
# NO context set
# Can't access banking functions
```

### 2. **RAG Live** (`/api/rag/live/query`):
```python
# Only 2 tools registered
tools = ["vector_search", "web_search"]
# Has user_id but doesn't set contexts
# Can't access banking functions
```

### 3. **RAG-Transactions** (`/api/rag/transaction/query`) ⭐:
```python
# ALL 26 tools registered! (I added them to LangGraph config)
tools = [
    "vector_search", "web_search",
    "get_account_balance", "get_my_accounts", "get_account_details",
    "deposit_money", "withdraw_money", "transfer_money", 
    "get_my_transactions", "get_transaction_stats",
    "search_products", "get_product_details",
    "add_to_cart", "get_my_cart", "checkout_cart",
    # ... all 26 tools
]

# Sets ALL contexts:
set_transaction_context(user_id, db)
set_account_context(user_id, db)
set_transaction_history_context(user_id, db)
set_product_context(user_id, db)
set_cart_context(user_id, db)

# NOW tools can access database!
```

---

## 📊 **Visual Flow**

### Wrong Endpoint (won't work for banking):
```
User: "How much money do I have?"
  ↓
Frontend: POST /api/rag/live/query  ❌ WRONG
  ↓
Backend: Only has vector_search, web_search
  ↓
AI: "I cannot access your account information"
```

### Correct Endpoint (works!):
```
User: "How much money do I have?"
  ↓
Frontend: POST /api/rag/transaction/query  ✅ CORRECT
  ↓
Backend: Sets all tool contexts (user_id, db)
  ↓
Supervisor Agent: Has access to all 26 tools
  ↓
Calls: get_my_accounts(user_id=1)
  ↓
Tool: Reads context, queries database
  ↓
AI: "You have $10,995 in your checking account"
```

---

## ✅ **What I Fixed Today**

1. **Added ALL 26 tools** to the Supervisor Agent config in `/backend/rag_agent/config/langraph.py`
2. **Updated your frontend** (`explore.tsx`) to use `/api/rag/transaction/query` instead of `/api/rag/live/query`
3. **Tools now registered** and will work once you have users in the database

---

## 🚀 **Recommendation**

### For your Explore page (Chat with Zaman):
Use: **`/api/rag/transaction/query`** ✅

### For Gemini Live voice chat:
You should also update it to use: **`/api/rag/transaction/query`** ✅
(Currently it's limited to just knowledge Q&A)

### Keep `/api/rag/query` for:
Simple, stateless knowledge queries that don't need user context

---

## 💡 **Summary**

| Endpoint | Tools Count | Purpose | Your 26 Tools? |
|----------|-------------|---------|----------------|
| `/api/rag/query` | 2 | Basic knowledge | ❌ No |
| `/api/rag/live/query` | 2 | Voice chat (knowledge only) | ❌ No |
| **`/api/rag/transaction/query`** | **26** | **Full banking system** | **✅ YES!** |

**The RAG-Transactions endpoint IS the one that uses your 26 tools!** 🎉

The other two endpoints only have 2 tools (vector_search, web_search) because they don't set the tool contexts needed for banking operations.
