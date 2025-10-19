git #!/usr/bin/env python3
"""
Test Voice-to-Transaction Integration

This script tests the voice-to-transaction functionality by sending
test requests to the live query endpoint.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your server URL
USER_ID = 1  # Test user ID (user 1 has accounts)

def test_live_query(query, user_id=USER_ID):
    """Test a live query request."""
    url = f"{BASE_URL}/api/rag/live/query"
    
    payload = {
        "query": query,
        "user_id": user_id,
        "context": {
            "session_id": "test_session_123"
        }
    }
    
    print(f"\n🔄 Testing: '{query}'")
    print(f"📤 Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success!")
            print(f"📥 Response: {result['response']}")
            print(f"🔧 Agents used: {result.get('agents_used', [])}")
            print(f"📊 Confidence: {result.get('confidence', 0.0)}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    
    print("-" * 80)

def main():
    """Run all tests."""
    print("=" * 80)
    print("🎯 VOICE-TO-TRANSACTION INTEGRATION TEST")
    print("=" * 80)
    
    # Test account information queries
    test_live_query("Show me all my accounts")
    test_live_query("What is my balance in account 1?")
    
    # Test transaction queries
    test_live_query("Transfer 50000 KZT from account 1 to account 2")
    test_live_query("Deposit 100000 tenge to account 1")
    test_live_query("Withdraw 25000 KZT from account 2")
    
    # Test information queries
    test_live_query("What is Zaman Bank's remote work policy?")
    test_live_query("Tell me about current AI trends")
    
    print("\n🎉 Test completed!")
    print("💡 If transactions worked, check your database for new transaction records.")

if __name__ == "__main__":
    main()
