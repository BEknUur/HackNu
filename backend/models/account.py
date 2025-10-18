from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Decimal
from database import Base
from sqlalchemy.orm import relationship

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_type = Column(String, nullable=False)  # 'checking', 'savings', 'credit'
    balance = Column(Decimal(15, 2), default=0.00)
    currency = Column(String(3), default='USD')  # 'USD', 'EUR', 'KZT'
    status = Column(String, default='active')  # 'active', 'blocked', 'closed'
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
