# 📊 Quick API Reference - Zaman Bank RAG Tools

## External APIs Being Used

### 1️⃣ **Google Gemini API** 🤖
```
Purpose: AI/LLM + Embeddings
API Key: GOOGLE_API_KEY (in .env)
Used By: 
  - Supervisor Agent (main LLM)
  - Vector Search (embeddings)
Cost: Pay-per-use
```

### 2️⃣ **Tavily Search API** 🌐
```
Purpose: Web search
API Key: TAVILY_API_KEY (in .env)
Used By: Web Search Tool
Cost: Free tier available
```

---

## Internal Services (Database Operations)

All internal services connect to PostgreSQL database `hacknu`:

### 🏦 Account Service
```python
from services.account import service as account_service

# Operations:
account_service.get_account(account_id, db)
account_service.get_user_accounts(user_id, db)
# Used by: get_account_balance, get_my_accounts, get_account_details
```

### 💳 Transaction Service
```python
from services.transaction import service as transaction_service

# Operations:
transaction_service.create_deposit(...)
transaction_service.create_withdrawal(...)
transaction_service.create_transfer(...)
transaction_service.get_user_transactions(...)
# Used by: deposit_money, withdraw_money, transfer_money, get_my_transactions
```

### 🛍️ Product Service
```python
from services.product import service as product_service

# Operations:
product_service.search_products(...)
product_service.get_product(product_id, db)
product_service.get_products_by_category(...)
# Used by: search_products, get_product_details, get_products_by_category
```

### 🛒 Cart Service
```python
from services.cart import service as cart_service

# Operations:
cart_service.add_to_cart(...)
cart_service.get_user_cart(user_id, db)
cart_service.remove_from_cart(...)
cart_service.checkout(...)
# Used by: add_to_cart, get_my_cart, remove_from_cart, checkout_cart
```

---

## Complete Tool → API Mapping

| # | Tool | External API | Internal Service | DB Tables |
|---|------|--------------|------------------|-----------|
| 1 | `vector_search` | Google Embeddings | - | FAISS store |
| 2 | `web_search` | Tavily | - | - |
| 3 | `get_account_balance` | - | Account | accounts |
| 4 | `get_my_accounts` | - | Account | accounts |
| 5 | `get_account_details` | - | Account | accounts |
| 6 | `deposit_money` | - | Transaction | transactions, accounts |
| 7 | `withdraw_money` | - | Transaction | transactions, accounts |
| 8 | `transfer_money` | - | Transaction | transactions, accounts |
| 9 | `purchase_product` | - | Transaction + Product | transactions, accounts, products |
| 10 | `get_my_transactions` | - | Transaction | transactions |
| 11 | `get_transaction_stats` | - | Transaction | transactions |
| 12 | `get_account_transactions` | - | Transaction | transactions |
| 13 | `get_transaction_details` | - | Transaction | transactions |
| 14 | `search_products` | - | Product | products |
| 15 | `get_product_details` | - | Product | products |
| 16 | `get_products_by_category` | - | Product | products |
| 17 | `get_featured_products` | - | Product | products |
| 18 | `add_to_cart` | - | Cart + Product | cart_items, products |
| 19 | `get_my_cart` | - | Cart + Product | cart_items, products |
| 20 | `remove_from_cart` | - | Cart | cart_items |
| 21 | `checkout_cart` | - | Cart + Product + Account | cart_items, products, accounts, transactions |
| 22 | `clear_cart` | - | Cart | cart_items |

**Total: 22 banking tools + 2 RAG tools = 24 tools**

---

## Data Flow Example

```
User asks: "How much money do I have?"
    ↓
Frontend: POST /api/rag/transaction/query
    ↓
Backend: transaction_router.py
    • Sets context: user_id=1, db=session
    ↓
Supervisor Agent (Gemini 2.0)
    • Analyzes query
    • Decides: Use "get_my_accounts" tool
    ↓
Tool: get_my_accounts(user_id=1)
    • Reads context: user_id=1, db
    • Calls: account_service.get_user_accounts(1, db)
    ↓
Service: services/account/service.py
    • SQL: SELECT * FROM accounts WHERE user_id=1
    ↓
PostgreSQL Database
    • Returns: [Account(id=1, balance=10995.00, ...)]
    ↓
Tool returns: "You have 1 account: Account #1 (Checking): 10995.00 USD"
    ↓
Supervisor synthesizes response
    ↓
Frontend displays: "You currently have $10,995.00 in your checking account."
```

---

## Quick Stats

- **External APIs**: 2 (Google Gemini, Tavily)
- **Internal Services**: 4 (Account, Transaction, Product, Cart)
- **Database Tables**: 6 (users, accounts, transactions, products, cart_items, financial_goals)
- **Total Tools**: 24 (22 banking + 2 RAG)
- **Database**: PostgreSQL (hacknu)
- **Vector Store**: FAISS (local files)

---

## Current Status

✅ All tools registered and integrated  
✅ External APIs configured (Google, Tavily)  
✅ Internal services connected  
✅ Database running  
❌ **Database empty - needs user registration**  

**To fix**: Register/login via frontend to create users and accounts!
