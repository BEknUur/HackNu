# Quick Start: Transaction Agent

## 🚀 Ready to Use!

Your multi-agent RAG system now has transaction capabilities!

## Test It Now

### 1. Check if it's working
```bash
curl http://localhost:8000/api/rag/transaction/capabilities
```

### 2. Test query understanding
```bash
curl -X POST "http://localhost:8000/api/rag/transaction/test?query=Deposit%20500%20dollars%20to%20account%201&user_id=1"
```

### 3. Execute a transaction (requires valid account)
```bash
curl -X POST "http://localhost:8000/api/rag/transaction/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Deposit $500 to account 1",
    "user_id": 1,
    "environment": "development"
  }'
```

## What You Can Say

### 💰 Deposits
- "Deposit $500 to account 1"
- "Add 1000 KZT to my account"
- "Put 100 euros in account 3"

### 💸 Withdrawals
- "Withdraw $200 from account 1"
- "Take out 500 KZT"
- "Remove 50 euros from my account"

### 🔄 Transfers
- "Transfer $100 from account 1 to account 2"
- "Send 5000 KZT to account 3"

### 🛒 Purchases
- "Buy product 5 for $50 from account 1"
- "Purchase item 10 for 15000 KZT"

## API Endpoints

### Transaction Query
```
POST /api/rag/transaction/query
```
Body:
```json
{
  "query": "your natural language query",
  "user_id": 1,
  "environment": "development"
}
```

### Capabilities
```
GET /api/rag/transaction/capabilities
```

### Test Query
```
POST /api/rag/transaction/test?query=YOUR_QUERY&user_id=1
```

## Documentation

📚 Full docs: `/backend/rag_agent/TRANSACTION_AGENT_README.md`
📝 Summary: `/backend/TRANSACTION_AGENT_SUMMARY.md`

## Need Help?

Check the logs:
```bash
docker logs hacknu-backend-1 -f
```

## Features

✅ 4 transaction types (deposit, withdraw, transfer, purchase)
✅ Multi-currency support (USD, EUR, KZT)
✅ Natural language understanding
✅ Automatic parameter extraction
✅ Comprehensive validation
✅ User-friendly error messages
✅ Multi-agent orchestration

Enjoy your AI-powered banking transactions! 🎉
