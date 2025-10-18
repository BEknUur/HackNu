from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class CartItemCreate(BaseModel):
    """Schema for adding item to cart"""
    product_id: int = Field(..., gt=0, description="Product ID to add to cart")
    quantity: int = Field(default=1, gt=0, description="Quantity of product")
    account_id: Optional[int] = Field(None, gt=0, description="Account ID for payment (optional)")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v > 100:
            raise ValueError("Quantity cannot exceed 100")
        return v


class CartItemUpdate(BaseModel):
    """Schema for updating cart item"""
    quantity: Optional[int] = Field(None, gt=0, description="Updated quantity")
    account_id: Optional[int] = Field(None, gt=0, description="Updated payment account")
    status: Optional[str] = Field(None, description="Cart item status")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v > 100:
            raise ValueError("Quantity cannot exceed 100")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_statuses = ['active', 'purchased', 'removed']
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class CartItemRead(BaseModel):
    """Schema for reading cart item data"""
    id: int
    user_id: int
    product_id: int
    account_id: Optional[int] = None
    quantity: int
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CartItemWithProduct(BaseModel):
    """Schema for cart item with product details"""
    id: int
    user_id: int
    product_id: int
    product_title: str
    product_description: Optional[str] = None
    product_price: Decimal
    product_currency: str
    product_category: Optional[str] = None
    account_id: Optional[int] = None
    quantity: int
    item_total: Decimal  # price * quantity
    status: str
    created_at: datetime


class CartSummary(BaseModel):
    """Schema for cart summary"""
    user_id: int
    total_items: int
    total_products: int  # unique products
    total_amount: Decimal
    currency: str
    items: List[CartItemWithProduct]
    has_payment_account: bool


class CheckoutRequest(BaseModel):
    """Schema for checkout request"""
    account_id: int = Field(..., gt=0, description="Account ID to charge from")


class CheckoutResponse(BaseModel):
    """Schema for checkout response"""
    success: bool
    message: str
    transaction_ids: List[int]
    total_amount: Decimal
    currency: str
    items_purchased: int

