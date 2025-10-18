"""
API Routes for Face Recognition System
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import cv2
import numpy as np
from io import BytesIO
import logging

from .schemas import (
    VerdictEnum, LivenessEnum, VerificationResponse, EnrollmentRequest,
    EnrollmentResponse, PersonInfo, DeletePersonResponse, HealthCheckResponse
)
from .face_service import face_service
from .models import Person, FaceEmbedding, VerificationAttempt
from .utils import generate_anonymized_id
from .config import MAX_IMAGE_SIZE_MB, ALLOWED_IMAGE_FORMATS, LOG_ATTEMPTS

# Import database dependency
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db

# Import test routes
from . import test_routes

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/faceid", tags=["Face Recognition"])


def decode_image(file_bytes: bytes) -> np.ndarray:
    """
    Decode uploaded image file to numpy array
    
    Args:
        file_bytes: Raw image bytes
        
    Returns:
        Image as numpy array in BGR format
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(file_bytes, np.uint8)
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
        
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")


async def validate_image_file(file: UploadFile) -> bytes:
    """
    Validate and read uploaded image file
    
    Args:
        file: Uploaded file
        
    Returns:
        File bytes
    """
    # Check file size
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    
    if file_size_mb > MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Image size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({MAX_IMAGE_SIZE_MB}MB)"
        )
    
    # Check content type
    if file.content_type not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image format. Allowed formats: {', '.join(ALLOWED_IMAGE_FORMATS)}"
        )
    
    return file_bytes


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    
    Returns system status and statistics
    """
    try:
        # Check model status
        model_loaded = face_service.model_loaded
        
        # Check database
        total_persons = db.query(Person).filter(Person.is_active == True).count()
        total_embeddings = db.query(FaceEmbedding).count()
        
        return HealthCheckResponse(
            status="healthy" if model_loaded else "degraded",
            model_loaded=model_loaded,
            database_connected=True,
            total_persons=total_persons,
            total_embeddings=total_embeddings
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_person(
    id_person: str = Form(...),
    name: str = Form(...),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Enroll a new person with face images
    
    Args:
        id_person: Unique identifier for the person
        name: Person's name
        images: List of face images (1-5 recommended)
        
    Returns:
        Enrollment result
    """
    try:
        # Validate and decode images
        decoded_images = []
        for image_file in images:
            file_bytes = await validate_image_file(image_file)
            image = decode_image(file_bytes)
            decoded_images.append(image)
        
        # Enroll person
        result = face_service.enroll_person(
            images=decoded_images,
            id_person=id_person,
            name=name,
            db_session=db
        )
        
        return EnrollmentResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Enrollment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")


@router.post("/verify", response_model=VerificationResponse)
async def verify_face(
    image: UploadFile = File(...),
    check_liveness: bool = Form(default=True),
    db: Session = Depends(get_db)
):
    """
    Verify a face against the database
    
    Args:
        image: Probe image containing a face
        check_liveness: Whether to perform liveness detection
        
    Returns:
        Verification result with match information
    """
    try:
        # Validate and decode image
        file_bytes = await validate_image_file(image)
        probe_image = decode_image(file_bytes)
        
        # Perform verification
        result = face_service.verify_face(
            image=probe_image,
            db_session=db,
            check_liveness=check_liveness
        )
        
        # Log attempt if enabled
        if LOG_ATTEMPTS:
            probe_id = generate_anonymized_id(file_bytes)
            
            attempt = VerificationAttempt(
                probe_id=probe_id,
                person_id=db.query(Person).filter(
                    Person.id_person == result['id_candidate']
                ).first().id if result['id_candidate'] else None,
                verdict=result['verdict'],
                similarity=result['similarity'],
                liveness_result=result['evidence']['liveness'],
                attempt_metadata={
                    'diagnostics': result['diagnostics'],
                    'liveness_details': result.get('liveness_details', {})
                }
            )
            db.add(attempt)
            db.commit()
        
        return VerificationResponse(**result)
    
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/verify-multi-frame", response_model=VerificationResponse)
async def verify_face_multi_frame(
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Verify a face using multiple frames for enhanced liveness detection
    
    Args:
        images: Multiple frames (minimum 3-5 recommended)
        
    Returns:
        Verification result with liveness check
    """
    try:
        # Validate and decode images
        decoded_images = []
        for image_file in images:
            file_bytes = await validate_image_file(image_file)
            image = decode_image(file_bytes)
            decoded_images.append(image)
        
        if len(decoded_images) < 3:
            raise HTTPException(
                status_code=400,
                detail="At least 3 frames are required for multi-frame verification"
            )
        
        # Use first frame as probe, all frames for liveness
        probe_image = decoded_images[0]
        
        # Perform verification with multi-frame liveness
        result = face_service.verify_face(
            image=probe_image,
            db_session=db,
            check_liveness=True,
            frames=decoded_images
        )
        
        # Log attempt
        if LOG_ATTEMPTS:
            probe_id = generate_anonymized_id(await images[0].read())
            
            attempt = VerificationAttempt(
                probe_id=probe_id,
                person_id=db.query(Person).filter(
                    Person.id_person == result['id_candidate']
                ).first().id if result['id_candidate'] else None,
                verdict=result['verdict'],
                similarity=result['similarity'],
                liveness_result=result['evidence']['liveness'],
                attempt_metadata={
                    'num_frames': len(decoded_images),
                    'diagnostics': result['diagnostics'],
                    'liveness_details': result.get('liveness_details', {})
                }
            )
            db.add(attempt)
            db.commit()
        
        return VerificationResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-frame verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/persons", response_model=List[PersonInfo])
async def list_persons(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all enrolled persons
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of persons
    """
    try:
        persons = db.query(Person).filter(
            Person.is_active == True
        ).offset(skip).limit(limit).all()
        
        return [
            PersonInfo(
                id_person=p.id_person,
                name=p.name,
                photo_count=p.photo_count,
                enrolled_at=p.enrolled_at,
                is_active=p.is_active
            )
            for p in persons
        ]
    except Exception as e:
        logger.error(f"Failed to list persons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/persons/{id_person}", response_model=PersonInfo)
async def get_person(id_person: str, db: Session = Depends(get_db)):
    """
    Get information about a specific person
    
    Args:
        id_person: Person identifier
        
    Returns:
        Person information
    """
    try:
        person = db.query(Person).filter(
            Person.id_person == id_person,
            Person.is_active == True
        ).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        return PersonInfo(
            id_person=person.id_person,
            name=person.name,
            photo_count=person.photo_count,
            enrolled_at=person.enrolled_at,
            is_active=person.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get person: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/persons/{id_person}", response_model=DeletePersonResponse)
async def delete_person(id_person: str, db: Session = Depends(get_db)):
    """
    Delete a person from the database (soft delete)
    
    Args:
        id_person: Person identifier
        
    Returns:
        Deletion result
    """
    try:
        person = db.query(Person).filter(
            Person.id_person == id_person
        ).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Soft delete
        person.is_active = False
        db.commit()
        
        return DeletePersonResponse(
            success=True,
            id_person=id_person,
            message=f"Person '{person.name}' has been deactivated"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete person: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get system statistics
    
    Returns:
        System statistics
    """
    try:
        total_persons = db.query(Person).filter(Person.is_active == True).count()
        total_embeddings = db.query(FaceEmbedding).count()
        total_attempts = db.query(VerificationAttempt).count()
        
        # Recent attempts statistics
        from sqlalchemy import func
        recent_attempts = db.query(
            VerificationAttempt.verdict,
            func.count(VerificationAttempt.id).label('count')
        ).group_by(VerificationAttempt.verdict).all()
        
        verdict_stats = {verdict: count for verdict, count in recent_attempts}
        
        return {
            'total_persons': total_persons,
            'total_embeddings': total_embeddings,
            'total_attempts': total_attempts,
            'verdict_distribution': verdict_stats,
            'model_status': 'loaded' if face_service.model_loaded else 'not_loaded'
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

