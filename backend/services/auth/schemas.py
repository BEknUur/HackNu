from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: str = Field(..., min_length=2, max_length=50, description="User's first name")
    surname: str = Field(..., min_length=2, max_length=50, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    phone: str = Field(..., description="User's phone number")
    password: str = Field(..., min_length=8, description="User's password (min 8 characters)")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserRead(BaseModel):
    """Schema for reading user data"""
    id: int
    name: str
    surname: str
    email: EmailStr
    phone: str
    avatar: Optional[str] = Field(None, description="Avatar filename (for Face ID)")
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
