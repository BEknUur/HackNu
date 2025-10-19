"""
Shopping Cart Tools for RAG Agent

This module provides LangChain tools for managing a shopping cart.
Users can add items, view cart contents, remove items, and checkout.

Tools:
- add_to_cart: Add products to shopping cart
- get_my_cart: View current cart contents
- remove_from_cart: Remove items from cart
- checkout_cart: Complete purchase from cart
- clear_cart: Empty the entire cart
"""

from langchain_core.tools import tool
from typing import Dict, Any
from services.cart import service as cart_service
from services.cart.schemas import CartItemCreate, CheckoutRequest


# Global context for user_id and db session
_cart_context: Dict[str, Any] = {}


def set_cart_context(user_id: int, db):
    """
    Set the context for cart tools.
    
    Args:
        user_id: The ID of the user making the request
        db: SQLAlchemy database session
    """
    global _cart_context
    _cart_context = {"user_id": user_id, "db": db}


@tool
def add_to_cart(product_id: int, quantity: int = 1) -> str:
    """
    Add a product to your shopping cart.
    
    This tool adds the specified product to your cart. If the product is
    already in your cart, the quantity will be increased. You can specify
    a quantity greater than 1 to add multiple items at once.
    
    Args:
        product_id: The ID of the product to add to cart
        quantity: Number of items to add (default: 1, must be positive)
        
    Returns:
        A confirmation message with the product added and current cart status.
        
    Examples:
        User: "Add product 5 to my cart"
        User: "Put product 3 in my shopping cart"
        User: "Add 2 of product 10 to cart"
        User: "I want to buy product 7"
    """
    try:
        user_id = _cart_context.get("user_id")
        db = _cart_context.get("db")
        
        if not user_id or not db:
            return "Error: Cart context not set. Please try again."
        
        # Validate quantity
        if quantity < 1:
            return "Error: Quantity must be at least 1."
        
        # Create cart item data
        cart_data = CartItemCreate(
            product_id=product_id,
            quantity=quantity
        )
        
        # Add to cart
        cart_item = cart_service.add_to_cart(user_id, cart_data, db)
        
        # Get product details for response
        from services.product import service as product_service
        product = product_service.get_product(product_id, db)
        
        # Format response
        response = f"✅ Added to cart:\n"
        response += f"   • {product.title} (x{cart_item.quantity})\n"
        response += f"   • Price: {product.price} {product.currency} each\n"
        response += f"   • Subtotal: {float(product.price) * cart_item.quantity:.2f} {product.currency}\n\n"
        
        # Get cart summary
        cart_summary = cart_service.get_user_cart(user_id, db, include_removed=False)
        response += f"🛒 Your cart now has {cart_summary.total_items} item(s) "
        response += f"totaling {cart_summary.total_amount} {cart_summary.currency}"
        
        return response
        
    except Exception as e:
        return f"Error adding to cart: {str(e)}"


@tool
def get_my_cart() -> str:
    """
    View the contents of your shopping cart.
    
    This tool shows all items currently in your cart, including product
    details, quantities, individual prices, and the total amount. Useful
    for reviewing your cart before checkout.
    
    Returns:
        A formatted summary of all cart items with quantities, prices,
        and total amount.
        
    Examples:
        User: "Show my cart"
        User: "What's in my shopping cart?"
        User: "View my cart"
        User: "How much is my cart total?"
        User: "What items do I have in cart?"
    """
    try:
        user_id = _cart_context.get("user_id")
        db = _cart_context.get("db")
        
        if not user_id or not db:
            return "Error: Cart context not set. Please try again."
        
        # Get cart summary
        cart_summary = cart_service.get_user_cart(user_id, db, include_removed=False)
        
        if not cart_summary.items or cart_summary.total_items == 0:
            return "🛒 Your cart is empty. Browse products to add items!"
        
        # Format cart contents
        response = f"🛒 Your Shopping Cart ({cart_summary.total_items} item(s)):\n\n"
        
        for item in cart_summary.items:
            if item.status != 'active':
                continue
                
            # Get product details
            from services.product import service as product_service
            product = product_service.get_product(item.product_id, db)
            
            # Category emoji
            category_emoji = {
                'banking': '🏦',
                'insurance': '🛡️',
                'investment': '📈',
                'cards': '💳'
            }.get(product.category, '📦')
            
            subtotal = float(product.price) * item.quantity
            
            response += f"{category_emoji} Cart Item #{item.id}:\n"
            response += f"   Product: {product.title} (ID: #{product.id})\n"
            response += f"   Quantity: {item.quantity}\n"
            response += f"   Price: {product.price} {product.currency} each\n"
            response += f"   Subtotal: {subtotal:.2f} {product.currency}\n\n"
        
        response += f"{'='*50}\n"
        response += f"💰 Total: {cart_summary.total_amount} {cart_summary.currency}\n\n"
        response += "Ready to checkout? Just say 'checkout with account X' or 'buy everything'"
        
        return response
        
    except Exception as e:
        return f"Error getting cart: {str(e)}"


@tool
def remove_from_cart(cart_item_id: int) -> str:
    """
    Remove an item from your shopping cart.
    
    This tool removes a specific item from your cart using the cart item ID.
    To find cart item IDs, use the get_my_cart tool first.
    
    Args:
        cart_item_id: The ID of the cart item to remove (not product ID)
        
    Returns:
        A confirmation message that the item was removed.
        
    Examples:
        User: "Remove item 5 from cart"
        User: "Delete cart item 3"
        User: "Remove that from my cart"
    """
    try:
        user_id = _cart_context.get("user_id")
        db = _cart_context.get("db")
        
        if not user_id or not db:
            return "Error: Cart context not set. Please try again."
        
        # Get cart item details before removal
        cart_item = cart_service.get_cart_item(cart_item_id, user_id, db)
        
        # Get product details
        from services.product import service as product_service
        product = product_service.get_product(cart_item.product_id, db)
        
        # Remove from cart (soft delete)
        cart_service.remove_from_cart(cart_item_id, user_id, db, soft_delete=True)
        
        # Format response
        response = f"✅ Removed from cart:\n"
        response += f"   • {product.title} (x{cart_item.quantity})\n\n"
        
        # Get updated cart
        cart_summary = cart_service.get_user_cart(user_id, db, include_removed=False)
        if cart_summary.total_items > 0:
            response += f"🛒 Your cart now has {cart_summary.total_items} item(s) "
            response += f"totaling {cart_summary.total_amount} {cart_summary.currency}"
        else:
            response += "🛒 Your cart is now empty."
        
        return response
        
    except Exception as e:
        return f"Error removing from cart: {str(e)}"


@tool
def checkout_cart(account_id: int) -> str:
    """
    Complete the purchase of all items in your cart.
    
    This tool processes the checkout, charging the specified account for
    all items in your cart. The account must have sufficient funds and
    use a compatible currency.
    
    Args:
        account_id: The ID of the account to charge for the purchase
        
    Returns:
        A confirmation message with transaction details and updated balance.
        
    Examples:
        User: "Checkout with account 1"
        User: "Buy everything in my cart using my checking account"
        User: "Complete purchase with account 2"
        User: "Pay for my cart with account 1"
    """
    try:
        user_id = _cart_context.get("user_id")
        db = _cart_context.get("db")
        
        if not user_id or not db:
            return "Error: Cart context not set. Please try again."
        
        # Get cart before checkout
        cart_summary = cart_service.get_user_cart(user_id, db, include_removed=False)
        
        if not cart_summary.items or cart_summary.total_items == 0:
            return "❌ Your cart is empty. Add some products before checking out!"
        
        # Verify account ownership
        from services.account import service as account_service
        account = account_service.get_account(account_id, db)
        
        if account.user_id != user_id:
            return f"Error: You don't have permission to use account {account_id}."
        
        # Check if account has sufficient funds
        total = float(cart_summary.total_amount)
        balance = float(account.balance)
        
        if balance < total:
            return f"❌ Insufficient funds in account {account_id}. " \
                   f"Balance: {balance} {account.currency}, Required: {total} {cart_summary.currency}"
        
        # Create checkout request
        checkout_request = CheckoutRequest(account_id=account_id)
        
        # Process checkout
        checkout_response = cart_service.checkout_cart(user_id, checkout_request, db)
        
        # Format success response
        response = "✅ Purchase Complete!\n\n"
        response += f"📦 Items Purchased: {len(checkout_response.purchased_items)}\n"
        
        for item in checkout_response.purchased_items:
            response += f"   • Product #{item.product_id} (x{item.quantity})\n"
        
        response += f"\n💰 Total Charged: {checkout_response.total_amount} {checkout_response.currency}\n"
        response += f"🏦 Account #{account_id}\n"
        
        # Get updated balance
        updated_account = account_service.get_account(account_id, db)
        response += f"📊 New Balance: {updated_account.balance} {updated_account.currency}\n\n"
        
        if checkout_response.failed_items:
            response += f"⚠️ Note: {len(checkout_response.failed_items)} item(s) could not be purchased"
        else:
            response += "Thank you for your purchase! 🎉"
        
        return response
        
    except Exception as e:
        return f"Error during checkout: {str(e)}"


@tool
def clear_cart() -> str:
    """
    Remove all items from your shopping cart.
    
    This tool empties your entire cart, removing all items at once.
    Use this when you want to start over with a fresh cart.
    
    Returns:
        A confirmation message that the cart was cleared.
        
    Examples:
        User: "Clear my cart"
        User: "Empty my shopping cart"
        User: "Remove everything from cart"
        User: "Start over with a fresh cart"
    """
    try:
        user_id = _cart_context.get("user_id")
        db = _cart_context.get("db")
        
        if not user_id or not db:
            return "Error: Cart context not set. Please try again."
        
        # Get current cart
        cart_summary = cart_service.get_user_cart(user_id, db, include_removed=False)
        items_count = cart_summary.total_items
        
        if items_count == 0:
            return "🛒 Your cart is already empty."
        
        # Clear cart
        cart_service.clear_cart(user_id, db)
        
        return f"✅ Cart cleared! Removed {items_count} item(s) from your cart.\n\n" \
               f"🛒 Your cart is now empty. Browse products to start shopping!"
        
    except Exception as e:
        return f"Error clearing cart: {str(e)}"
