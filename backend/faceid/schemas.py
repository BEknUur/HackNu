from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserMatchInfo(BaseModel):
    """Information about matched user"""
    user_id: int
    name: str
    surname: str
    email: str
    phone: str
    avatar: str
    created_at: Optional[str] = None 


class FaceVerificationResult(BaseModel):
    """Result of face verification"""
    success: bool
    verified: bool
    message: str
    user: Optional[UserMatchInfo] = None
    confidence: Optional[float] = None
    distance: Optional[float] = None
    threshold: Optional[float] = None
    model: Optional[str] = None
    error: Optional[str] = None


class VerificationResponse(BaseModel):
    """API response wrapper"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

