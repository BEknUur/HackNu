from pydantic import BaseModel, EmailStr, Field
from datetime import datetime 


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    surname: str = Field(..., min_length=2, max_length=50)
    email: EmailStr = Field(..., unique=True)
    phone: str = Field(..., unique=True)
    password: str = Field(..., min_length=8)
    avatar: str = Field(..., nullable=True)

class UserLogin(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

class User(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
    surname: str = Field(...)
    email: EmailStr = Field(...)
    phone: str = Field(...)
    avatar: str = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    deleted_at: datetime = Field(...)