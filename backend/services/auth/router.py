from fastapi import APIRouter
from services.auth.service import create_user, login_user, get_user
from services.auth.schemas import UserCreate, UserLogin, UserRead

router = APIRouter()

router.post("/register", response_model=UserRead, tags=["auth"])(create_user)
router.post("/login", response_model=UserRead, tags=["auth"])(login_user)
router.get("/{user_id}", response_model=UserRead, tags=["auth"])(get_user)

