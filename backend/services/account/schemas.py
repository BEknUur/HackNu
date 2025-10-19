from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


class AccountCreate(BaseModel):
    """Schema for creating a new account"""
    user_id: int = Field(..., gt=0, description="User ID who owns the account")
    account_type: str = Field(..., description="Account type: 'checking', 'savings', 'credit'")
    balance: Optional[Decimal] = Field(default=Decimal('0.00'), ge=0, description="Initial account balance")
    currency: str = Field(default='KZT', description="Currency code: 'KZT'")
    
    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        allowed_types = ['checking', 'savings', 'credit']
        if v not in allowed_types:
            raise ValueError(f"Account type must be one of: {', '.join(allowed_types)}")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper()
        if v != 'KZT':
            raise ValueError("Currency must be 'KZT'")
        return v


class AccountUpdate(BaseModel):
    """Schema for updating an existing account"""
    account_type: Optional[str] = Field(None, description="Account type: 'checking', 'savings', 'credit'")
    balance: Optional[Decimal] = Field(None, ge=0, description="Account balance")
    currency: Optional[str] = Field(None, description="Currency code: 'KZT'")
    status: Optional[str] = Field(None, description="Account status: 'active', 'blocked', 'closed'")
    
    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_types = ['checking', 'savings', 'credit']
            if v not in allowed_types:
                raise ValueError(f"Account type must be one of: {', '.join(allowed_types)}")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.upper()
            if v != 'KZT':
                raise ValueError("Currency must be 'KZT'")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_statuses = ['active', 'blocked', 'closed']
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class AccountRead(BaseModel):
    """Schema for reading account data"""
    id: int
    user_id: int
    account_type: str
    balance: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccountBalanceUpdate(BaseModel):
    """Schema for updating account balance (deposit/withdraw)"""
    amount: Decimal = Field(..., gt=0, description="Amount to deposit or withdraw")
    operation: str = Field(..., description="Operation type: 'deposit' or 'withdraw'")
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v: str) -> str:
        allowed_operations = ['deposit', 'withdraw']
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v

