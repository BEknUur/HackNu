import os
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
from deepface import DeepFace
from sqlalchemy.orm import Session
from models.user import User


class FaceIDService:
    """
    Face ID Service using DeepFace for user verification.
    Compares uploaded photos against registered user avatars.
    """
    
    def __init__(self, 
                 model_name: str = "Facenet512",
                 detector_backend: str = "retinaface",
                 distance_metric: str = "cosine",
                 avatars_base_dir: str = "uploads/avatars"):
        """
        Initialize Face ID Service
        
        Args:
            model_name: Model to use for face recognition
                       Options: VGG-Face, Facenet, Facenet512, OpenFace, DeepFace, 
                               DeepID, ArcFace, Dlib, SFace, GhostFaceNet
            detector_backend: Face detector backend
                            Options: opencv, ssd, dlib, mtcnn, retinaface, 
                                    mediapipe, yolov8, yunet, fastmtcnn
            distance_metric: Distance metric for similarity
                           Options: cosine, euclidean, euclidean_l2
            avatars_base_dir: Base directory where user avatars are stored
        """
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric
        self.avatars_base_dir = Path(avatars_base_dir)
        
        # Create avatars directory if it doesn't exist
        self.avatars_base_dir.mkdir(parents=True, exist_ok=True)
    
    def _save_temp_image(self, image_data: bytes) -> str:
        """
        Save uploaded image to temporary file
        
        Args:
            image_data: Bytes of the uploaded image
            
        Returns:
            Path to temporary file
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_data)
            return temp_file.name
    
    def _get_avatar_path(self, avatar_filename: str) -> Optional[Path]:
        """
        Get full path to avatar file
        
        Args:
            avatar_filename: Filename of the avatar
            
        Returns:
            Path to avatar file or None if not found
        """
        if not avatar_filename:
            return None
            
        avatar_path = self.avatars_base_dir / avatar_filename
        
        if avatar_path.exists() and avatar_path.is_file():
            return avatar_path
        
        return None
    
    def verify_face_against_user(self, 
                                 uploaded_image_data: bytes, 
                                 user: User) -> Dict[str, Any]:
        """
        Verify uploaded face against a specific user's avatar
        
        Args:
            uploaded_image_data: Bytes of the uploaded image
            user: User object from database
            
        Returns:
            Dictionary with verification results
        """
        temp_image_path = None
        
        try:
            # Check if user has avatar
            if not user.avatar:
                return {
                    "verified": False,
                    "message": f"User {user.email} has no registered avatar",
                    "error": "NO_AVATAR"
                }
            
            # Get avatar path
            avatar_path = self._get_avatar_path(user.avatar)
            if not avatar_path:
                return {
                    "verified": False,
                    "message": f"Avatar file not found for user {user.email}",
                    "error": "AVATAR_NOT_FOUND"
                }
            
            # Save uploaded image temporarily
            temp_image_path = self._save_temp_image(uploaded_image_data)
            
            # Verify face using DeepFace
            result = DeepFace.verify(
                img1_path=str(avatar_path),
                img2_path=temp_image_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                distance_metric=self.distance_metric,
                enforce_detection=True
            )
            
            # Calculate confidence score
            threshold = result.get('threshold', 1.0)
            distance = result.get('distance', 0)
            confidence = max(0, min(1, 1 - (distance / threshold))) if threshold > 0 else 0
            
            return {
                "verified": result['verified'],
                "distance": round(distance, 4),
                "threshold": threshold,
                "confidence": round(confidence, 4),
                "model": result['model'],
                "detector_backend": result['detector_backend'],
                "similarity_metric": result['similarity_metric'],
                "user_id": user.id
            }
            
        except Exception as e:
            return {
                "verified": False,
                "message": f"Error verifying face: {str(e)}",
                "error": str(e)
            }
        finally:
            # Clean up temporary file
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.remove(temp_image_path)
                except:
                    pass
    
    def verify_face_against_all_users(self, 
                                      uploaded_image_data: bytes, 
                                      db: Session) -> Dict[str, Any]:
        """
        Verify uploaded face against all registered users' avatars
        
        Args:
            uploaded_image_data: Bytes of the uploaded image
            db: Database session
            
        Returns:
            Dictionary with verification results including matched user info
        """
        try:
            # Get all users with avatars
            users = db.query(User).filter(
                User.avatar.isnot(None),
                User.deleted_at.is_(None)
            ).all()
            
            if not users:
                return {
                    "success": False,
                    "verified": False,
                    "message": "No registered users with avatars found in database",
                    "user": None
                }
            
            best_match = None
            best_confidence = 0
            best_user = None
            
            # Compare against each user's avatar
            for user in users:
                result = self.verify_face_against_user(uploaded_image_data, user)
                
                # Skip if error occurred
                if "error" in result:
                    continue
                
                # Check if this is a better match
                if result.get("verified", False):
                    confidence = result.get("confidence", 0)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = result
                        best_user = user
            
            # Return result
            if best_match and best_user:
                return {
                    "success": True,
                    "verified": True,
                    "message": f"Face verified successfully! Welcome, {best_user.name} {best_user.surname}",
                    "user": {
                        "user_id": best_user.id,
                        "name": best_user.name,
                        "surname": best_user.surname,
                        "email": best_user.email,
                        "phone": best_user.phone,
                        "avatar": best_user.avatar,
                        "created_at": best_user.created_at
                    },
                    "confidence": best_match.get("confidence"),
                    "distance": best_match.get("distance"),
                    "threshold": best_match.get("threshold"),
                    "model": best_match.get("model")
                }
            else:
                return {
                    "success": True,
                    "verified": False,
                    "message": "No matching face found in registered users",
                    "user": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "verified": False,
                "message": "Error during face verification",
                "error": str(e),
                "user": None
            }
    
    def save_avatar(self, image_data: bytes, user_id: int) -> str:
        """
        Save user avatar to disk
        
        Args:
            image_data: Bytes of the avatar image
            user_id: ID of the user
            
        Returns:
            Filename of saved avatar
        """
        filename = f"user_{user_id}_avatar.jpg"
        filepath = self.avatars_base_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return filename

