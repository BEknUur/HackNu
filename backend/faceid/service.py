import os
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
from deepface import DeepFace


class FaceVerificationService:
    def __init__(self, 
                 model_name: str = "VGG-Face",
                 detector_backend: str = "opencv",
                 distance_metric: str = "cosine"):
        """
        Initialize Face Verification Service
        
        Args:
            model_name: Model to use for face recognition (VGG-Face, Facenet, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace)
            detector_backend: Face detector backend (opencv, ssd, dlib, mtcnn, retinaface, mediapipe)
            distance_metric: Distance metric for similarity (cosine, euclidean, euclidean_l2)
        """
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric
        self.images_dir = Path(__file__).parent / "images"
        
    def get_all_registered_images(self) -> list[Path]:
        """Get all image files from the images directory"""
        if not self.images_dir.exists():
            return []
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        return [
            img for img in self.images_dir.iterdir()
            if img.is_file() and img.suffix.lower() in image_extensions
        ]
    
    def save_temp_image(self, image_data: bytes) -> str:
        """Save uploaded image to temporary file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_data)
            return temp_file.name
    
    def verify_face(self, uploaded_image_data: bytes) -> Dict[str, Any]:
        """
        Verify the uploaded face against all registered faces in images directory
        
        Args:
            uploaded_image_data: Bytes of the uploaded image
            
        Returns:
            Dictionary with verification results
        """
        temp_image_path = None
        
        try:
            # Get all registered images
            registered_images = self.get_all_registered_images()
            
            if not registered_images:
                return {
                    "success": False,
                    "message": "No registered faces found in the database",
                    "result": None
                }
            
            # Save uploaded image temporarily
            temp_image_path = self.save_temp_image(uploaded_image_data)
            
            best_match = None
            best_distance = float('inf')
            best_verified = False
            
            # Loop through all registered images
            for img_path in registered_images:
                try:
                    # Verify face against current registered image
                    result = DeepFace.verify(
                        img1_path=str(img_path),
                        img2_path=temp_image_path,
                        model_name=self.model_name,
                        detector_backend=self.detector_backend,
                        distance_metric=self.distance_metric,
                        enforce_detection=True
                    )
                    
                    # Check if this is the best match so far
                    if result['distance'] < best_distance:
                        best_distance = result['distance']
                        best_verified = result['verified']
                        best_match = {
                            "person": img_path.stem,  # filename without extension
                            "distance": result['distance'],
                            "verified": result['verified'],
                            "threshold": result['threshold'],
                            "model": result['model'],
                            "detector_backend": result['detector_backend'],
                            "similarity_metric": result['similarity_metric']
                        }
                        
                        # If we found a verified match, we can optionally break here
                        # or continue to find the absolute best match
                        if best_verified:
                            break
                            
                except Exception as e:
                    # Skip this image if face detection fails
                    print(f"Error verifying against {img_path.name}: {str(e)}")
                    continue
            
            if best_match:
                confidence = 1 - (best_distance / best_match['threshold']) if best_match['threshold'] > 0 else 0
                confidence = max(0, min(1, confidence))  # Clamp between 0 and 1
                
                return {
                    "success": True,
                    "message": "Verification completed successfully",
                    "result": {
                        "verified": best_match['verified'],
                        "confidence": round(confidence, 4),
                        "matched_person": best_match['person'] if best_match['verified'] else None,
                        "distance": round(best_match['distance'], 4),
                        "threshold": best_match['threshold'],
                        "model": best_match['model'],
                        "detector_backend": best_match['detector_backend'],
                        "similarity_metric": best_match['similarity_metric']
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "No face detected in the uploaded image or registered images",
                    "result": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": "Error during verification",
                "error": str(e),
                "result": None
            }
        finally:
            # Clean up temporary file
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.remove(temp_image_path)
                except:
                    pass
    
    def get_registered_faces_count(self) -> int:
        """Get count of registered faces"""
        return len(self.get_all_registered_images())
    
    def get_person_image_path(self, person_name: str) -> Optional[Path]:
        """
        Get the image path for a specific person
        
        Args:
            person_name: The name of the person (filename without extension)
            
        Returns:
            Path to the image file or None if not found
        """
        registered_images = self.get_all_registered_images()
        
        for img_path in registered_images:
            if img_path.stem == person_name:
                return img_path
        
        return None
