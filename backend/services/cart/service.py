from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.cart import Cart
from models.product import Product
from models.account import Account
from models.user import User
from models.transaction import Transaction
from services.cart.schemas import (
    CartItemRead,
    CartItemCreate,
    CartItemUpdate,
    CartItemWithProduct,
    CartSummary,
    CheckoutRequest,
    CheckoutResponse
)
from typing import List
from datetime import datetime
from decimal import Decimal


def get_cart_item_by_id(
    cart_item_id: int,
    db: Session,
    include_deleted: bool = False
) -> Cart:
    """
    Get cart item by ID with optional deleted filter
    
    Args:
        cart_item_id: Cart item ID
        db: Database session
        include_deleted: Whether to include deleted items
        
    Returns:
        Cart object
        
    Raises:
        HTTPException: If cart item not found
    """
    cart_item = db.query(Cart).filter(Cart.id == cart_item_id).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    if not include_deleted and cart_item.deleted_at:
        raise HTTPException(status_code=404, detail="Cart item is deleted")
    
    return cart_item


def verify_product_available(product_id: int, db: Session) -> Product:
    """
    Verify that product exists and is available for purchase
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Product object
        
    Raises:
        HTTPException: If product not found or not available
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.deleted_at:
        raise HTTPException(status_code=404, detail="Product is deleted")
    
    if product.is_active != 'active':
        raise HTTPException(status_code=400, detail="Product is not available for purchase")
    
    return product


def verify_user_owns_account(user_id: int, account_id: int, db: Session) -> Account:
    """
    Verify that user owns the specified account
    
    Args:
        user_id: User ID
        account_id: Account ID
        db: Database session
        
    Returns:
        Account object
        
    Raises:
        HTTPException: If account not found or user doesn't own it
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account.deleted_at:
        raise HTTPException(status_code=404, detail="Account is deleted")
    
    if account.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this account")
    
    return account


def add_to_cart(
    user_id: int,
    cart_data: CartItemCreate,
    db: Session = Depends(get_db)
) -> CartItemRead:
    """
    Add item to cart or update quantity if already exists
    
    Args:
        user_id: User ID
        cart_data: Cart item data
        db: Database session
        
    Returns:
        Created or updated cart item data
        
    Raises:
        HTTPException: If validation fails
    """
    # Verify product is available
    product = verify_product_available(cart_data.product_id, db)
    
    # Verify account ownership if provided
    if cart_data.account_id:
        verify_user_owns_account(user_id, cart_data.account_id, db)
    
    # Check if item already in cart
    existing_item = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.product_id == cart_data.product_id,
        Cart.status == 'active',
        Cart.deleted_at.is_(None)
    ).first()
    
    if existing_item:
        # Update quantity
        existing_item.quantity += cart_data.quantity
        if cart_data.account_id:
            existing_item.account_id = cart_data.account_id
        existing_item.updated_at = datetime.now()
        
        db.commit()
        db.refresh(existing_item)
        
        return CartItemRead.from_orm(existing_item)
    else:
        # Create new cart item
        new_cart_item = Cart(
            user_id=user_id,
            product_id=cart_data.product_id,
            account_id=cart_data.account_id,
            quantity=cart_data.quantity,
            status='active'
        )
        
        db.add(new_cart_item)
        db.commit()
        db.refresh(new_cart_item)
        
        return CartItemRead.from_orm(new_cart_item)


def get_user_cart(
    user_id: int,
    db: Session = Depends(get_db),
    include_removed: bool = False
) -> CartSummary:
    """
    Get user's cart with product details
    
    Args:
        user_id: User ID
        db: Database session
        include_removed: Whether to include removed items
        
    Returns:
        Cart summary with all items
    """
    # Build query
    query = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.deleted_at.is_(None)
    )
    
    if not include_removed:
        query = query.filter(Cart.status == 'active')
    
    cart_items = query.all()
    
    # Build cart items with product details
    items_with_products = []
    total_amount = Decimal('0.00')
    currency = 'USD'  # Default currency
    has_payment_account = False
    
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        
        if product:
            item_total = product.price * item.quantity
            total_amount += item_total
            currency = product.currency  # Use product's currency
            
            if item.account_id:
                has_payment_account = True
            
            items_with_products.append(CartItemWithProduct(
                id=item.id,
                user_id=item.user_id,
                product_id=item.product_id,
                product_title=product.title,
                product_description=product.description,
                product_price=product.price,
                product_currency=product.currency,
                product_category=product.category,
                account_id=item.account_id,
                quantity=item.quantity,
                item_total=item_total,
                status=item.status,
                created_at=item.created_at
            ))
    
    return CartSummary(
        user_id=user_id,
        total_items=sum(item.quantity for item in cart_items),
        total_products=len(cart_items),
        total_amount=total_amount,
        currency=currency,
        items=items_with_products,
        has_payment_account=has_payment_account
    )


def get_cart_item(
    cart_item_id: int,
    user_id: int,
    db: Session = Depends(get_db)
) -> CartItemRead:
    """
    Get specific cart item
    
    Args:
        cart_item_id: Cart item ID
        user_id: User ID (for permission check)
        db: Database session
        
    Returns:
        Cart item data
        
    Raises:
        HTTPException: If cart item not found or user doesn't own it
    """
    cart_item = get_cart_item_by_id(cart_item_id, db)
    
    # Verify user owns this cart item
    if cart_item.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this cart item")
    
    return CartItemRead.from_orm(cart_item)


def update_cart_item(
    cart_item_id: int,
    user_id: int,
    cart_data: CartItemUpdate,
    db: Session = Depends(get_db)
) -> CartItemRead:
    """
    Update cart item
    
    Args:
        cart_item_id: Cart item ID
        user_id: User ID (for permission check)
        cart_data: Updated cart data
        db: Database session
        
    Returns:
        Updated cart item data
        
    Raises:
        HTTPException: If cart item not found or user doesn't own it
    """
    cart_item = get_cart_item_by_id(cart_item_id, db)
    
    # Verify user owns this cart item
    if cart_item.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this cart item")
    
    # Verify account ownership if provided
    if cart_data.account_id:
        verify_user_owns_account(user_id, cart_data.account_id, db)
    
    # Update only provided fields
    update_data = cart_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(cart_item, field, value)
    
    cart_item.updated_at = datetime.now()
    
    db.commit()
    db.refresh(cart_item)
    
    return CartItemRead.from_orm(cart_item)


def remove_from_cart(
    cart_item_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    soft_delete: bool = True
) -> dict:
    """
    Remove item from cart
    
    Args:
        cart_item_id: Cart item ID
        user_id: User ID (for permission check)
        db: Database session
        soft_delete: If True, marks as removed; if False, deletes from database
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If cart item not found or user doesn't own it
    """
    cart_item = get_cart_item_by_id(cart_item_id, db)
    
    # Verify user owns this cart item
    if cart_item.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this cart item")
    
    if soft_delete:
        # Soft delete: mark as removed
        cart_item.status = 'removed'
        cart_item.deleted_at = datetime.now()
        db.commit()
        return {"message": "Item removed from cart"}
    else:
        # Hard delete: remove from database
        db.delete(cart_item)
        db.commit()
        return {"message": "Item permanently deleted from cart"}


def clear_cart(
    user_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Clear all items from user's cart
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Success message with count of removed items
    """
    # Get all active cart items
    cart_items = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.status == 'active',
        Cart.deleted_at.is_(None)
    ).all()
    
    count = len(cart_items)
    
    # Mark all as removed
    for item in cart_items:
        item.status = 'removed'
        item.deleted_at = datetime.now()
    
    db.commit()
    
    return {"message": f"Cart cleared successfully", "items_removed": count}


def checkout(
    user_id: int,
    checkout_data: CheckoutRequest,
    db: Session = Depends(get_db)
) -> CheckoutResponse:
    """
    Checkout and purchase all items in cart
    
    Args:
        user_id: User ID
        checkout_data: Checkout request with account ID
        db: Database session
        
    Returns:
        Checkout response with transaction details
        
    Raises:
        HTTPException: If validation fails or insufficient funds
    """
    # Verify account ownership and status
    account = verify_user_owns_account(user_id, checkout_data.account_id, db)
    
    if account.status != 'active':
        raise HTTPException(
            status_code=400,
            detail=f"Account is {account.status}. Only active accounts can make purchases"
        )
    
    # Get active cart items
    cart_items = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.status == 'active',
        Cart.deleted_at.is_(None)
    ).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate total and verify products
    total_amount = Decimal('0.00')
    currency = account.currency
    transaction_ids = []
    
    for item in cart_items:
        product = verify_product_available(item.product_id, db)
        
        # Verify currency matches
        if product.currency != currency:
            raise HTTPException(
                status_code=400,
                detail=f"Product '{product.title}' uses {product.currency}, but account uses {currency}"
            )
        
        item_total = product.price * item.quantity
        total_amount += item_total
    
    # Check sufficient funds
    if account.balance < total_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Required: {total_amount} {currency}, Available: {account.balance} {currency}"
        )
    
    # Process purchases
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        item_total = product.price * item.quantity
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            account_id=checkout_data.account_id,
            amount=item_total,
            currency=currency,
            transaction_type='purchase',
            description=f"Purchase of {product.title} (x{item.quantity})",
            product_id=item.product_id
        )
        
        db.add(transaction)
        db.flush()  # Get transaction ID
        
        transaction_ids.append(transaction.id)
        
        # Update cart item status
        item.status = 'purchased'
        item.account_id = checkout_data.account_id
        item.updated_at = datetime.now()
    
    # Update account balance
    account.balance -= total_amount
    account.updated_at = datetime.now()
    
    db.commit()
    
    return CheckoutResponse(
        success=True,
        message="Checkout completed successfully",
        transaction_ids=transaction_ids,
        total_amount=total_amount,
        currency=currency,
        items_purchased=len(cart_items)
    )


def set_payment_account(
    user_id: int,
    account_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Set payment account for all items in cart
    
    Args:
        user_id: User ID
        account_id: Account ID to use for payment
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If account not found or user doesn't own it
    """
    # Verify account ownership
    verify_user_owns_account(user_id, account_id, db)
    
    # Update all active cart items
    cart_items = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.status == 'active',
        Cart.deleted_at.is_(None)
    ).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    count = 0
    for item in cart_items:
        item.account_id = account_id
        item.updated_at = datetime.now()
        count += 1
    
    db.commit()
    
    return {"message": f"Payment account set for {count} cart items"}


def get_cart_history(
    user_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> List[CartItemRead]:
    """
    Get user's cart history (purchased and removed items)
    
    Args:
        user_id: User ID
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of historical cart items
    """
    cart_items = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.status.in_(['purchased', 'removed'])
    ).order_by(Cart.updated_at.desc()).offset(skip).limit(limit).all()
    
    return [CartItemRead.from_orm(item) for item in cart_items]

