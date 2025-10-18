#!/usr/bin/env python3
"""
Test script for RAG endpoints
"""

import requests
import json

BASE_URL = "http://46.101.175.118:8000"

def test_status_endpoint():
    """Test the status endpoint"""
    print("Testing /api/rag/status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/rag/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_initialize_endpoint():
    """Test the initialize endpoint"""
    print("\nTesting /api/rag/initialize endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/api/rag/initialize", params={"environment": "development"})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_query_endpoint():
    """Test the query endpoint"""
    print("\nTesting /api/rag/query endpoint...")
    try:
        payload = {
            "query": "What is the remote work policy?",
            "context": {},
            "environment": "development"
        }
        response = requests.post(f"{BASE_URL}/api/rag/query", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_tools_status_endpoint():
    """Test the tools status endpoint"""
    print("\nTesting /api/rag/tools/status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/rag/tools/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing RAG endpoints...")
    print("=" * 50)
    
    tests = [
        test_status_endpoint,
        test_initialize_endpoint,
        test_query_endpoint,
        test_tools_status_endpoint
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Status endpoint: {'PASS' if results[0] else 'FAIL'}")
    print(f"Initialize endpoint: {'PASS' if results[1] else 'FAIL'}")
    print(f"Query endpoint: {'PASS' if results[2] else 'FAIL'}")
    print(f"Tools status endpoint: {'PASS' if results[3] else 'FAIL'}")
    
    all_passed = all(results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    main()
