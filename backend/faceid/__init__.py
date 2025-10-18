"""
Face Recognition and Liveness Detection Module

This module provides face recognition capabilities with liveness detection
for secure biometric authentication.

Features:
- Face detection and embedding extraction using InsightFace
- Liveness detection to prevent spoofing attacks
- Database storage of face embeddings
- RESTful API for enrollment and verification

Usage:
    from faceid_auth import main_router
    app.include_router(main_router)
"""

from .routes import router
from .test_routes import router as test_router
from .face_service import face_service
from .models import Person, FaceEmbedding, VerificationAttempt
from .schemas import (
    VerdictEnum, LivenessEnum, VerificationResponse, EnrollmentResponse
)

# Combine routers
from fastapi import APIRouter
main_router = APIRouter()
main_router.include_router(router)
main_router.include_router(test_router)

__version__ = "1.0.0"
__all__ = [
    "main_router",
    "router",
    "test_router", 
    "face_service",
    "Person",
    "FaceEmbedding",
    "VerificationAttempt",
    "VerdictEnum",
    "LivenessEnum",
    "VerificationResponse",
    "EnrollmentResponse"
]