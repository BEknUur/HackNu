"""
Product Browsing Tools for RAG Agent

This module provides LangChain tools for discovering and browsing products.
Users can search for products, view details, and explore categories.

Tools:
- search_products: Search for products with filters
- get_product_details: Get information about a specific product
- get_products_by_category: Browse products in a category
- get_featured_products: View popular/featured products
"""

from langchain_core.tools import tool
from typing import Dict, Any, Optional
from decimal import Decimal
from services.product import service as product_service
from services.product.schemas import ProductSearch


# Global context for db session
_product_context: Dict[str, Any] = {}


def set_product_context(user_id: int, db):
    """
    Set the context for product tools.
    
    Args:
        user_id: The ID of the user making the request
        db: SQLAlchemy database session
    """
    global _product_context
    _product_context = {"user_id": user_id, "db": db}


@tool
def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 10
) -> str:
    """
    Search for products with optional filters.
    
    This tool allows searching across all products with filters for
    text search, category, and price range. Useful for finding specific
    products or browsing by criteria.
    
    Args:
        query: Search text (searches in title and description)
        category: Filter by category ('banking', 'insurance', 'investment', 'cards')
        max_price: Maximum price filter
        limit: Maximum number of results (default: 10, max: 20)
        
    Returns:
        A formatted list of matching products with prices and descriptions.
        
    Examples:
        User: "Find banking products"
        User: "Search for insurance under $100"
        User: "What credit card products do you have?"
        User: "Show me investment products"
        User: "Find products with 'premium' in the name"
    """
    try:
        db = _product_context.get("db")
        
        if not db:
            return "Error: Product context not set. Please try again."
        
        # Limit results
        limit = min(limit, 20)
        
        # Build filters
        filters = ProductSearch(
            search_query=query,
            category=category,
            max_price=Decimal(str(max_price)) if max_price is not None else None,
            is_active='active'
        )
        
        # Search products
        products = product_service.search_products(db, filters, skip=0, limit=limit)
        
        if not products:
            search_desc = []
            if query:
                search_desc.append(f"'{query}'")
            if category:
                search_desc.append(f"category '{category}'")
            if max_price:
                search_desc.append(f"under ${max_price}")
            
            search_str = " ".join(search_desc) if search_desc else "your criteria"
            return f"No products found matching {search_str}."
        
        # Format product list
        response = f"Found {len(products)} product(s)"
        if query or category or max_price:
            filters_desc = []
            if query:
                filters_desc.append(f"matching '{query}'")
            if category:
                filters_desc.append(f"in {category}")
            if max_price:
                filters_desc.append(f"under ${max_price}")
            response += f" ({', '.join(filters_desc)})"
        response += ":\n\n"
        
        for product in products:
            # Category emoji
            category_emoji = {
                'banking': '🏦',
                'insurance': '🛡️',
                'investment': '📈',
                'cards': '💳'
            }.get(product.category, '📦')
            
            response += f"{category_emoji} Product #{product.id}: {product.title}\n"
            response += f"   Price: {product.price} {product.currency}\n"
            
            if product.description:
                # Truncate long descriptions
                desc = product.description
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                response += f"   Description: {desc}\n"
            
            if product.category:
                response += f"   Category: {product.category.title()}\n"
            
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error searching products: {str(e)}"


@tool
def get_product_details(product_id: int) -> str:
    """
    Get detailed information about a specific product.
    
    This tool provides complete information about a product including
    title, description, price, category, and availability.
    
    Args:
        product_id: The ID of the product to view
        
    Returns:
        A formatted string with complete product information.
        
    Examples:
        User: "Tell me about product 5"
        User: "What is product 3?"
        User: "Show details for product 10"
        User: "Give me information about that insurance product"
    """
    try:
        db = _product_context.get("db")
        
        if not db:
            return "Error: Product context not set. Please try again."
        
        # Get product
        product = product_service.get_product(product_id, db)
        
        # Category emoji
        category_emoji = {
            'banking': '🏦',
            'insurance': '🛡️',
            'investment': '📈',
            'cards': '💳'
        }.get(product.category, '📦')
        
        # Format details
        details = f"{category_emoji} Product #{product.id}: {product.title}\n\n"
        details += f"💰 Price: {product.price} {product.currency}\n"
        
        if product.category:
            details += f"📂 Category: {product.category.title()}\n"
        
        if product.description:
            details += f"\n📝 Description:\n{product.description}\n"
        
        # Status
        if product.is_active:
            details += f"\n✅ Status: Available for purchase"
        else:
            details += f"\n❌ Status: Currently unavailable"
        
        # Purchase count if significant
        if product.purchase_count and product.purchase_count > 0:
            details += f"\n⭐ {product.purchase_count} customer(s) have purchased this product"
        
        return details
        
    except Exception as e:
        return f"Error getting product details: {str(e)}"


@tool
def get_products_by_category(category: str, limit: int = 10) -> str:
    """
    Browse all products in a specific category.
    
    This tool shows products filtered by category, making it easy to
    explore banking, insurance, investment, or card products.
    
    Args:
        category: Category to browse ('banking', 'insurance', 'investment', 'cards')
        limit: Maximum number of products to show (default: 10, max: 20)
        
    Returns:
        A formatted list of products in the specified category.
        
    Examples:
        User: "Show banking products"
        User: "What insurance options do you have?"
        User: "List investment products"
        User: "Show me credit card options"
        User: "Browse banking category"
    """
    try:
        db = _product_context.get("db")
        
        if not db:
            return "Error: Product context not set. Please try again."
        
        # Validate category
        valid_categories = ['banking', 'insurance', 'investment', 'cards']
        category_lower = category.lower()
        
        if category_lower not in valid_categories:
            return f"Invalid category. Please choose from: {', '.join(valid_categories)}"
        
        # Limit results
        limit = min(limit, 20)
        
        # Get products by category
        products = product_service.get_products_by_category(category_lower, db, skip=0, limit=limit)
        
        if not products:
            return f"No active products found in the {category} category."
        
        # Category emoji
        category_emoji = {
            'banking': '🏦',
            'insurance': '🛡️',
            'investment': '📈',
            'cards': '💳'
        }.get(category_lower, '📦')
        
        # Format product list
        response = f"{category_emoji} {category.title()} Products ({len(products)} available):\n\n"
        
        for product in products:
            response += f"• Product #{product.id}: {product.title}\n"
            response += f"  Price: {product.price} {product.currency}\n"
            
            if product.description:
                # Short description
                desc = product.description
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                response += f"  {desc}\n"
            
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error getting products by category: {str(e)}"


@tool
def get_featured_products(limit: int = 5) -> str:
    """
    View popular or featured products.
    
    This tool shows the most popular products based on purchase count,
    helping users discover what other customers are buying.
    
    Args:
        limit: Maximum number of products to show (default: 5, max: 10)
        
    Returns:
        A formatted list of featured/popular products.
        
    Examples:
        User: "What are the most popular products?"
        User: "Show me featured products"
        User: "What do most people buy?"
        User: "Show top products"
    """
    try:
        db = _product_context.get("db")
        
        if not db:
            return "Error: Product context not set. Please try again."
        
        # Limit results
        limit = min(limit, 10)
        
        # Get featured products
        products = product_service.get_featured_products(db, limit)
        
        if not products:
            return "No featured products available at the moment."
        
        # Format product list
        response = f"⭐ Featured Products (Top {len(products)}):\n\n"
        
        for idx, product in enumerate(products, 1):
            # Category emoji
            category_emoji = {
                'banking': '🏦',
                'insurance': '🛡️',
                'investment': '📈',
                'cards': '💳'
            }.get(product.category, '📦')
            
            response += f"{idx}. {category_emoji} {product.title}\n"
            response += f"   Product ID: #{product.id}\n"
            response += f"   Price: {product.price} {product.currency}\n"
            
            if product.purchase_count and product.purchase_count > 0:
                response += f"   Purchases: {product.purchase_count} ⭐\n"
            
            if product.description:
                desc = product.description
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                response += f"   {desc}\n"
            
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error getting featured products: {str(e)}"
