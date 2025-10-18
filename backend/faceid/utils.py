"""
Utility functions for face recognition
"""
import numpy as np
import cv2
from typing import Tuple, Optional
import hashlib
from datetime import datetime


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    """
    Normalize embedding using L2 normalization
    
    Args:
        embedding: Raw embedding vector
        
    Returns:
        Normalized embedding vector
    """
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return embedding
    return embedding / norm


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding (normalized)
        embedding2: Second embedding (normalized)
        
    Returns:
        Cosine similarity score [0, 1]
    """
    # Ensure embeddings are normalized
    embedding1 = normalize_embedding(embedding1)
    embedding2 = normalize_embedding(embedding2)
    
    # Calculate cosine similarity
    similarity = np.dot(embedding1, embedding2)
    
    # Clip to [0, 1] range (in case of numerical errors)
    return float(np.clip(similarity, 0.0, 1.0))


def euclidean_distance(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate Euclidean distance between two embeddings
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        
    Returns:
        Euclidean distance
    """
    return float(np.linalg.norm(embedding1 - embedding2))


def assess_lighting_quality(image: np.ndarray) -> float:
    """
    Assess lighting quality of an image
    
    Args:
        image: Input image in BGR format
        
    Returns:
        Lighting quality score [0, 1] where 1 is optimal
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Calculate mean brightness
    mean_brightness = np.mean(gray) / 255.0
    
    # Calculate standard deviation (dynamic range)
    std_brightness = np.std(gray) / 255.0
    
    # Optimal brightness is around 0.4-0.6
    # Good dynamic range is > 0.15
    brightness_score = 1.0 - abs(mean_brightness - 0.5) * 2
    dynamic_range_score = min(std_brightness / 0.15, 1.0)
    
    # Combined score
    return float((brightness_score + dynamic_range_score) / 2)


def assess_motion_blur(image: np.ndarray) -> float:
    """
    Assess motion blur in an image using Laplacian variance
    
    Args:
        image: Input image in BGR format
        
    Returns:
        Blur score [0, 1] where 0 is sharp, 1 is very blurred
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Calculate Laplacian variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Normalize (empirically, sharp images have variance > 100)
    # Blurry images have variance < 50
    blur_score = 1.0 - min(laplacian_var / 100.0, 1.0)
    
    return float(blur_score)


def generate_anonymized_id(image_data: bytes) -> str:
    """
    Generate anonymized ID for logging purposes
    
    Args:
        image_data: Raw image data
        
    Returns:
        Anonymized hash ID
    """
    # Create hash with timestamp for uniqueness
    timestamp = datetime.utcnow().isoformat().encode()
    hash_data = image_data[:1000] + timestamp  # Use first 1KB + timestamp
    hash_id = hashlib.sha256(hash_data).hexdigest()[:16]
    return f"probe_{hash_id}"


def embedding_to_binary(embedding: np.ndarray) -> bytes:
    """
    Convert numpy embedding to binary format for storage
    
    Args:
        embedding: Numpy array
        
    Returns:
        Binary representation
    """
    return embedding.tobytes()


def binary_to_embedding(binary_data: bytes, dtype=np.float32) -> np.ndarray:
    """
    Convert binary data back to numpy embedding
    
    Args:
        binary_data: Binary representation
        dtype: Data type of the embedding
        
    Returns:
        Numpy array
    """
    return np.frombuffer(binary_data, dtype=dtype)


def expand_face_box(box: Tuple[float, float, float, float], 
                    image_shape: Tuple[int, int],
                    expand_ratio: float = 0.1) -> Tuple[int, int, int, int]:
    """
    Expand face bounding box by a certain ratio
    
    Args:
        box: (x, y, w, h) bounding box
        image_shape: (height, width) of the image
        expand_ratio: Ratio to expand the box
        
    Returns:
        Expanded (x, y, w, h) box
    """
    x, y, w, h = box
    img_h, img_w = image_shape[:2]
    
    # Calculate expansion
    expand_w = w * expand_ratio
    expand_h = h * expand_ratio
    
    # Expand box
    new_x = max(0, int(x - expand_w / 2))
    new_y = max(0, int(y - expand_h / 2))
    new_w = min(img_w - new_x, int(w + expand_w))
    new_h = min(img_h - new_y, int(h + expand_h))
    
    return (new_x, new_y, new_w, new_h)


def draw_face_box(image: np.ndarray, 
                  box: Tuple[float, float, float, float],
                  label: str = "",
                  color: Tuple[int, int, int] = (0, 255, 0),
                  thickness: int = 2) -> np.ndarray:
    """
    Draw bounding box on image
    
    Args:
        image: Input image
        box: (x, y, w, h) bounding box
        label: Text label to display
        color: Box color in BGR
        thickness: Line thickness
        
    Returns:
        Image with drawn box
    """
    img_copy = image.copy()
    x, y, w, h = [int(v) for v in box]
    
    # Draw rectangle
    cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, thickness)
    
    # Draw label if provided
    if label:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2
        
        # Get text size
        (text_w, text_h), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        
        # Draw background rectangle for text
        cv2.rectangle(img_copy, (x, y - text_h - 10), (x + text_w, y), color, -1)
        
        # Draw text
        cv2.putText(img_copy, label, (x, y - 5), font, font_scale, (255, 255, 255), font_thickness)
    
    return img_copy

