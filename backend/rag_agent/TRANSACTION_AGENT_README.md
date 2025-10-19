# Transaction Agent Integration

This module adds transaction capabilities to the Agentic RAG system, allowing users to perform financial operations through natural language prompts.

## Overview

The transaction agent extends the RAG system with four main financial operations:
- **Deposit Money**: Add funds to an account
- **Withdraw Money**: Remove funds from an account
- **Transfer Money**: Send funds between accounts
- **Purchase Product**: Buy products using account funds

## Architecture

### Components

1. **Transaction Tools** (`rag_agent/tools/transaction_tools.py`)
   - LangChain tool definitions using `@tool` decorator
   - Integration with transaction service layer
   - Context management for user authentication and database sessions

2. **Transaction Agent Config** (`rag_agent/config/langraph.py`)
   - Specialized agent configuration for financial operations
   - Integration with supervisor agent
   - Tool registry and factory patterns

3. **Transaction Router** (`rag_agent/routes/transaction_router.py`)
   - FastAPI endpoints for transaction-enabled RAG queries
   - Authentication and authorization
   - Context setup for tools

## Usage

### API Endpoint

```bash
POST /api/rag/transaction/query
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "query": "Deposit $500 to my account 1",
  "environment": "production"
}
```

### Response

```json
{
  "query": "Deposit $500 to my account 1",
  "response": "✅ Deposit successful!\nTransaction ID: 123\nAmount: 500.0 USD\nAccount ID: 1\n...",
  "sources": [
    {
      "tool": "deposit_money",
      "query": {"account_id": 1, "amount": 500, "currency": "USD"}
    }
  ],
  "confidence": 0.95,
  "status": "success",
  "transaction_executed": true
}
```

### Example Queries

#### Deposits
```
- "Deposit $500 to account 1"
- "Add 1000 KZT to my account 2"
- "Deposit 100 euros to account 3 for salary"
```

#### Withdrawals
```
- "Withdraw $200 from account 1"
- "Take out 500 KZT from my account 2"
- "Withdraw 50 euros from account 3"
```

#### Transfers
```
- "Transfer $100 from account 1 to account 2"
- "Send 5000 KZT from my account 3 to account 4"
- "Transfer 75 euros from account 1 to account 5 for payment"
```

#### Purchases
```
- "Buy product 5 for $50 from account 1"
- "Purchase product 10 using account 2 for 15000 KZT"
- "Buy item 3 for 30 euros from my account 4"
```

## How It Works

### 1. Context Setup

Before processing queries, the transaction context is established:

```python
from rag_agent.tools.transaction_tools import set_transaction_context

# In your API endpoint
set_transaction_context(user_id=current_user.id, db=db)
```

This ensures:
- User authentication is maintained
- Database transactions are properly scoped
- Security boundaries are enforced

### 2. Query Processing

The RAG system:
1. Analyzes the natural language query
2. Identifies transaction intent
3. Extracts parameters (account_id, amount, currency, etc.)
4. Calls the appropriate tool
5. Returns the result to the user

### 3. Tool Execution

Each tool:
1. Validates input parameters
2. Creates appropriate schema objects
3. Calls the transaction service layer
4. Returns formatted success/error messages

## Security Features

### Authentication
- All transactions require JWT authentication
- User context is propagated through the tool execution chain

### Authorization
- Users can only perform transactions on their own accounts
- The transaction service verifies account ownership

### Validation
- Amount must be positive
- Currency must be valid (USD, EUR, KZT)
- Account IDs must exist and be active
- Sufficient balance checks for withdrawals/transfers

## Configuration

### Tool Registration

Tools are automatically registered in `langraph.py`:

```python
def _setup_default_tools(self):
    self.tool_registry.register_tool_factory("deposit_money", self._create_deposit_tool)
    self.tool_registry.register_tool_factory("withdraw_money", self._create_withdraw_tool)
    self.tool_registry.register_tool_factory("transfer_money", self._create_transfer_tool)
    self.tool_registry.register_tool_factory("purchase_product", self._create_purchase_tool)
```

### Agent Configuration

The supervisor agent includes transaction tools:

```python
class SupervisorAgentConfig(AgentConfig):
    tools: List[str] = [
        "vector_search", 
        "web_search", 
        "deposit_money", 
        "withdraw_money", 
        "transfer_money", 
        "purchase_product"
    ]
```

## Error Handling

### Common Errors

1. **Validation Errors**
   ```
   ❌ Error: Amount must be positive. You provided: -100
   ```

2. **Account Errors**
   ```
   ❌ Error: Account 5 not found
   ```

3. **Insufficient Funds**
   ```
   ❌ Error: Insufficient balance for withdrawal
   ```

4. **Currency Mismatch**
   ```
   ❌ Error: Currency mismatch. Account uses USD, transaction uses EUR
   ```

## Testing

### Test Endpoint

Use the test endpoint to verify query understanding without executing:

```bash
POST /api/rag/transaction/test?query=Deposit $500 to account 1
Authorization: Bearer <token>
```

Response:
```json
{
  "query": "Deposit $500 to account 1",
  "user_id": 1,
  "detected_action": "deposit_money",
  "would_execute": true,
  "message": "Query would trigger 'deposit_money' tool",
  "note": "This is a test endpoint. Use /query for actual execution."
}
```

### Capabilities Endpoint

Get information about available transaction tools:

```bash
GET /api/rag/transaction/capabilities
```

## Integration with Existing Services

The transaction agent integrates seamlessly with existing services:

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
    ┌────▼────┐      ┌────▼────────┐
    │  Auth   │      │   RAG       │
    │ Service │      │  Router     │
    └────┬────┘      └────┬────────┘
         │                │
         │           ┌────▼────────┐
         │           │ Transaction │
         │           │   Tools     │
         │           └────┬────────┘
         │                │
         │           ┌────▼────────┐
         └───────────►Transaction │
                     │  Service   │
                     └────┬────────┘
                          │
                     ┌────▼────────┐
                     │  Database   │
                     └─────────────┘
```

## Future Enhancements

1. **Transaction History Queries**
   - "Show my last 5 transactions"
   - "What transactions did I make yesterday?"

2. **Account Information Queries**
   - "What's my balance in account 1?"
   - "List all my accounts"

3. **Complex Transactions**
   - Scheduled transfers
   - Recurring payments
   - Multi-account operations

4. **Transaction Confirmations**
   - Optional confirmation step before execution
   - Transaction limits and approval workflows

## Troubleshooting

### Issue: "Transaction context not set"

**Solution**: Ensure `set_transaction_context()` is called before processing queries:

```python
set_transaction_context(user_id=current_user.id, db=db)
```

### Issue: "Tool not found in registry"

**Solution**: Verify tool registration in `_setup_default_tools()` method.

### Issue: "User can't perform transaction"

**Solution**: Check:
1. User is authenticated
2. Account belongs to user
3. Account is active
4. Sufficient balance (for withdrawals/transfers)

## Contributing

When adding new transaction types:

1. Create tool function in `transaction_tools.py`
2. Register in `_setup_default_tools()`
3. Add to supervisor agent tools list
4. Update system prompt with instructions
5. Add tests and documentation

## License

Part of the Zaman Bank API system.
