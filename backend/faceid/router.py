from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from .service import FaceIDService
from .schemas import FaceVerificationResult


router = APIRouter()

# Initialize Face ID Service with optimal settings
face_service = FaceIDService(
    model_name="Facenet512",  # High accuracy model
    detector_backend="retinaface",  # Best detector for face detection
    distance_metric="cosine"  # Standard metric for face similarity
)


@router.post("/verify", response_model=FaceVerificationResult)
async def verify_face(
    file: UploadFile = File(..., description="Image file to verify (from camera or upload)"),
    db: Session = Depends(get_db)
):
    """
    Verify uploaded face against all registered users' avatars.
    
    This is the main endpoint for face ID verification. It compares the uploaded
    image against all registered user avatars and returns the matched user if found.
    
    Args:
        file: Uploaded image file containing a face
        db: Database session
        
    Returns:
        FaceVerificationResult with match information and user details
        
    Example response on success:
        {
            "success": true,
            "verified": true,
            "message": "Face verified successfully! Welcome, John Doe",
            "user": {
                "user_id": 1,
                "name": "John",
                "surname": "Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "avatar": "user_1_avatar.jpg",
                "created_at": "2025-01-01T00:00:00"
            },
            "confidence": 0.95,
            "distance": 0.15,
            "threshold": 0.40,
            "model": "Facenet512"
        }
        
    Example response on no match:
        {
            "success": true,
            "verified": false,
            "message": "No matching face found in registered users",
            "user": null
        }
    """
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload an image file."
            )
        
        # Read uploaded image
        contents = await file.read()
        
        if not contents:
            raise HTTPException(
                status_code=400, 
                detail="Empty file uploaded. Please upload a valid image."
            )
        
        # Verify face against all users
        result = face_service.verify_face_against_all_users(contents, db)
        
        # Return result
        return JSONResponse(
            content=result,
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "verified": False,
                "message": "Error processing image",
                "error": str(e),
                "user": None
            },
            status_code=500
        )
