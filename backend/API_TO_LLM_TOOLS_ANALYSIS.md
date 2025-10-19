# Complete API to LLM Tools Analysis

## 🎯 Executive Summary

Your backend has **48+ API endpoints** across 6 services. Currently, only 4 transaction action tools are exposed to the LLM. This document proposes **15 additional tools** to enable complete natural language interaction with your financial system.

### Current State
✅ **Transaction Actions** (4 tools implemented)
- Deposit money
- Withdraw money
- Transfer money
- Purchase product

### Proposed State
🚀 **Complete Natural Language Banking** (19 total tools)
- Account information queries
- Transaction history & analytics
- Product browsing & search
- Shopping cart management
- Financial goals planning

---

## 📊 Complete API Endpoint Inventory

### 1. Authentication Service (`/auth`)

| Endpoint | Method | Description | LLM Tool Needed? |
|----------|--------|-------------|------------------|
| `/register` | POST | Register new user with avatar | ❌ No - One-time setup |
| `/login` | POST | Login with email/password | ❌ No - Authentication layer |
| `/{user_id}/avatar` | PUT | Update user avatar | ❌ No - Not conversational |

**Analysis:** Auth endpoints are not suitable for LLM tools - they're one-time actions or authentication mechanisms.

---

### 2. Account Service (`/accounts`)

| Endpoint | Method | Description | LLM Tool Priority |
|----------|--------|-------------|-------------------|
| `/` | POST | Create new account | 🟡 Medium - "Create savings account" |
| `/{account_id}` | GET | Get account details | 🔴 **HIGH** - "What's my account info?" |
| `/user/{user_id}` | GET | Get all user accounts | 🔴 **HIGH** - "Show my accounts" |
| `/` | GET | Get all accounts (admin) | ❌ Admin only |
| `/{account_id}` | PUT | Update account info | 🟢 Low - Rare use case |
| `/{account_id}` | DELETE | Delete account | 🟢 Low - Sensitive operation |
| `/{account_id}/restore` | POST | Restore deleted account | ❌ No - Admin action |
| `/{account_id}/block` | POST | Block account | ❌ No - Security action |
| `/{account_id}/unblock` | POST | Unblock account | ❌ No - Security action |

**Proposed Tools:**
1. ✅ `get_account_balance(account_id)` - Get current balance
2. ✅ `get_my_accounts(user_id)` - List all accounts with balances
3. ✅ `get_account_details(account_id)` - Full account information

**Example Queries:**
- "What's my balance?"
- "How much money do I have in my savings account?"
- "Show me all my accounts"
- "What's the balance in account 1?"

---

### 3. Transaction Service (`/transactions`)

| Endpoint | Method | Description | LLM Tool Status |
|----------|--------|-------------|-----------------|
| `/deposit` | POST | Deposit funds | ✅ **IMPLEMENTED** |
| `/withdrawal` | POST | Withdraw funds | ✅ **IMPLEMENTED** |
| `/transfer` | POST | Transfer between accounts | ✅ **IMPLEMENTED** |
| `/purchase` | POST | Purchase product | ✅ **IMPLEMENTED** |
| `/{transaction_id}` | GET | Get transaction details | 🔴 **HIGH** - "Show transaction #123" |
| `/user/{user_id}` | GET | Get user transactions + filters | 🔴 **HIGH** - "Show my last 10 transactions" |
| `/account/{account_id}/history` | GET | Get account transaction history | 🔴 **HIGH** - "Show account 1 history" |
| `/{transaction_id}` | PUT | Update transaction description | 🟡 Medium - "Rename transaction" |
| `/{transaction_id}` | DELETE | Delete transaction | 🟢 Low - Sensitive |
| `/user/{user_id}/stats` | GET | Get transaction statistics | 🔴 **HIGH** - "How much did I spend?" |

**Proposed Tools:**
4. ✅ `get_my_transactions(user_id, limit, filters)` - Transaction history
5. ✅ `get_account_transactions(account_id)` - Account-specific history
6. ✅ `get_transaction_stats(user_id, currency, date_range)` - Spending analytics
7. ✅ `get_transaction_details(transaction_id)` - Single transaction info

**Example Queries:**
- "Show my last 5 transactions"
- "How much did I spend this month?"
- "What are my deposits this week?"
- "Show all transfers I made to account 2"
- "What's my spending in USD?"

---

### 4. Product Service (`/products`)

| Endpoint | Method | Description | LLM Tool Priority |
|----------|--------|-------------|-------------------|
| `/` | POST | Create product | ❌ No - Admin only |
| `/{product_id}` | GET | Get product details | 🔴 **HIGH** - "Tell me about product X" |
| `/` | GET | Get all products | 🔴 **HIGH** - "What products are available?" |
| `/search` | POST | Search products with filters | 🔴 **HIGH** - "Find insurance products" |
| `/category/{category}` | GET | Get products by category | 🔴 **HIGH** - "Show banking products" |
| `/featured/top` | GET | Get featured products | 🟡 Medium - "What's popular?" |
| `/{product_id}` | PUT | Update product | ❌ No - Admin only |
| `/{product_id}` | DELETE | Delete product | ❌ No - Admin only |
| `/{product_id}/restore` | POST | Restore product | ❌ No - Admin only |

**Proposed Tools:**
8. ✅ `search_products(query, category, price_range)` - Search & filter products
9. ✅ `get_product_details(product_id)` - Product information
10. ✅ `get_products_by_category(category)` - Browse by category
11. ✅ `get_featured_products(limit)` - Popular products

**Example Queries:**
- "What banking products do you have?"
- "Find investment products under $1000"
- "Tell me about product 5"
- "What are the most popular products?"
- "Show me insurance options"
- "Search for credit card products"

---

### 5. Cart Service (`/cart`)

| Endpoint | Method | Description | LLM Tool Priority |
|----------|--------|-------------|-------------------|
| `/` | POST | Add item to cart | 🔴 **HIGH** - "Add product X to cart" |
| `/` | GET | Get user's cart | 🔴 **HIGH** - "Show my cart" |
| `/history` | GET | Get cart history | 🟡 Medium - "What did I buy?" |
| `/{cart_item_id}` | GET | Get specific cart item | 🟢 Low - Rare use |
| `/{cart_item_id}` | PUT | Update cart item | 🟡 Medium - "Change quantity" |
| `/{cart_item_id}` | DELETE | Remove from cart | 🔴 **HIGH** - "Remove item from cart" |
| `/` | DELETE | Clear cart | 🟡 Medium - "Clear my cart" |
| `/checkout` | POST | Checkout and purchase | 🔴 **HIGH** - "Buy everything in cart" |

**Proposed Tools:**
12. ✅ `add_to_cart(user_id, product_id, quantity)` - Add items
13. ✅ `get_my_cart(user_id)` - View cart contents
14. ✅ `remove_from_cart(user_id, cart_item_id)` - Remove items
15. ✅ `checkout_cart(user_id, account_id)` - Complete purchase
16. ✅ `clear_cart(user_id)` - Empty cart

**Example Queries:**
- "Add product 3 to my cart"
- "What's in my cart?"
- "How much is my cart total?"
- "Remove item 2 from my cart"
- "Checkout using account 1"
- "Buy everything in my cart with my savings account"
- "Clear my shopping cart"

---

### 6. Financial Goals Service (`/financial-goals`)

| Endpoint | Method | Description | LLM Tool Priority |
|----------|--------|-------------|-------------------|
| `/` | POST | Create financial goal | 🔴 **HIGH** - "I want to save for X" |
| `/` | GET | Get all user goals | 🔴 **HIGH** - "Show my goals" |
| `/{goal_id}` | GET | Get specific goal | 🟡 Medium - "How's goal X doing?" |
| `/{goal_id}` | PUT | Update goal | 🟡 Medium - "Change goal target" |
| `/{goal_id}` | DELETE | Delete goal | 🟢 Low - Rare |
| `/{goal_id}/analysis` | GET | Get AI goal analysis | 🔴 **HIGH** - "Can I achieve this?" |
| `/{goal_id}/update-progress` | POST | Update savings progress | 🟡 Medium - "Update goal progress" |
| `/user/financial-summary` | GET | Get financial summary | 🔴 **HIGH** - "My financial overview" |
| `/recommendations/goal-suggestions` | GET | Get AI recommendations | 🟡 Medium - "Suggest goals for me" |

**Proposed Tools:**
17. ✅ `get_my_financial_goals(user_id)` - List all goals
18. ✅ `create_financial_goal(user_id, goal_data)` - Create savings goal
19. ✅ `get_goal_analysis(goal_id)` - AI analysis & predictions
20. ✅ `get_financial_summary(user_id)` - Complete financial overview

**Example Queries:**
- "I want to save $5000 for a vacation"
- "Show my financial goals"
- "Can I achieve my goal to buy a car?"
- "What's my financial situation?"
- "Create a goal to save $10000 in 12 months"
- "How likely am I to reach my savings goal?"

---

## 🎨 Implementation Architecture

### Proposed File Structure

```
backend/rag_agent/tools/
├── transaction_tools.py          # ✅ Already implemented (4 tools)
├── account_tools.py              # 🆕 3 tools - Account queries
├── transaction_history_tools.py  # 🆕 4 tools - Transaction history
├── product_tools.py              # 🆕 4 tools - Product browsing
├── cart_tools.py                 # 🆕 5 tools - Cart management
└── financial_goal_tools.py       # 🆕 4 tools - Goals & planning
```

### Tool Pattern (from Context7 best practices)

```python
from langchain_core.tools import tool
from typing import Dict, Any

# Global context for user_id and db session
_account_context: Dict[str, Any] = {}

def set_account_context(user_id: int, db):
    """Set the context for account tools."""
    global _account_context
    _account_context = {"user_id": user_id, "db": db}

@tool
def get_account_balance(account_id: int) -> str:
    """
    Get the current balance of a specific account.
    
    Args:
        account_id: The ID of the account to check
        
    Returns:
        A formatted string with the account balance and currency
        
    Examples:
        - "What's my balance in account 1?"
        - "How much money is in my savings account 2?"
        - "Check balance of account 3"
    """
    try:
        user_id = _account_context.get("user_id")
        db = _account_context.get("db")
        
        # Call service layer
        account = account_service.get_account(account_id, db)
        
        # Verify ownership
        if account.user_id != user_id:
            return f"Error: You don't have permission to view account {account_id}"
        
        return f"Account {account_id} ({account.account_type}): {account.balance} {account.currency}"
        
    except Exception as e:
        return f"Error getting account balance: {str(e)}"
```

---

## 💬 Complete User Experience Examples

### Scenario 1: Checking Financial Status
```
User: "What's my current financial situation?"

LLM uses:
1. get_my_accounts() → Shows all accounts with balances
2. get_financial_summary() → Overall financial health
3. get_my_financial_goals() → Active savings goals

Response: "You have 3 accounts with a total of $15,243. Your checking 
account has $5,243, savings has $8,000, and investment account has 
$2,000. You have 2 active financial goals..."
```

### Scenario 2: Making a Purchase
```
User: "I want to buy product 5 and product 12"

LLM uses:
1. get_product_details(5) → Gets product info
2. get_product_details(12) → Gets product info
3. add_to_cart(user_id, 5, 1) → Adds first product
4. add_to_cart(user_id, 12, 1) → Adds second product
5. get_my_cart() → Shows cart summary

Response: "I've added Premium Insurance ($150) and Gold Credit Card 
($100) to your cart. Your total is $250. Would you like to checkout?"

User: "Yes, use my checking account"

LLM uses:
6. checkout_cart(user_id, checking_account_id) → Completes purchase

Response: "Purchase complete! $250 has been charged to your checking 
account. New balance: $4,993"
```

### Scenario 3: Budget Analysis
```
User: "How much did I spend on purchases last month?"

LLM uses:
1. get_transaction_stats(user_id, "USD", date_from="2024-12-01", date_to="2024-12-31")

Response: "In December, you spent $1,250 on purchases across 8 
transactions. You also made 3 deposits totaling $3,000 and 2 
transfers totaling $500."
```

### Scenario 4: Financial Planning
```
User: "I want to save $10,000 for a car in 12 months"

LLM uses:
1. get_my_accounts() → Checks current financial state
2. create_financial_goal(user_id, {target: 10000, deadline: "2025-12-19"})
3. get_goal_analysis(goal_id) → Gets AI predictions

Response: "I've created your car savings goal. Based on your income 
and spending patterns, you have a 78% probability of achieving this. 
I recommend saving $850 per month. Would you like to set up automatic 
monthly deposits?"
```

### Scenario 5: Product Discovery
```
User: "What banking products do you have under $200?"

LLM uses:
1. search_products(category="banking", max_price=200)

Response: "I found 5 banking products under $200:
1. Basic Checking Account - $0
2. Premium Savings Account - $50/year
3. Student Account - $0
4. Business Starter Account - $150/year
5. Silver Debit Card - $25

Which one interests you?"
```

---

## 📋 Implementation Priority

### Phase 1: High Priority - Account & Transaction Info (Week 1)
**Goal:** Enable users to check their financial status

- ✅ `get_account_balance(account_id)`
- ✅ `get_my_accounts(user_id)`
- ✅ `get_my_transactions(user_id, limit, filters)`
- ✅ `get_transaction_stats(user_id, currency, date_range)`

**Value:** Users can check balances and spending without manual API calls

### Phase 2: High Priority - Product Discovery (Week 1)
**Goal:** Enable product browsing and shopping

- ✅ `search_products(query, category, price_range)`
- ✅ `get_product_details(product_id)`
- ✅ `get_products_by_category(category)`

**Value:** Users can discover and learn about products conversationally

### Phase 3: High Priority - Shopping Cart (Week 2)
**Goal:** Complete e-commerce experience

- ✅ `add_to_cart(user_id, product_id, quantity)`
- ✅ `get_my_cart(user_id)`
- ✅ `remove_from_cart(user_id, cart_item_id)`
- ✅ `checkout_cart(user_id, account_id)`

**Value:** Full shopping experience through conversation

### Phase 4: Medium Priority - Financial Planning (Week 2)
**Goal:** AI-powered financial goal management

- ✅ `get_my_financial_goals(user_id)`
- ✅ `create_financial_goal(user_id, goal_data)`
- ✅ `get_goal_analysis(goal_id)`
- ✅ `get_financial_summary(user_id)`

**Value:** Proactive financial planning with AI insights

---

## 🔧 Technical Implementation Details

### 1. Tool Registration in LangGraph

```python
# backend/rag_agent/config/langraph.py

class SupervisorAgentConfig:
    tools = [
        # Transaction actions (existing)
        "deposit_money", "withdraw_money", "transfer_money", "purchase_product",
        
        # Account information (new)
        "get_account_balance", "get_my_accounts", "get_account_details",
        
        # Transaction history (new)
        "get_my_transactions", "get_transaction_stats", "get_account_transactions",
        
        # Products (new)
        "search_products", "get_product_details", "get_products_by_category",
        
        # Cart (new)
        "add_to_cart", "get_my_cart", "checkout_cart", "remove_from_cart",
        
        # Financial goals (new)
        "get_my_financial_goals", "create_financial_goal", "get_goal_analysis",
        
        # RAG tools
        "vector_search", "web_search"
    ]
```

### 2. Enhanced System Prompt

```python
system_prompt = """You are a helpful AI banking assistant with access to:

ACCOUNT TOOLS:
- get_account_balance: Check account balance
- get_my_accounts: List all user accounts

TRANSACTION TOOLS (Actions):
- deposit_money: Add funds to account
- withdraw_money: Remove funds from account
- transfer_money: Transfer between accounts
- purchase_product: Buy products

TRANSACTION TOOLS (History):
- get_my_transactions: View transaction history
- get_transaction_stats: Analyze spending patterns

PRODUCT TOOLS:
- search_products: Find products by criteria
- get_product_details: Get product information
- get_products_by_category: Browse by category

CART TOOLS:
- add_to_cart: Add products to shopping cart
- get_my_cart: View cart contents
- checkout_cart: Complete purchase
- remove_from_cart: Remove cart items

FINANCIAL PLANNING TOOLS:
- get_my_financial_goals: View savings goals
- create_financial_goal: Create new goal with AI analysis
- get_goal_analysis: Get AI predictions for goal achievement

Always:
1. Confirm before executing financial transactions
2. Provide clear, formatted responses
3. Suggest related actions when helpful
4. Use appropriate tools based on user intent
"""
```

### 3. Context Management Pattern

Each tool file follows this pattern:

```python
# Set context at request time
from rag_agent.tools import (
    set_account_context,
    set_transaction_context,
    set_product_context,
    set_cart_context,
    set_goal_context
)

@router.post("/api/rag/query")
def query_rag(query: str, user_id: int, db: Session = Depends(get_db)):
    # Set context for all tools
    set_account_context(user_id, db)
    set_transaction_context(user_id, db)
    set_product_context(user_id, db)
    set_cart_context(user_id, db)
    set_goal_context(user_id, db)
    
    # Execute RAG query
    result = rag_system.query(query)
    return result
```

---

## 📊 Impact Analysis

### Before (Current State)
- **Tools Available:** 4 (transaction actions only)
- **User Capability:** Can perform deposits, withdrawals, transfers, purchases
- **User Experience:** Must know account IDs, balances, product IDs manually
- **Conversation Types:** Action-only ("Transfer $100")

### After (Proposed State)
- **Tools Available:** 20 (complete financial management)
- **User Capability:** Full account management, shopping, planning, analytics
- **User Experience:** Natural conversation without technical knowledge
- **Conversation Types:** Questions + Actions ("How much do I have? Transfer $100")

### Example Conversation Flow

**Current (Limited):**
```
User: "Transfer $500 to account 2"
LLM: Uses transfer_money tool
Response: "Transfer complete"
```

**Proposed (Complete):**
```
User: "Do I have enough money to buy product 5?"
LLM: 
  1. Uses get_my_accounts() → Sees checking: $2,500
  2. Uses get_product_details(5) → Price: $150
Response: "Yes, you have $2,500 in your checking account. Product 5 
costs $150. Would you like to purchase it?"

User: "Yes, buy it"
LLM: Uses purchase_product(account_id, 5, 150)
Response: "Purchase complete! $150 charged to checking. New balance: $2,350"
```

---

## 🎯 Recommended Next Steps

1. **Review & Approve** this analysis
2. **Choose Implementation Priority**
   - Option A: All 20 tools at once (2-3 days)
   - Option B: Phase 1+2 first (1 day), then Phase 3+4 (1 day)
   - Option C: Custom priority based on your needs

3. **Implementation Plan**
   - Create 5 new tool files
   - Register 16 new tools in langraph.py
   - Update supervisor system prompt
   - Create unified router for all queries
   - Write comprehensive tests
   - Update documentation

4. **Testing Strategy**
   - Test each tool independently
   - Test multi-tool conversations
   - Test error handling & edge cases
   - Test with real user scenarios

---

## 📝 Questions for You

1. **Priority:** Which tools are most important for your use case?
2. **Scope:** Should we implement all 20 tools or start with a subset?
3. **Security:** Should some operations require additional confirmation?
4. **Features:** Any additional capabilities you'd like exposed to the LLM?

---

## 🚀 Ready to Implement?

Once you approve, I'll:
1. Create all 5 new tool files following LangChain best practices
2. Register tools in LangGraph configuration
3. Update the system prompt with tool descriptions
4. Create test suite for new capabilities
5. Document usage examples

**Estimated Implementation Time:** 2-3 hours for all 20 tools

Would you like me to proceed with the implementation? If so, which priority phase should I start with?
