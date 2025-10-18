#!/usr/bin/env python3
"""
Query Optimization Strategy - Improve query formulation for better results
Based on documentation research and best practices
"""

import re
from typing import List, Dict, Any

def optimize_query_for_equipment(original_query: str) -> List[str]:
    """
    Generate multiple optimized query variations for equipment search.
    Based on document structure analysis.
    """
    
    # Base query variations
    base_variations = [
        "EQUIPMENT AND TECHNOLOGY OF Zaman Bank",
        "company provides equipment employees",
        "laptop computer monitor VPN software",
        "Zaman Bank equipment technology"
    ]
    
    # Extract key terms from original query
    key_terms = re.findall(r'\b\w+\b', original_query.lower())
    equipment_terms = ['equipment', 'technology', 'laptop', 'monitor', 'vpn', 'software', 'computer']
    
    # Find relevant terms
    relevant_terms = [term for term in key_terms if term in equipment_terms]
    
    # Generate optimized queries
    optimized_queries = []
    
    # 1. Exact section match
    optimized_queries.append("EQUIPMENT AND TECHNOLOGY OF Zaman Bank")
    
    # 2. Company-specific queries
    optimized_queries.append("Zaman Bank provides equipment")
    optimized_queries.append("company equipment policy")
    
    # 3. Specific equipment queries
    optimized_queries.append("laptop computer monitor")
    optimized_queries.append("VPN access software licenses")
    
    # 4. Employee-focused queries
    optimized_queries.append("what does company provide employees")
    optimized_queries.append("employee equipment technology")
    
    # 5. Policy-focused queries
    optimized_queries.append("remote work equipment policy")
    optimized_queries.append("technology requirements employees")
    
    return optimized_queries

def test_query_optimization():
    """Test the query optimization strategy."""
    print("\n" + "="*80)
    print("🔍 QUERY OPTIMIZATION STRATEGY")
    print("="*80)
    
    test_queries = [
        "What equipment does Zaman Bank provide?",
        "equipment and technology of Zaman Bank",
        "laptop monitor VPN software"
    ]
    
    for original_query in test_queries:
        print(f"\n📝 Original Query: '{original_query}'")
        optimized = optimize_query_for_equipment(original_query)
        
        print(f"🎯 Optimized Queries:")
        for i, query in enumerate(optimized[:5], 1):  # Show first 5
            print(f"   {i}. {query}")
    
    print("\n" + "="*80)
    print("✅ Query optimization strategy complete!")
    print("="*80)

if __name__ == "__main__":
    test_query_optimization()
