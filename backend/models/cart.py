from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from database import Base
from sqlalchemy.orm import relationship

class Cart(Base):
    __tablename__ = "carts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)  # Счет для оплаты
    quantity = Column(Integer, default=1)
    status = Column(String, default="active")  # 'active', 'purchased', 'removed'
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="carts")
    product = relationship("Product", back_populates="carts")
    account = relationship("Account")