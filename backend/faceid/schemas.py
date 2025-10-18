"""
Pydantic schemas for Face Recognition API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VerdictEnum(str, Enum):
    """Possible verification verdicts"""
    MATCH = "match"
    POSSIBLE_MATCH = "possible_match"
    NOT_FOUND = "not_found"
    SPOOF = "spoof"
    NO_FACE_DETECTED = "no_face_detected"


class LivenessEnum(str, Enum):
    """Liveness detection results"""
    LIVE = "live"
    SPOOF = "spoof"
    UNKNOWN = "unknown"


class EnrollmentRequest(BaseModel):
    """Request to enroll a new person"""
    id_person: str = Field(..., description="Unique identifier for the person")
    name: str = Field(..., description="Name of the person")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")


class EnrollmentResponse(BaseModel):
    """Response after enrollment"""
    success: bool
    id_person: str
    name: str
    photo_count: int
    message: str
    enrolled_at: datetime


class VerificationRequest(BaseModel):
    """Request for face verification"""
    check_liveness: bool = Field(default=True, description="Perform liveness check")


class CandidateStats(BaseModel):
    """Statistics about the matched candidate"""
    id: str
    name: str
    best_similarity: float
    matched_reference_photo_id: str
    reference_photo_similarity: float


class Evidence(BaseModel):
    """Evidence supporting the verification decision"""
    probe_face_box: List[float] = Field(description="[x, y, w, h] bounding box")
    probe_embedding_norm: float
    candidate_stats: Optional[CandidateStats] = None
    liveness: LivenessEnum


class Diagnostics(BaseModel):
    """Diagnostic information about image quality"""
    detector_confidence: float
    lighting_score: float
    motion_blur_score: float


class VerificationResponse(BaseModel):
    """Response from face verification"""
    verdict: VerdictEnum
    id_candidate: Optional[str] = None
    name_candidate: Optional[str] = None
    similarity: Optional[float] = None
    threshold_used: Optional[float] = None
    explain: str = Field(description="Brief scientific explanation of the decision")
    evidence: Evidence
    diagnostics: Diagnostics
    timestamp: datetime


class PersonInfo(BaseModel):
    """Person information"""
    id_person: str
    name: str
    photo_count: int
    enrolled_at: datetime
    is_active: bool


class DeletePersonResponse(BaseModel):
    """Response after deleting a person"""
    success: bool
    id_person: str
    message: str


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    database_connected: bool
    total_persons: int
    total_embeddings: int

