from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text
from database import Base
from typing import Optional


# SQLAlchemy model for database
class ItemDB(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


# Pydantic model for API
class Item(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Sample Item",
                "description": "This is a sample item description"
            }
        }


# Pydantic model for creating items (without ID)
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "New Item",
                "description": "Description for new item"
            }
        }

