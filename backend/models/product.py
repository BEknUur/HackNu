from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Decimal
from database import Base
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    price = Column(Decimal(15, 2), nullable=False)
    currency = Column(String(3), default='USD')  # 'USD', 'EUR', 'KZT'
    category = Column(String, nullable=True)  # 'banking', 'insurance', 'investment'
    is_active = Column(String, default='active')  # 'active', 'inactive'
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="product")
    carts = relationship("Cart", back_populates="product")