from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from services.auth.service import create_user, login_user, get_user, update_user_avatar
from services.auth.schemas import UserLogin, UserRead
from typing import Optional

router = APIRouter()


@router.post("/register", response_model=UserRead, tags=["auth"])
async def register(
    name: str = Form(..., description="User's first name"),
    surname: str = Form(..., description="User's last name"),
    email: str = Form(..., description="User's email address"),
    phone: str = Form(..., description="User's phone number"),
    password: str = Form(..., description="User's password"),
    avatar: Optional[UploadFile] = File(None, description="User's avatar image (optional)"),
    db: Session = Depends(get_db)
):
    """
    Register a new user with optional avatar image for Face ID.
    
    If an avatar is provided, it will be saved and used for face verification.
    """
    return await create_user(
        name=name,
        surname=surname,
        email=email,
        phone=phone,
        password=password,
        avatar_file=avatar,
        db=db
    )


@router.post("/login", response_model=UserRead, tags=["auth"])
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns user information if credentials are valid.
    """
    return login_user(
        email=credentials.email,
        password=credentials.password,
        db=db
    )


@router.put("/{user_id}/avatar", response_model=UserRead, tags=["auth"])
async def update_avatar(
    user_id: int,
    avatar: UploadFile = File(..., description="New avatar image"),
    db: Session = Depends(get_db)
):
    """
    Update user's avatar image for Face ID.
    
    This will replace the existing avatar with a new one.
    """
    return await update_user_avatar(
        user_id=user_id,
        avatar_file=avatar,
        db=db
    )
