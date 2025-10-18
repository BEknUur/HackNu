from pydantic import BaseModel
from typing import Optional


class VerificationResponse(BaseModel):
    verified: bool
    confidence: float
    matched_person: Optional[str] = None
    distance: Optional[float] = None
    threshold: float
    model: str
    detector_backend: str
    similarity_metric: str


class VerificationResult(BaseModel):
    success: bool
    message: str
    result: Optional[VerificationResponse] = None
    error: Optional[str] = None

