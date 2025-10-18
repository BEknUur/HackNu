from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from database import get_db
from services.cart import service
from services.cart.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartItemRead,
    CartSummary,
    CheckoutRequest,
    CheckoutResponse
)
from typing import List

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/", response_model=CartItemRead, status_code=201)
def add_to_cart(
    user_id: int = Query(..., gt=0, description="User ID"),
    cart_data: CartItemCreate = ...,
    db: Session = Depends(get_db)
):
    """
    Add item to cart.
    
    If the product already exists in the cart, the quantity will be incremented.
    
    **Required fields:**
    - product_id: Product to add
    - user_id: User ID (query parameter)
    
    **Optional fields:**
    - quantity: Quantity to add (default: 1)
    - account_id: Payment account (can be set later)
    """
    return service.add_to_cart(user_id, cart_data, db)


@router.get("/", response_model=CartSummary)
def get_user_cart(
    user_id: int = Query(..., gt=0, description="User ID"),
    include_removed: bool = Query(False, description="Include removed items"),
    db: Session = Depends(get_db)
):
    """
    Get user's shopping cart with full details.
    
    Returns cart summary including:
    - All cart items with product details
    - Total items count
    - Total amount
    - Currency information
    
    **Query parameters:**
    - user_id: User ID (required)
    - include_removed: Include removed items (default: False)
    """
    return service.get_user_cart(user_id, db, include_removed)


@router.get("/history", response_model=List[CartItemRead])
def get_cart_history(
    user_id: int = Query(..., gt=0, description="User ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get user's cart history (purchased and removed items).
    
    **Query parameters:**
    - user_id: User ID (required)
    - skip: Pagination offset
    - limit: Maximum results to return
    """
    return service.get_cart_history(user_id, db, skip, limit)


@router.get("/{cart_item_id}", response_model=CartItemRead)
def get_cart_item(
    cart_item_id: int = Path(..., gt=0, description="Cart item ID"),
    user_id: int = Query(..., gt=0, description="User ID for permission check"),
    db: Session = Depends(get_db)
):
    """
    Get specific cart item by ID.
    
    **Path parameters:**
    - cart_item_id: Cart item ID
    
    **Query parameters:**
    - user_id: User ID for permission verification
    """
    return service.get_cart_item(cart_item_id, user_id, db)


@router.put("/{cart_item_id}", response_model=CartItemRead)
def update_cart_item(
    cart_item_id: int = Path(..., gt=0, description="Cart item ID"),
    user_id: int = Query(..., gt=0, description="User ID for permission check"),
    cart_data: CartItemUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Update cart item.
    
    **Updatable fields:**
    - quantity: Update quantity
    - account_id: Update payment account
    - status: Update status ('active', 'purchased', 'removed')
    
    All fields are optional - only provided fields will be updated.
    
    **Path parameters:**
    - cart_item_id: Cart item ID
    
    **Query parameters:**
    - user_id: User ID for permission verification
    """
    return service.update_cart_item(cart_item_id, user_id, cart_data, db)


@router.delete("/{cart_item_id}")
def remove_from_cart(
    cart_item_id: int = Path(..., gt=0, description="Cart item ID"),
    user_id: int = Query(..., gt=0, description="User ID for permission check"),
    soft_delete: bool = Query(True, description="Soft delete (True) or hard delete (False)"),
    db: Session = Depends(get_db)
):
    """
    Remove item from cart.
    
    **Path parameters:**
    - cart_item_id: Cart item ID
    
    **Query parameters:**
    - user_id: User ID for permission verification
    - soft_delete: If True, marks as removed; if False, deletes permanently (default: True)
    """
    return service.remove_from_cart(cart_item_id, user_id, db, soft_delete)


@router.delete("/")
def clear_cart(
    user_id: int = Query(..., gt=0, description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Clear all items from cart.
    
    Marks all active cart items as removed.
    
    **Query parameters:**
    - user_id: User ID
    """
    return service.clear_cart(user_id, db)


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(
    user_id: int = Query(..., gt=0, description="User ID"),
    checkout_data: CheckoutRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Checkout and purchase all items in cart.
    
    This will:
    1. Verify account has sufficient funds
    2. Create purchase transactions for each item
    3. Deduct total amount from account
    4. Mark cart items as purchased
    
    **Required fields:**
    - account_id: Account to charge from
    - user_id: User ID (query parameter)
    
    **Query parameters:**
    - user_id: User ID
    
    **Returns:**
    - Transaction IDs for all purchases
    - Total amount charged
    - Number of items purchased
    
    **Note:** All items must use the same currency as the payment account.
    """
    return service.checkout(user_id, checkout_data, db)


@router.post("/payment-account")
def set_payment_account(
    user_id: int = Query(..., gt=0, description="User ID"),
    account_id: int = Query(..., gt=0, description="Account ID for payment"),
    db: Session = Depends(get_db)
):
    """
    Set payment account for all items in cart.
    
    Updates the payment account for all active cart items.
    
    **Query parameters:**
    - user_id: User ID
    - account_id: Account ID to use for payment
    """
    return service.set_payment_account(user_id, account_id, db)

