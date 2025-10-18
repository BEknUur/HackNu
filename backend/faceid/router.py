from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from .service import FaceVerificationService
from .schemas import VerificationResult

router = APIRouter()

# Initialize face verification service
face_service = FaceVerificationService(
    model_name="VGG-Face",
    detector_backend="opencv",
    distance_metric="cosine"
)


@router.post("/verify", response_model=VerificationResult)
async def verify_face(file: UploadFile = File(...)):
    """
    Verify uploaded face against all registered faces in the database
    
    Args:
        file: Uploaded image file (from camera or file upload)
        
    Returns:
        VerificationResult with match information
    """
    try:
        # Read the uploaded file
        contents = await file.read()
        
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Verify the face
        result = face_service.verify_face(contents)
        
        return JSONResponse(content=result, status_code=200)
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Error processing image",
                "error": str(e),
                "result": None
            },
            status_code=500
        )


@router.get("/registered-count")
async def get_registered_count():
    """Get the count of registered faces in the database"""
    try:
        count = face_service.get_registered_faces_count()
        return {
            "success": True,
            "count": count,
            "message": f"Found {count} registered face(s)"
        }
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "message": "Error getting registered faces count"
            },
            status_code=500
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for face verification service"""
    return {
        "status": "healthy",
        "service": "Face Verification",
        "model": face_service.model_name,
        "detector": face_service.detector_backend,
        "metric": face_service.distance_metric
    }

