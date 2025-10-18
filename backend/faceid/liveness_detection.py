"""
Liveness Detection Module

Implements basic liveness detection to prevent spoofing attacks.
Methods include:
1. Multi-frame motion analysis
2. Texture analysis (detect printed photos vs real faces)
3. Eye blink detection (optional, requires additional models)
"""
import numpy as np
import cv2
from typing import List, Tuple, Optional
from .config import LIVENESS_MIN_FRAMES, LIVENESS_MOTION_THRESHOLD, LIVENESS_TEXTURE_THRESHOLD
from .schemas import LivenessEnum


class LivenessDetector:
    """
    Liveness detection using multiple techniques
    """
    
    def __init__(self):
        self.min_frames = LIVENESS_MIN_FRAMES
        self.motion_threshold = LIVENESS_MOTION_THRESHOLD
        self.texture_threshold = LIVENESS_TEXTURE_THRESHOLD
    
    def check_liveness(self, frames: List[np.ndarray]) -> Tuple[LivenessEnum, dict]:
        """
        Perform liveness check on frames
        
        Args:
            frames: List of image frames (BGR format)
            
        Returns:
            Tuple of (verdict, details)
        """
        if len(frames) == 1:
            # Single frame - use texture analysis only
            return self._check_single_frame(frames[0])
        else:
            # Multi-frame - use motion analysis
            return self._check_multi_frame(frames)
    
    def _check_single_frame(self, frame: np.ndarray) -> Tuple[LivenessEnum, dict]:
        """
        Liveness check for single frame using texture analysis
        
        Args:
            frame: Single image frame
            
        Returns:
            Tuple of (verdict, details)
        """
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Texture analysis using Local Binary Pattern (LBP) variance
        texture_score = self._analyze_texture(gray)
        
        # Frequency analysis
        frequency_score = self._analyze_frequency(gray)
        
        # Combined score
        combined_score = (texture_score + frequency_score) / 2
        
        details = {
            "texture_score": float(texture_score),
            "frequency_score": float(frequency_score),
            "combined_score": float(combined_score),
            "method": "single_frame_texture"
        }
        
        if combined_score > self.texture_threshold:
            return LivenessEnum.LIVE, details
        elif combined_score < self.texture_threshold * 0.6:
            return LivenessEnum.SPOOF, details
        else:
            return LivenessEnum.UNKNOWN, details
    
    def _check_multi_frame(self, frames: List[np.ndarray]) -> Tuple[LivenessEnum, dict]:
        """
        Liveness check for multiple frames using motion analysis
        
        Args:
            frames: List of image frames
            
        Returns:
            Tuple of (verdict, details)
        """
        if len(frames) < self.min_frames:
            # Not enough frames, fall back to single frame check
            return self._check_single_frame(frames[0])
        
        # Convert frames to grayscale
        gray_frames = []
        for frame in frames:
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            gray_frames.append(gray)
        
        # Calculate motion between frames
        motion_score = self._calculate_motion_score(gray_frames)
        
        # Check texture on first frame
        texture_score = self._analyze_texture(gray_frames[0])
        
        # Calculate variance across frames (live faces have more variance)
        variance_score = self._calculate_temporal_variance(gray_frames)
        
        # Combined decision
        combined_score = (motion_score * 0.5 + texture_score * 0.3 + variance_score * 0.2)
        
        details = {
            "motion_score": float(motion_score),
            "texture_score": float(texture_score),
            "variance_score": float(variance_score),
            "combined_score": float(combined_score),
            "num_frames": len(frames),
            "method": "multi_frame_motion"
        }
        
        # Decision thresholds
        if combined_score > 0.5:
            return LivenessEnum.LIVE, details
        elif combined_score < 0.3:
            return LivenessEnum.SPOOF, details
        else:
            return LivenessEnum.UNKNOWN, details
    
    def _analyze_texture(self, gray_image: np.ndarray) -> float:
        """
        Analyze texture using LBP (Local Binary Pattern) variance
        
        Real faces have richer texture than printed photos
        """
        # Calculate LBP
        lbp = self._compute_lbp(gray_image)
        
        # Calculate variance of LBP
        lbp_variance = np.var(lbp)
        
        # Normalize (empirically determined values)
        # Real faces: variance > 500
        # Printed photos: variance < 300
        normalized_score = min(lbp_variance / 500.0, 1.0)
        
        return normalized_score
    
    def _compute_lbp(self, gray_image: np.ndarray, radius: int = 1, points: int = 8) -> np.ndarray:
        """
        Compute Local Binary Pattern
        
        Simple implementation for basic texture analysis
        """
        rows, cols = gray_image.shape
        lbp = np.zeros((rows - 2 * radius, cols - 2 * radius), dtype=np.uint8)
        
        for i in range(radius, rows - radius):
            for j in range(radius, cols - radius):
                center = gray_image[i, j]
                code = 0
                
                # Compare with 8 neighbors
                if gray_image[i-1, j-1] >= center: code |= 1 << 0
                if gray_image[i-1, j] >= center: code |= 1 << 1
                if gray_image[i-1, j+1] >= center: code |= 1 << 2
                if gray_image[i, j+1] >= center: code |= 1 << 3
                if gray_image[i+1, j+1] >= center: code |= 1 << 4
                if gray_image[i+1, j] >= center: code |= 1 << 5
                if gray_image[i+1, j-1] >= center: code |= 1 << 6
                if gray_image[i, j-1] >= center: code |= 1 << 7
                
                lbp[i - radius, j - radius] = code
        
        return lbp
    
    def _analyze_frequency(self, gray_image: np.ndarray) -> float:
        """
        Analyze frequency domain characteristics
        
        Printed photos have different frequency characteristics than real faces
        """
        # Apply FFT
        f_transform = np.fft.fft2(gray_image)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)
        
        # Analyze high frequency content
        rows, cols = gray_image.shape
        crow, ccol = rows // 2, cols // 2
        
        # Extract high frequency region (outer 30%)
        mask = np.ones((rows, cols), dtype=np.uint8)
        r = int(min(rows, cols) * 0.35)
        cv2.circle(mask, (ccol, crow), r, 0, -1)
        
        high_freq_energy = np.sum(magnitude_spectrum * mask)
        total_energy = np.sum(magnitude_spectrum)
        
        # Real faces have more high frequency content
        freq_ratio = high_freq_energy / (total_energy + 1e-6)
        
        # Normalize
        normalized_score = min(freq_ratio * 10, 1.0)
        
        return normalized_score
    
    def _calculate_motion_score(self, gray_frames: List[np.ndarray]) -> float:
        """
        Calculate motion score across frames
        
        Real faces show natural micro-movements
        """
        if len(gray_frames) < 2:
            return 0.0
        
        total_motion = 0.0
        
        for i in range(1, len(gray_frames)):
            # Calculate optical flow or simple frame difference
            diff = cv2.absdiff(gray_frames[i], gray_frames[i-1])
            motion = np.mean(diff) / 255.0
            total_motion += motion
        
        avg_motion = total_motion / (len(gray_frames) - 1)
        
        # Normalize
        # Too little motion (< 0.01): likely static photo
        # Moderate motion (0.01-0.1): likely live face
        # Too much motion (> 0.1): likely video replay or shaking
        
        if avg_motion < 0.01:
            score = avg_motion / 0.01  # Scale to [0, 1]
        elif avg_motion < 0.1:
            score = 1.0
        else:
            score = max(0.5, 1.0 - (avg_motion - 0.1) / 0.2)
        
        return float(score)
    
    def _calculate_temporal_variance(self, gray_frames: List[np.ndarray]) -> float:
        """
        Calculate temporal variance across frames
        
        Real faces have natural variations in pixel intensity
        """
        if len(gray_frames) < 2:
            return 0.0
        
        # Stack frames and calculate variance across time dimension
        frames_array = np.array(gray_frames, dtype=np.float32)
        temporal_variance = np.var(frames_array, axis=0)
        
        avg_variance = np.mean(temporal_variance)
        
        # Normalize (empirically determined)
        # Live faces: variance > 10
        # Static photos: variance < 5
        normalized_score = min(avg_variance / 10.0, 1.0)
        
        return normalized_score


# Global instance
liveness_detector = LivenessDetector()

