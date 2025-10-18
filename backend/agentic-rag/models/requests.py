"""
Pydantic request models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """
    Request model for submitting queries to the agentic RAG system.
    
    Attributes:
        query: The user's question or request
        session_id: Optional session ID for conversation continuity
        max_iterations: Maximum number of agent invocation cycles
        stream: Whether to stream the response (future feature)
    """
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's query to the RAG system",
        examples=["What is the company's remote work policy?"]
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for multi-turn conversations",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of agent invocation iterations"
    )
    
    stream: bool = Field(
        default=False,
        description="Enable streaming responses (future feature)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is our remote work policy and what are the latest AI trends?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "max_iterations": 3,
                "stream": False
            }
        }
