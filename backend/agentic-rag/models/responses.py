"""
Pydantic response models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AgentResult(BaseModel):
    """
    Result from a single agent execution.
    
    Attributes:
        agent_name: Name of the agent (e.g., 'local_knowledge_agent')
        result: The agent's output/findings
        execution_time_ms: Time taken to execute (milliseconds)
    """
    
    agent_name: str = Field(
        ...,
        description="Name of the specialized agent",
        examples=["local_knowledge_agent", "web_search_agent"]
    )
    
    result: str = Field(
        ...,
        description="The agent's findings or output"
    )
    
    execution_time_ms: Optional[int] = Field(
        default=None,
        description="Execution time in milliseconds"
    )


class QueryResponse(BaseModel):
    """
    Response model for query results from the agentic RAG system.
    
    Attributes:
        query: The original user query
        final_answer: The synthesized final answer
        agents_used: List of agent names that were invoked
        agent_results: Detailed results from each agent
        session_id: Session identifier
        reasoning_plan: The supervisor's reasoning/planning steps
        total_time_ms: Total processing time
        timestamp: Response timestamp
    """
    
    query: str = Field(
        ...,
        description="The original user query"
    )
    
    final_answer: str = Field(
        ...,
        description="The final synthesized answer"
    )
    
    agents_used: List[str] = Field(
        default_factory=list,
        description="List of agents that were invoked"
    )
    
    agent_results: List[AgentResult] = Field(
        default_factory=list,
        description="Detailed results from each agent"
    )
    
    session_id: str = Field(
        ...,
        description="Session identifier for tracking"
    )
    
    reasoning_plan: Optional[str] = Field(
        default=None,
        description="The supervisor's reasoning and planning steps"
    )
    
    total_time_ms: int = Field(
        ...,
        description="Total processing time in milliseconds"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is our remote work policy?",
                "final_answer": "According to company policy, employees can work remotely up to 3 days per week with manager approval.",
                "agents_used": ["local_knowledge_agent"],
                "agent_results": [
                    {
                        "agent_name": "local_knowledge_agent",
                        "result": "Found policy document: Remote work allowed 3 days/week...",
                        "execution_time_ms": 1250
                    }
                ],
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "reasoning_plan": "Query requires internal company policy information. Delegating to local_knowledge_agent.",
                "total_time_ms": 2500,
                "timestamp": "2025-10-18T10:30:00"
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response model.
    """
    
    status: str = Field(
        ...,
        description="Health status",
        examples=["healthy", "degraded", "unhealthy"]
    )
    
    service: str = Field(
        ...,
        description="Service name"
    )
    
    version: str = Field(
        default="1.0.0",
        description="API version"
    )
    
    agents_available: List[str] = Field(
        default_factory=list,
        description="List of available agents"
    )
