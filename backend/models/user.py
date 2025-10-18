from datetime import datetime
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    DateTime,
)
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)

    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)

    password_hash = Column(String)
    avatar = Column(String, nullable=True) # path to the avatar file

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)
