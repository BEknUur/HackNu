from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Decimal
from database import Base
from sqlalchemy.orm import relationship

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    amount = Column(Decimal(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    transaction_type = Column(String, nullable=False)  # 'transfer', 'purchase', 'deposit', 'withdrawal'
    description = Column(String)
    
    # Для переводов
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    
    # Для покупок
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    to_user = relationship("User", foreign_keys=[to_user_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])
    product = relationship("Product", back_populates="transactions")