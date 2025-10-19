# 🗺️ API Architecture Map - Zaman Bank RAG System

## Overview
Complete mapping of all APIs, services, and integrations used in the RAG tools.

---

## 🚨 **IMPORTANT: 3 RAG Endpoints - Which One Has Your 26 Tools?**

### ⚠️ Summary:
| Endpoint | Tools | Purpose |
|----------|-------|---------|
| `/api/rag/query` | 2 tools | Basic knowledge Q&A |
| `/api/rag/live/query` | 2 tools | Gemini Live voice chat (knowledge only) |
| **`/api/rag/transaction/query`** | **26 tools** | **FULL banking system with ALL tools** ⭐ |

**Only `/api/rag/transaction/query` has access to your 26 banking tools!**

See detailed comparison: [RAG_ENDPOINTS_COMPARISON.md](./RAG_ENDPOINTS_COMPARISON.md)

---

## 📊 **EXTERNAL APIs**

### 1. **Google Gemini API** 🤖
- **Purpose**: AI/LLM processing and embeddings
- **Used In**: 
  - Vector Search Tool (embeddings)
  - Main LLM for Supervisor Agent
- **API Key**: `GOOGLE_API_KEY` (from .env)
- **Models Used**:
  - `models/gemini-2.0-flash-exp` - Main LLM
  - `models/embedding-001` - Text embeddings
- **Endpoint**: Google AI Platform
- **Cost**: Pay-per-use

### 2. **Tavily Search API** 🌐
- **Purpose**: Web search for current information
- **Used In**: Web Search Tool
- **API Key**: `TAVILY_API_KEY` (from .env)
- **Features**:
  - Basic search
  - Advanced search (deeper crawling)
  - Configurable max results
- **Endpoint**: `https://tavily.com/`
- **Cost**: Free tier + paid plans

---

## 🏦 **INTERNAL SERVICE APIs**

All internal services are located in `/backend/services/` and accessed via database operations.

### 3. **Account Service API** 💰
- **File**: `/backend/services/account/service.py`
- **Database**: PostgreSQL (hacknu database)
- **Used By Tools**:
  - `get_account_balance`
  - `get_my_accounts`
  - `get_account_details`
  - `checkout_cart` (for payment)
- **Operations**:
  - `get_account(account_id, db)` - Get single account
  - `get_user_accounts(user_id, db)` - Get all user accounts
  - Update balance for transactions
- **Tables**: `accounts`

### 4. **Transaction Service API** 💳
- **File**: `/backend/services/transaction/service.py`
- **Database**: PostgreSQL (hacknu database)
- **Used By Tools**:
  - `deposit_money`
  - `withdraw_money`
  - `transfer_money`
  - `get_my_transactions`
  - `get_transaction_stats`
  - `get_account_transactions`
  - `get_transaction_details`
- **Operations**:
  - Create deposits/withdrawals/transfers
  - Query transaction history
  - Calculate statistics
  - Filter transactions
- **Tables**: `transactions`

### 5. **Product Service API** 🛍️
- **File**: `/backend/services/product/service.py`
- **Database**: PostgreSQL (hacknu database)
- **Used By Tools**:
  - `search_products`
  - `get_product_details`
  - `get_products_by_category`
  - `get_featured_products`
  - `add_to_cart` (validation)
  - `checkout_cart` (order creation)
- **Operations**:
  - Search products by name/description
  - Filter by category
  - Get featured items
  - Check stock availability
- **Tables**: `products`

### 6. **Cart Service API** 🛒
- **File**: `/backend/services/cart/service.py`
- **Database**: PostgreSQL (hacknu database)
- **Used By Tools**:
  - `add_to_cart`
  - `get_my_cart`
  - `remove_from_cart`
  - `checkout_cart`
  - `clear_cart`
- **Operations**:
  - CRUD operations on cart
  - Calculate cart totals
  - Process checkout
  - Validate items
- **Tables**: `cart_items`

---

## 🔧 **RAG INFRASTRUCTURE**

### 7. **Vector Store (FAISS)** 📚
- **Type**: Local file-based vector database
- **Location**: `/backend/rag_agent/data/vector_store/`
- **Technology**: FAISS (Facebook AI Similarity Search)
- **Used By**: Vector Search Tool
- **Purpose**: Store and search document embeddings
- **Features**:
  - Semantic search
  - HyDE (Hypothetical Document Embeddings)
  - Hybrid search (BM25 + Vector)
  - AI reranking
- **Data Source**: PDF documents in `/backend/rag_agent/documents/`

### 8. **PostgreSQL Database** 🗄️
- **Host**: `postgres` (Docker service)
- **Port**: `5433:5432`
- **Database**: `hacknu`
- **Credentials**: postgres/postgres
- **URL**: `postgresql://postgres:postgres@postgres:5432/hacknu`
- **Tables**:
  - `users` - User accounts
  - `accounts` - Bank accounts
  - `transactions` - Financial transactions
  - `products` - E-commerce products
  - `cart_items` - Shopping cart
  - `financial_goals` - User financial goals

---

## 🎯 **TOOL → API MAPPING**

| Tool Category | Tool Name | External APIs | Internal Services | Database Tables |
|---------------|-----------|---------------|-------------------|-----------------|
| **RAG** | vector_search | Google Embeddings | - | FAISS vector store |
| **RAG** | web_search | Tavily API | - | - |
| **Account** | get_account_balance | - | Account Service | accounts |
| **Account** | get_my_accounts | - | Account Service | accounts |
| **Account** | get_account_details | - | Account Service | accounts |
| **Transaction** | deposit_money | - | Transaction Service | transactions, accounts |
| **Transaction** | withdraw_money | - | Transaction Service | transactions, accounts |
| **Transaction** | transfer_money | - | Transaction Service | transactions, accounts |
| **Transaction** | purchase_product | - | Transaction Service | transactions, accounts, products |
| **History** | get_my_transactions | - | Transaction Service | transactions |
| **History** | get_transaction_stats | - | Transaction Service | transactions |
| **History** | get_account_transactions | - | Transaction Service | transactions |
| **History** | get_transaction_details | - | Transaction Service | transactions |
| **Product** | search_products | - | Product Service | products |
| **Product** | get_product_details | - | Product Service | products |
| **Product** | get_products_by_category | - | Product Service | products |
| **Product** | get_featured_products | - | Product Service | products |
| **Cart** | add_to_cart | - | Cart + Product Services | cart_items, products |
| **Cart** | get_my_cart | - | Cart + Product Services | cart_items, products |
| **Cart** | remove_from_cart | - | Cart Service | cart_items |
| **Cart** | checkout_cart | - | Cart + Product + Account Services | cart_items, products, accounts, transactions |
| **Cart** | clear_cart | - | Cart Service | cart_items |

---

## 🔄 **DATA FLOW**

### Example: "How much money do I have?"

```
1. Frontend (explore.tsx)
   ↓ POST /api/rag/transaction/query
   ↓ Body: { query: "How much money do I have?", user_id: 1 }
   
2. Backend (transaction_router.py)
   ↓ Set tool contexts (user_id, db session)
   ↓ Call rag_system.query()
   
3. RAG System (orchestrator.py)
   ↓ Supervisor Agent analyzes query
   ↓ Decides to use "get_my_accounts" tool
   
4. Tool (account_tools.py)
   ↓ Reads _account_context (user_id, db)
   ↓ Calls account_service.get_user_accounts(user_id, db)
   
5. Service (services/account/service.py)
   ↓ Query PostgreSQL: SELECT * FROM accounts WHERE user_id = 1
   ↓ Returns account list
   
6. Tool formats response
   ↓ "You have 2 accounts: Account #1 (Checking): 10995.00 USD..."
   
7. Supervisor Agent
   ↓ Synthesizes final response
   
8. Backend returns JSON
   ↓ { response: "...", sources: [...], confidence: 0.8 }
   
9. Frontend displays answer
```

---

## 💡 **KEY INSIGHTS**

### ✅ What's Working:
- **26 tools** fully implemented and registered
- **2 external APIs** (Google, Tavily) properly configured
- **5 internal services** for database operations
- **Context system** for passing user_id and db session to tools
- **Multi-agent system** with Supervisor coordinating specialist agents

### ❌ Current Issues:
- **Database empty** - No users registered yet
- **Tools can't access data** until users exist in DB
- Frontend must register/login first to create users

### 🚀 Architecture Strengths:
- **Separation of concerns**: Tools → Services → Database
- **Reusable services**: Same services used by REST API and RAG tools
- **Flexible tool registration**: Easy to add new tools
- **Context injection**: Tools get user_id without exposing sensitive data

---

## 📝 **CONFIGURATION CHECKLIST**

### Environment Variables Required:
```bash
# External APIs
GOOGLE_API_KEY=AIzaSy...         # ✅ Set in .env
TAVILY_API_KEY=tvly-dev-...      # ✅ Set in .env

# Database
POSTGRES_USER=postgres            # ✅ Set in .env
POSTGRES_PASSWORD=postgres        # ✅ Set in .env
POSTGRES_DB=hacknu               # ✅ Set in .env
DATABASE_URL=postgresql://...    # ✅ Set in .env
```

### Services Status:
- ✅ PostgreSQL running (port 5433)
- ✅ Backend API running (port 8000)
- ✅ Frontend running (port 8081)
- ✅ Vector store initialized
- ❌ Database needs user data (register via frontend)

---

## 🎬 **NEXT STEPS**

1. **Register User** → Creates user in `users` table
2. **Login** → Creates account in `accounts` table with initial balance
3. **Ask AI** → "How much money do I have?" will now work!
4. **Tools will access**:
   - User from `users` table
   - Accounts from `accounts` table
   - Returns actual balance

---

## 📚 **API DOCUMENTATION**

### External API Docs:
- Google Gemini: https://ai.google.dev/docs
- Tavily Search: https://docs.tavily.com/

### Internal API Endpoints:
See Swagger UI at: http://localhost:8000/docs

### Tool Documentation:
Each tool has detailed docstrings explaining:
- Purpose
- Parameters
- Return format
- Example queries
- Error handling

---

**Last Updated**: October 19, 2025  
**Status**: ✅ All tools integrated and ready (pending user registration)
