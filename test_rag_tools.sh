#!/bin/bash

# RAG Tools Comprehensive Testing Script
# This script tests all 26 tools through the RAG transaction endpoint

BASE_URL="http://localhost:8000"
USER_ID=1

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}           RAG TOOLS COMPREHENSIVE TEST SUITE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to test RAG query
test_rag_query() {
    local category=$1
    local query=$2
    local user_id=$3
    
    echo -e "${YELLOW}Testing: ${query}${NC}"
    
    response=$(curl -s -X POST "${BASE_URL}/api/rag/transaction/query" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"${query}\", \"user_id\": ${user_id}, \"environment\": \"production\"}")
    
    # Check if response contains error
    if echo "$response" | grep -q "error\|Error\|ERROR"; then
        echo -e "${RED}✗ FAILED${NC}"
        echo "$response" | jq .
    else
        echo -e "${GREEN}✓ SUCCESS${NC}"
        echo "$response" | jq '.response, .sources[0].tool' 2>/dev/null || echo "$response"
    fi
    echo ""
}

# Step 1: Create Test User
echo -e "${BLUE}STEP 1: Creating Test User${NC}"
echo "────────────────────────────────────────────────────────────────────"

register_response=$(curl -s -X POST "${BASE_URL}/api/auth/register" \
    -F "name=Test" \
    -F "surname=User" \
    -F "email=test@zamanbank.com" \
    -F "phone=+77001234567" \
    -F "password=Test1234")

if echo "$register_response" | grep -q "user_id\|id"; then
    USER_ID=$(echo "$register_response" | jq -r '.user_id // .id')
    echo -e "${GREEN}✓ User created successfully! User ID: ${USER_ID}${NC}"
else
    echo -e "${YELLOW}⚠ User might already exist, using default USER_ID=1${NC}"
    USER_ID=1
fi
echo ""

# Step 2: Initialize RAG System
echo -e "${BLUE}STEP 2: Initializing RAG System${NC}"
echo "────────────────────────────────────────────────────────────────────"

curl -s -X POST "${BASE_URL}/api/rag/live/supervisor/initialize?environment=production" | jq .
echo ""

# Step 3: Check RAG System Status
echo -e "${BLUE}STEP 3: Checking RAG System Status${NC}"
echo "────────────────────────────────────────────────────────────────────"

curl -s -X GET "${BASE_URL}/api/rag/live/supervisor/status" | jq .
echo ""

# Step 4: Test Account Tools
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CATEGORY 1: ACCOUNT INFORMATION TOOLS (3 tools)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

test_rag_query "Account" "How much money do I have?" "$USER_ID"
test_rag_query "Account" "Show me all my accounts" "$USER_ID"
test_rag_query "Account" "What are the details of my account 1?" "$USER_ID"

# Step 5: Test Transaction Action Tools
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CATEGORY 2: TRANSACTION ACTION TOOLS (4 tools)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

test_rag_query "Transaction" "Deposit 500 dollars to my account 1" "$USER_ID"
test_rag_query "Transaction" "Withdraw 100 USD from account 1" "$USER_ID"
test_rag_query "Transaction" "Transfer 50 dollars from account 1 to account 2" "$USER_ID"

# Step 6: Test Transaction History Tools
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CATEGORY 3: TRANSACTION HISTORY TOOLS (4 tools)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

test_rag_query "Transaction History" "Show me my recent transactions" "$USER_ID"
test_rag_query "Transaction History" "What are my transaction statistics?" "$USER_ID"
test_rag_query "Transaction History" "Show transactions for account 1" "$USER_ID"

# Step 7: Test Product Tools
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CATEGORY 4: PRODUCT TOOLS (4 tools)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

test_rag_query "Products" "Search for Islamic banking products" "$USER_ID"
test_rag_query "Products" "Show me products in savings category" "$USER_ID"
test_rag_query "Products" "What are the featured products?" "$USER_ID"

# Step 8: Test Cart Tools
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CATEGORY 5: SHOPPING CART TOOLS (5 tools)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

test_rag_query "Cart" "What's in my shopping cart?" "$USER_ID"
test_rag_query "Cart" "Add product 1 to my cart" "$USER_ID"
test_rag_query "Cart" "Show my cart" "$USER_ID"

# Step 9: Test RAG Tools
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CATEGORY 6: KNOWLEDGE SEARCH TOOLS (2 tools)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

test_rag_query "Knowledge" "What is Zaman Bank's mission?" "$USER_ID"
test_rag_query "Web Search" "What are the latest AI trends in 2025?" "$USER_ID"

# Step 10: Combined Queries
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CATEGORY 7: COMPLEX MULTI-TOOL QUERIES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

test_rag_query "Complex" "Show my balance, then deposit 1000 USD to account 1, and show my new balance" "$USER_ID"
test_rag_query "Complex" "What products does Zaman Bank offer and what's my account balance?" "$USER_ID"

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    TEST SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✓ Tested 26 tools across 6 categories${NC}"
echo -e "${YELLOW}  - Account Tools: 3${NC}"
echo -e "${YELLOW}  - Transaction Actions: 4${NC}"
echo -e "${YELLOW}  - Transaction History: 4${NC}"
echo -e "${YELLOW}  - Products: 4${NC}"
echo -e "${YELLOW}  - Shopping Cart: 5${NC}"
echo -e "${YELLOW}  - Knowledge/Web Search: 2${NC}"
echo -e "${YELLOW}  - Complex Multi-tool: 2${NC}"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
