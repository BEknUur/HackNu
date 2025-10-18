from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    title: str = Field(..., min_length=2, max_length=200, description="Product title")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    price: Decimal = Field(..., gt=0, description="Product price (must be positive)")
    currency: str = Field(default='USD', description="Currency code: 'USD', 'EUR', 'KZT'")
    category: Optional[str] = Field(None, description="Product category: 'banking', 'insurance', 'investment', 'cards'")
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        allowed_currencies = ['USD', 'EUR', 'KZT']
        v = v.upper()
        if v not in allowed_currencies:
            raise ValueError(f"Currency must be one of: {', '.join(allowed_currencies)}")
        return v
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_categories = ['banking', 'insurance', 'investment', 'cards']
            if v not in allowed_categories:
                raise ValueError(f"Category must be one of: {', '.join(allowed_categories)}")
        return v


class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    title: Optional[str] = Field(None, min_length=2, max_length=200, description="Product title")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    price: Optional[Decimal] = Field(None, gt=0, description="Product price (must be positive)")
    currency: Optional[str] = Field(None, description="Currency code: 'USD', 'EUR', 'KZT'")
    category: Optional[str] = Field(None, description="Product category")
    is_active: Optional[str] = Field(None, description="Product status: 'active', 'inactive'")
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_currencies = ['USD', 'EUR', 'KZT']
            v = v.upper()
            if v not in allowed_currencies:
                raise ValueError(f"Currency must be one of: {', '.join(allowed_currencies)}")
        return v
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_categories = ['banking', 'insurance', 'investment', 'cards']
            if v not in allowed_categories:
                raise ValueError(f"Category must be one of: {', '.join(allowed_categories)}")
        return v
    
    @field_validator('is_active')
    @classmethod
    def validate_is_active(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_statuses = ['active', 'inactive']
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class ProductRead(BaseModel):
    """Schema for reading product data"""
    id: int
    title: str
    description: Optional[str] = None
    price: Decimal
    currency: str
    category: Optional[str] = None
    is_active: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductSearch(BaseModel):
    """Schema for searching products"""
    search_query: Optional[str] = Field(None, description="Search in title and description")
    category: Optional[str] = Field(None, description="Filter by category")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price")
    currency: Optional[str] = Field(None, description="Filter by currency")
    is_active: Optional[str] = Field(None, description="Filter by status")
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_categories = ['banking', 'insurance', 'investment', 'cards']
            if v not in allowed_categories:
                raise ValueError(f"Category must be one of: {', '.join(allowed_categories)}")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_currencies = ['USD', 'EUR', 'KZT']
            v = v.upper()
            if v not in allowed_currencies:
                raise ValueError(f"Currency must be one of: {', '.join(allowed_currencies)}")
        return v
    
    @field_validator('is_active')
    @classmethod
    def validate_is_active(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_statuses = ['active', 'inactive']
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class ProductStats(BaseModel):
    """Schema for product statistics"""
    product_id: int
    product_title: str
    total_purchases: int
    total_revenue: Decimal
    currency: str
    total_in_carts: int


class CategoryStats(BaseModel):
    """Schema for category statistics"""
    category: str
    total_products: int
    active_products: int
    total_purchases: int
    total_revenue: Decimal

