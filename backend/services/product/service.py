from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from database import get_db
from models.product import Product
from models.transaction import Transaction
from models.cart import Cart
from services.product.schemas import (
    ProductRead,
    ProductCreate,
    ProductUpdate,
    ProductSearch,
    ProductStats,
    CategoryStats
)
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


def get_product_by_id(
    product_id: int,
    db: Session,
    include_deleted: bool = False,
    include_inactive: bool = False
) -> Product:
    """
    Get product by ID with optional filters
    
    Args:
        product_id: Product ID
        db: Database session
        include_deleted: Whether to include deleted products
        include_inactive: Whether to include inactive products
        
    Returns:
        Product object
        
    Raises:
        HTTPException: If product not found
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not include_deleted and product.deleted_at:
        raise HTTPException(status_code=404, detail="Product is deleted")
    
    if not include_inactive and product.is_active != 'active':
        raise HTTPException(status_code=404, detail="Product is inactive")
    
    return product


def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
) -> ProductRead:
    """
    Create a new product
    
    Args:
        product_data: Product creation data
        db: Database session
        
    Returns:
        Created product data
    """
    # Create new product
    new_product = Product(
        title=product_data.title,
        description=product_data.description,
        price=product_data.price,
        currency=product_data.currency,
        category=product_data.category,
        is_active='active'
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return ProductRead.from_orm(new_product)


def get_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> ProductRead:
    """
    Get product by ID
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Product data
        
    Raises:
        HTTPException: If product not found
    """
    product = get_product_by_id(product_id, db)
    return ProductRead.from_orm(product)


def get_all_products(
    db: Session = Depends(get_db),
    include_deleted: bool = False,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[ProductRead]:
    """
    Get all products with pagination
    
    Args:
        db: Database session
        include_deleted: Whether to include deleted products
        include_inactive: Whether to include inactive products
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of products
    """
    query = db.query(Product)
    
    if not include_deleted:
        query = query.filter(Product.deleted_at.is_(None))
    
    if not include_inactive:
        query = query.filter(Product.is_active == 'active')
    
    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    
    return [ProductRead.from_orm(product) for product in products]


def search_products(
    db: Session = Depends(get_db),
    filters: Optional[ProductSearch] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ProductRead]:
    """
    Search products with filters
    
    Args:
        db: Database session
        filters: Search filters
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of matching products
    """
    query = db.query(Product).filter(Product.deleted_at.is_(None))
    
    # Apply filters if provided
    if filters:
        # Search in title and description
        if filters.search_query:
            search_pattern = f"%{filters.search_query}%"
            query = query.filter(
                or_(
                    Product.title.ilike(search_pattern),
                    Product.description.ilike(search_pattern)
                )
            )
        
        if filters.category:
            query = query.filter(Product.category == filters.category)
        
        if filters.min_price is not None:
            query = query.filter(Product.price >= filters.min_price)
        
        if filters.max_price is not None:
            query = query.filter(Product.price <= filters.max_price)
        
        if filters.currency:
            query = query.filter(Product.currency == filters.currency)
        
        if filters.is_active:
            query = query.filter(Product.is_active == filters.is_active)
        else:
            # Default: only active products
            query = query.filter(Product.is_active == 'active')
    else:
        # Default: only active products
        query = query.filter(Product.is_active == 'active')
    
    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    
    return [ProductRead.from_orm(product) for product in products]


def get_products_by_category(
    category: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> List[ProductRead]:
    """
    Get all products in a specific category
    
    Args:
        category: Product category
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of products in category
    """
    # Validate category
    allowed_categories = ['banking', 'insurance', 'investment', 'cards']
    if category not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(allowed_categories)}"
        )
    
    products = db.query(Product).filter(
        Product.category == category,
        Product.is_active == 'active',
        Product.deleted_at.is_(None)
    ).order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    
    return [ProductRead.from_orm(product) for product in products]


def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
) -> ProductRead:
    """
    Update product information
    
    Args:
        product_id: Product ID
        product_data: Updated product data
        db: Database session
        
    Returns:
        Updated product data
        
    Raises:
        HTTPException: If product not found
    """
    product = get_product_by_id(product_id, db, include_inactive=True)
    
    # Update only provided fields
    update_data = product_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    product.updated_at = datetime.now()
    
    db.commit()
    db.refresh(product)
    
    return ProductRead.from_orm(product)


def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    soft_delete: bool = True
) -> dict:
    """
    Delete product (soft or hard delete)
    
    Args:
        product_id: Product ID
        db: Database session
        soft_delete: If True, marks product as deleted; if False, removes from database
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If product not found
    """
    product = get_product_by_id(product_id, db, include_inactive=True)
    
    # Check if product is used in any active carts
    active_carts = db.query(Cart).filter(
        Cart.product_id == product_id,
        Cart.status == 'active',
        Cart.deleted_at.is_(None)
    ).count()
    
    if active_carts > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete product. It's in {active_carts} active cart(s). Remove from carts first."
        )
    
    if soft_delete:
        # Soft delete: mark as deleted and inactive
        product.deleted_at = datetime.now()
        product.is_active = 'inactive'
        db.commit()
        return {"message": "Product soft deleted successfully"}
    else:
        # Hard delete: remove from database
        db.delete(product)
        db.commit()
        return {"message": "Product permanently deleted"}


def restore_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> ProductRead:
    """
    Restore a soft-deleted product
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Restored product data
        
    Raises:
        HTTPException: If product not found or not deleted
    """
    product = get_product_by_id(product_id, db, include_deleted=True, include_inactive=True)
    
    if not product.deleted_at:
        raise HTTPException(status_code=400, detail="Product is not deleted")
    
    # Restore product
    product.deleted_at = None
    product.is_active = 'active'
    product.updated_at = datetime.now()
    
    db.commit()
    db.refresh(product)
    
    return ProductRead.from_orm(product)


def activate_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> ProductRead:
    """
    Activate a product
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Updated product data
        
    Raises:
        HTTPException: If product not found
    """
    product = get_product_by_id(product_id, db, include_inactive=True)
    
    if product.is_active == 'active':
        raise HTTPException(status_code=400, detail="Product is already active")
    
    product.is_active = 'active'
    product.updated_at = datetime.now()
    
    db.commit()
    db.refresh(product)
    
    return ProductRead.from_orm(product)


def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> ProductRead:
    """
    Deactivate a product
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Updated product data
        
    Raises:
        HTTPException: If product not found
    """
    product = get_product_by_id(product_id, db)
    
    if product.is_active == 'inactive':
        raise HTTPException(status_code=400, detail="Product is already inactive")
    
    product.is_active = 'inactive'
    product.updated_at = datetime.now()
    
    db.commit()
    db.refresh(product)
    
    return ProductRead.from_orm(product)


def get_product_stats(
    product_id: int,
    db: Session = Depends(get_db)
) -> ProductStats:
    """
    Get statistics for a specific product
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Product statistics
        
    Raises:
        HTTPException: If product not found
    """
    product = get_product_by_id(product_id, db, include_inactive=True)
    
    # Count purchases from transactions
    purchases = db.query(Transaction).filter(
        Transaction.product_id == product_id,
        Transaction.transaction_type == 'purchase',
        Transaction.deleted_at.is_(None)
    ).all()
    
    total_purchases = len(purchases)
    total_revenue = sum(t.amount for t in purchases)
    
    # Count items in active carts
    total_in_carts = db.query(func.sum(Cart.quantity)).filter(
        Cart.product_id == product_id,
        Cart.status == 'active',
        Cart.deleted_at.is_(None)
    ).scalar() or 0
    
    return ProductStats(
        product_id=product.id,
        product_title=product.title,
        total_purchases=total_purchases,
        total_revenue=Decimal(str(total_revenue)),
        currency=product.currency,
        total_in_carts=int(total_in_carts)
    )


def get_category_stats(
    category: str,
    db: Session = Depends(get_db)
) -> CategoryStats:
    """
    Get statistics for a product category
    
    Args:
        category: Category name
        db: Database session
        
    Returns:
        Category statistics
    """
    # Validate category
    allowed_categories = ['banking', 'insurance', 'investment', 'cards']
    if category not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(allowed_categories)}"
        )
    
    # Count products
    total_products = db.query(Product).filter(
        Product.category == category,
        Product.deleted_at.is_(None)
    ).count()
    
    active_products = db.query(Product).filter(
        Product.category == category,
        Product.is_active == 'active',
        Product.deleted_at.is_(None)
    ).count()
    
    # Get product IDs in this category
    product_ids = [p.id for p in db.query(Product.id).filter(
        Product.category == category,
        Product.deleted_at.is_(None)
    ).all()]
    
    # Count purchases
    purchases = db.query(Transaction).filter(
        Transaction.product_id.in_(product_ids),
        Transaction.transaction_type == 'purchase',
        Transaction.deleted_at.is_(None)
    ).all()
    
    total_purchases = len(purchases)
    total_revenue = sum(t.amount for t in purchases)
    
    return CategoryStats(
        category=category,
        total_products=total_products,
        active_products=active_products,
        total_purchases=total_purchases,
        total_revenue=Decimal(str(total_revenue))
    )


def get_featured_products(
    db: Session = Depends(get_db),
    limit: int = 10
) -> List[ProductRead]:
    """
    Get featured products (most purchased)
    
    Args:
        db: Database session
        limit: Maximum number of products to return
        
    Returns:
        List of featured products
    """
    # Get products with purchase counts
    product_purchases = db.query(
        Product,
        func.count(Transaction.id).label('purchase_count')
    ).outerjoin(
        Transaction,
        (Transaction.product_id == Product.id) & 
        (Transaction.transaction_type == 'purchase') &
        (Transaction.deleted_at.is_(None))
    ).filter(
        Product.is_active == 'active',
        Product.deleted_at.is_(None)
    ).group_by(Product.id).order_by(
        func.count(Transaction.id).desc()
    ).limit(limit).all()
    
    return [ProductRead.from_orm(product) for product, _ in product_purchases]

