"""
Database models for Face Recognition System
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, LargeBinary, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
import os

# Add parent directory to path to import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base


class Person(Base):
    """Person entity with enrolled face data"""
    __tablename__ = "persons"
    
    id = Column(Integer, primary_key=True, index=True)
    id_person = Column(String, unique=True, index=True, nullable=False)  # External ID
    name = Column(String, nullable=False)
    photo_count = Column(Integer, default=0)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    person_metadata = Column(JSON, default={})  # Additional metadata
    is_active = Column(Boolean, default=True)
    
    # Relationships
    embeddings = relationship("FaceEmbedding", back_populates="person", cascade="all, delete-orphan")
    attempts = relationship("VerificationAttempt", back_populates="person", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Person(id_person='{self.id_person}', name='{self.name}')>"


class FaceEmbedding(Base):
    """Face embedding storage"""
    __tablename__ = "face_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    embedding = Column(LargeBinary, nullable=False)  # Stored as binary (numpy array)
    embedding_norm = Column(Float)  # L2 norm of the embedding
    photo_id = Column(String, unique=True, index=True)  # Reference to original photo
    created_at = Column(DateTime, default=datetime.utcnow)
    quality_metrics = Column(JSON, default={})  # Store quality scores
    
    # Relationships
    person = relationship("Person", back_populates="embeddings")
    
    def __repr__(self):
        return f"<FaceEmbedding(person_id={self.person_id}, photo_id='{self.photo_id}')>"


class VerificationAttempt(Base):
    """Log of verification attempts for audit trail"""
    __tablename__ = "verification_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    probe_id = Column(String, index=True)  # Anonymized probe identifier
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)  # Null if not found
    verdict = Column(String, nullable=False)  # match, possible_match, not_found, spoof, no_face_detected
    similarity = Column(Float, nullable=True)
    liveness_result = Column(String, nullable=True)  # live, spoof, unknown
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    attempt_metadata = Column(JSON, default={})  # Additional context
    
    # Relationships
    person = relationship("Person", back_populates="attempts")
    
    def __repr__(self):
        return f"<VerificationAttempt(verdict='{self.verdict}', similarity={self.similarity})>"

