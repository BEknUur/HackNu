"""
Pydantic schemas for the RAG system API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    query: str = Field(..., description="The user's question or query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    environment: str = Field("development", description="Environment to run in (development, production, testing)")
    max_iterations: Optional[int] = Field(None, description="Maximum number of agent iterations")


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    query: str = Field(..., description="The original query")
    response: str = Field(..., description="The RAG system's response")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Sources used in the response")
    confidence: float = Field(0.0, description="Confidence score of the response")
    status: str = Field("success", description="Status of the query processing")
    processing_time: Optional[float] = Field(None, description="Time taken to process the query")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the response")


class SystemStatus(BaseModel):
    """System status information."""
    status: str = Field(..., description="Overall system status")
    supervisor_agent: bool = Field(..., description="Whether supervisor agent is initialized")
    specialist_agents: List[str] = Field(default_factory=list, description="Available specialist agents")
    available_tools: List[str] = Field(default_factory=list, description="Available tools")
    available_agents: List[str] = Field(default_factory=list, description="Available agent types")
    environment: str = Field(..., description="Current environment")
    uptime: Optional[float] = Field(None, description="System uptime in seconds")


class ToolStatus(BaseModel):
    """Individual tool status."""
    name: str = Field(..., description="Tool name")
    status: str = Field(..., description="Tool status")
    available: bool = Field(..., description="Whether tool is available")
    error: Optional[str] = Field(None, description="Error message if tool is not available")


class ToolsStatus(BaseModel):
    """Status of all tools in the system."""
    vector_search: str = Field(..., description="Vector search tool status")
    web_search: str = Field(..., description="Web search tool status")
    overall_status: str = Field(..., description="Overall tools status")


class InitializeRequest(BaseModel):
    """Request to initialize the RAG system."""
    environment: str = Field("development", description="Environment to initialize for")
    force_reinitialize: bool = Field(False, description="Force reinitialization even if already initialized")


class InitializeResponse(BaseModel):
    """Response from system initialization."""
    status: str = Field(..., description="Initialization status")
    environment: str = Field(..., description="Environment initialized for")
    message: str = Field(..., description="Status message")
    initialized_agents: List[str] = Field(default_factory=list, description="List of initialized agents")
    initialized_tools: List[str] = Field(default_factory=list, description="List of initialized tools")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the error")
