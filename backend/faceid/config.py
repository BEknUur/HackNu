"""
Configuration for Face Recognition and Liveness Detection System
"""
import os
from pathlib import Path

# Model paths
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

# InsightFace model configuration
DETECTION_MODEL = "buffalo_l"  # buffalo_l, buffalo_m, buffalo_s
EMBEDDING_SIZE = 512  # ArcFace embedding dimension

# Similarity thresholds для ArcFace (InsightFace)
# ArcFace дает очень точные эмбеддинги, поэтому пороги выше!
THRESHOLD_HIGH_CONFIDENCE = 0.40  # >= 0.40: высокая уверенность
THRESHOLD_MEDIUM_CONFIDENCE = 0.30  # 0.30-0.40: возможное совпадение
# < 0.30: не совпадает (это точно другой человек!)

# Liveness detection configuration
LIVENESS_MIN_FRAMES = 5  # Minimum frames for multi-frame liveness check
LIVENESS_MOTION_THRESHOLD = 0.02  # Motion threshold for detecting movement
LIVENESS_TEXTURE_THRESHOLD = 0.3  # Texture analysis threshold

# Face detection configuration
MIN_FACE_SIZE = 80  # Minimum face size in pixels
MAX_FACES_PER_IMAGE = 10  # Maximum faces to process per image
DETECTION_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for face detection

# Image quality thresholds
MIN_LIGHTING_SCORE = 0.3  # Minimum acceptable lighting score
MAX_BLUR_SCORE = 0.7  # Maximum acceptable motion blur score

# Enrollment configuration
MIN_ENROLLMENT_PHOTOS = 1  # Minimum photos required for enrollment
MAX_ENROLLMENT_PHOTOS = 5  # Maximum photos to store per person

# Security settings
LOG_ATTEMPTS = True  # Log all verification attempts
ENCRYPT_EMBEDDINGS = False  # Enable encryption for embeddings (implement key management)
ANONYMIZE_LOGS = True  # Anonymize probe IDs in logs

# Database settings
EMBEDDING_TABLE_NAME = "face_embeddings"
PERSON_TABLE_NAME = "persons"
ATTEMPT_LOG_TABLE_NAME = "verification_attempts"

# API settings
MAX_IMAGE_SIZE_MB = 10  # Maximum image size in MB
ALLOWED_IMAGE_FORMATS = ["image/jpeg", "image/png", "image/jpg"]

