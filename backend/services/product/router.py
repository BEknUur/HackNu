from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from database import get_db
from services.product import service
from services.product.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductRead,
    ProductSearch,
    ProductStats,
    CategoryStats
)
from typing import List, Optional
from decimal import Decimal

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductRead, status_code=201)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product.
    
    **Required fields:**
    - title: Product title
    - price: Product price (must be positive)
    
    **Optional fields:**
    - description: Product description
    - currency: Currency code (default: 'USD')
    - category: Product category ('banking', 'insurance', 'investment', 'cards')
    """
    return service.create_product(product_data, db)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    db: Session = Depends(get_db)
):
    """
    Get product details by ID.
    
    Returns only active, non-deleted products.
    """
    return service.get_product(product_id, db)


@router.get("/", response_model=List[ProductRead])
def get_all_products(
    include_deleted: bool = Query(False, description="Include deleted products"),
    include_inactive: bool = Query(False, description="Include inactive products"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all products with pagination.
    
    **Query parameters:**
    - include_deleted: Include soft-deleted products
    - include_inactive: Include inactive products
    - skip: Pagination offset
    - limit: Maximum results to return (max: 1000)
    
    By default, returns only active, non-deleted products.
    """
    return service.get_all_products(db, include_deleted, include_inactive, skip, limit)


@router.post("/search", response_model=List[ProductRead])
def search_products(
    search_query: Optional[str] = Query(None, description="Search in title and description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    is_active: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Search products with filters.
    
    **Query parameters:**
    - search_query: Search text (searches in title and description)
    - category: Filter by category ('banking', 'insurance', 'investment', 'cards')
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - currency: Filter by currency ('USD', 'EUR', 'KZT')
    - is_active: Filter by status ('active', 'inactive')
    - skip: Pagination offset
    - limit: Maximum results to return
    
    All filters are optional. By default returns only active products.
    """
    # Build filters
    filters = ProductSearch(
        search_query=search_query,
        category=category,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
        currency=currency,
        is_active=is_active
    )
    
    return service.search_products(db, filters, skip, limit)


@router.get("/category/{category}", response_model=List[ProductRead])
def get_products_by_category(
    category: str = Path(..., description="Product category"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all products in a specific category.
    
    **Path parameters:**
    - category: One of 'banking', 'insurance', 'investment', 'cards'
    
    Returns only active, non-deleted products in the specified category.
    """
    return service.get_products_by_category(category, db, skip, limit)


@router.get("/featured/top", response_model=List[ProductRead])
def get_featured_products(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of products to return"),
    db: Session = Depends(get_db)
):
    """
    Get featured products (most purchased).
    
    Returns the most popular products based on purchase count.
    
    **Query parameters:**
    - limit: Maximum number of products to return (default: 10, max: 50)
    """
    return service.get_featured_products(db, limit)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    product_data: ProductUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Update product information.
    
    **Updatable fields:**
    - title: Product title
    - description: Product description
    - price: Product price
    - currency: Currency code
    - category: Product category
    - is_active: Product status ('active', 'inactive')
    
    All fields are optional - only provided fields will be updated.
    """
    return service.update_product(product_id, product_data, db)


@router.delete("/{product_id}")
def delete_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    soft_delete: bool = Query(True, description="Soft delete (True) or hard delete (False)"),
    db: Session = Depends(get_db)
):
    """
    Delete a product.
    
    **Query parameters:**
    - soft_delete: If True, marks product as deleted; if False, permanently removes it (default: True)
    
    **Note:** Cannot delete products that are in active shopping carts.
    """
    return service.delete_product(product_id, db, soft_delete)


@router.post("/{product_id}/restore", response_model=ProductRead)
def restore_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted product.
    
    Sets the product status back to 'active' and clears the deleted_at timestamp.
    """
    return service.restore_product(product_id, db)


@router.post("/{product_id}/activate", response_model=ProductRead)
def activate_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    db: Session = Depends(get_db)
):
    """
    Activate a product.
    
    Makes the product available for purchase.
    """
    return service.activate_product(product_id, db)


@router.post("/{product_id}/deactivate", response_model=ProductRead)
def deactivate_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    db: Session = Depends(get_db)
):
    """
    Deactivate a product.
    
    Makes the product unavailable for purchase without deleting it.
    """
    return service.deactivate_product(product_id, db)


@router.get("/{product_id}/stats", response_model=ProductStats)
def get_product_stats(
    product_id: int = Path(..., gt=0, description="Product ID"),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific product.
    
    Returns:
    - Total number of purchases
    - Total revenue generated
    - Number of items currently in shopping carts
    """
    return service.get_product_stats(product_id, db)


@router.get("/category/{category}/stats", response_model=CategoryStats)
def get_category_stats(
    category: str = Path(..., description="Product category"),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a product category.
    
    **Path parameters:**
    - category: One of 'banking', 'insurance', 'investment', 'cards'
    
    Returns:
    - Total products in category
    - Active products count
    - Total purchases
    - Total revenue
    """
    return service.get_category_stats(category, db)

