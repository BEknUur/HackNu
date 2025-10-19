from fastapi import HTTPException, Depends, UploadFile
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
from models.user import User
from models.account import Account
from services.auth.schemas import UserRead
from typing import Optional
from decimal import Decimal
import os
from pathlib import Path

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

AVATARS_DIR = Path("uploads/avatars")
AVATARS_DIR.mkdir(parents=True, exist_ok=True)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(password, password_hash)


def save_avatar_file(file_data: bytes, user_id: int) -> str:
    """
    Save avatar file to disk
    
    Args:
        file_data: Image file bytes
        user_id: User ID
        
    Returns:
        Filename of saved avatar
    """
    filename = f"user_{user_id}_avatar.jpg"
    filepath = AVATARS_DIR / filename
    
    with open(filepath, 'wb') as f:
        f.write(file_data)
    
    return filename


async def create_user(
    name: str,
    surname: str,
    email: str,
    phone: str,
    password: str,
    avatar_file: Optional[UploadFile] = None,
    db: Session = Depends(get_db)
) -> UserRead:
    """
    Create a new user with optional avatar
    
    Args:
        name: User's first name
        surname: User's last name
        email: User's email
        phone: User's phone number
        password: User's password
        avatar_file: Optional avatar image file
        db: Database session
        
    Returns:
        Created user data
    """
    # Check if email already exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if phone already exists
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    # Create user without avatar first
    new_user = User(
        name=name,
        surname=surname,
        email=email,
        phone=phone,
        password_hash=pwd_context.hash(password),
        avatar=None
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default checking account for new user
    try:
        default_account = Account(
            user_id=new_user.id,
            account_type="checking",
            balance=Decimal("0.00"),
            currency="KZT",
            status="active"
        )
        db.add(default_account)
        db.commit()
        print(f"✅ Created default checking account for user {new_user.id}")
    except Exception as e:
        print(f"⚠️ Error creating default account for user {new_user.id}: {str(e)}")
        # Don't fail registration if account creation fails
        db.rollback()

    # Save avatar if provided
    if avatar_file:
        try:
            # Read file contents
            avatar_data = await avatar_file.read()
            
            # Save avatar file
            avatar_filename = save_avatar_file(avatar_data, new_user.id)
            
            # Update user with avatar filename
            new_user.avatar = avatar_filename
            db.commit()
            db.refresh(new_user)
        except Exception as e:
            # If avatar save fails, still return user but log error
            print(f"Error saving avatar for user {new_user.id}: {str(e)}")

    return UserRead.from_orm(new_user)


def login_user(email: str, password: str, db: Session = Depends(get_db)) -> UserRead:
    """
    Login user with email and password
    
    Args:
        email: User's email
        password: User's password
        db: Database session
        
    Returns:
        User data if credentials are valid
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.deleted_at:
        raise HTTPException(status_code=401, detail="User is deleted")
    
    return UserRead.from_orm(user)


def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    """
    Get user by ID
    
    Args:
        user_id: User's ID
        db: Database session
        
    Returns:
        User data
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.deleted_at:
        raise HTTPException(status_code=404, detail="User is deleted")

    return UserRead.from_orm(user)


async def update_user_avatar(
    user_id: int,
    avatar_file: UploadFile,
    db: Session = Depends(get_db)
) -> UserRead:
    """
    Update user's avatar
    
    Args:
        user_id: User's ID
        avatar_file: New avatar image file
        db: Database session
        
    Returns:
        Updated user data
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.deleted_at:
        raise HTTPException(status_code=404, detail="User is deleted")
    
    try:
        # Read file contents
        avatar_data = await avatar_file.read()
        
        # Delete old avatar if exists
        if user.avatar:
            old_avatar_path = AVATARS_DIR / user.avatar
            if old_avatar_path.exists():
                os.remove(old_avatar_path)
        
        # Save new avatar
        avatar_filename = save_avatar_file(avatar_data, user.id)
        
        # Update user
        user.avatar = avatar_filename
        db.commit()
        db.refresh(user)
        
        return UserRead.from_orm(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating avatar: {str(e)}")
