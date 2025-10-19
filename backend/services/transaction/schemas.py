from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


class TransactionBase(BaseModel):
    """Base schema for transaction"""
    amount: Decimal = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(..., description="Currency code: 'KZT'")
    description: Optional[str] = Field(None, max_length=500, description="Transaction description")
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper()
        if v != 'KZT':
            raise ValueError("Currency must be 'KZT'")
        return v


class TransactionDeposit(TransactionBase):
    """Schema for deposit transaction"""
    account_id: int = Field(..., gt=0, description="Account ID to deposit to")


class TransactionWithdrawal(TransactionBase):
    """Schema for withdrawal transaction"""
    account_id: int = Field(..., gt=0, description="Account ID to withdraw from")


class TransactionTransfer(TransactionBase):
    """Schema for transfer between accounts"""
    from_account_id: int = Field(..., gt=0, description="Source account ID")
    to_account_id: int = Field(..., gt=0, description="Destination account ID")
    
    @field_validator('to_account_id')
    @classmethod
    def validate_different_accounts(cls, v: int, info) -> int:
        # Check that from and to accounts are different
        if 'from_account_id' in info.data and v == info.data['from_account_id']:
            raise ValueError("Cannot transfer to the same account")
        return v


class TransactionPurchase(TransactionBase):
    """Schema for product purchase"""
    account_id: int = Field(..., gt=0, description="Account ID to charge from")
    product_id: int = Field(..., gt=0, description="Product ID to purchase")
    quantity: int = Field(default=1, gt=0, description="Quantity of product to purchase")


class TransactionUpdate(BaseModel):
    """Schema for updating transaction"""
    description: Optional[str] = Field(None, max_length=500, description="Updated description")


class TransactionRead(BaseModel):
    """Schema for reading transaction data"""
    id: int
    user_id: int
    account_id: int
    amount: Decimal
    currency: str
    transaction_type: str
    description: Optional[str] = None
    to_user_id: Optional[int] = None
    to_account_id: Optional[int] = None
    product_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionHistoryFilter(BaseModel):
    """Schema for filtering transaction history"""
    account_id: Optional[int] = Field(None, gt=0, description="Filter by account ID")
    transaction_type: Optional[str] = Field(None, description="Filter by transaction type")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum amount")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
    
    @field_validator('transaction_type')
    @classmethod
    def validate_transaction_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_types = ['transfer', 'purchase', 'deposit', 'withdrawal']
            if v not in allowed_types:
                raise ValueError(f"Transaction type must be one of: {', '.join(allowed_types)}")
        return v


class TransactionStats(BaseModel):
    """Schema for transaction statistics"""
    total_transactions: int
    total_deposits: Decimal
    total_withdrawals: Decimal
    total_transfers_sent: Decimal
    total_transfers_received: Decimal
    total_purchases: Decimal
    currency: str

