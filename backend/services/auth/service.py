from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
from models.user import User
from services.auth.schemas import UserCreate, UserRead

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    if db.query(User).filter(User.email == user.email).first() :
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.phone == user.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    new_user = User(
        name=user.name,
        surname=user.surname,
        email=user.email,
        phone=user.phone,
        password_hash=pwd_context.hash(user.password),
        avatar=user.avatar,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserRead.from_orm(new_user)


def login_user(email: str, password: str, db: Session = Depends(get_db)) -> UserRead:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.deleted_at:
        raise HTTPException(status_code=401, detail="User is deleted")
    return UserRead.from_orm(user)


def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.deleted_at:
        raise HTTPException(status_code=404, detail="User is deleted")

    return UserRead.from_orm(user)
