"""
Financial Analysis Router

Single endpoint for comprehensive financial analysis using ML models.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from ml_models import FinancialAgent
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["Financial Analysis"])


class FinancialAnalysisResponse(BaseModel):
    """Response model for financial analysis."""
    
    user_id: int
    analysis_period_months: int
    financial_data: Dict[str, Any]
    ai_insights: str
    specific_query: Optional[str]
    status: str


@router.post("/analyze", response_model=FinancialAnalysisResponse)
async def analyze_user_finances(
    user_id: int = Query(..., description="User ID to analyze"),
    months_back: int = Query(6, ge=1, le=24, description="Number of months to analyze (1-24)"),
    specific_query: Optional[str] = Query(None, description="Specific question or focus area"),
    db: Session = Depends(get_db)
):
    """
    Comprehensive financial analysis endpoint.
    
    Analyzes user's financial data including:
    - Account balances and activity
    - Transaction patterns and spending behavior
    - Income stability and savings rate
    - Financial goals progress
    - Financial health score
    - AI-powered insights and recommendations
    
    Args:
        user_id: ID of the user to analyze
        months_back: Number of months to include in analysis (1-24)
        specific_query: Optional specific question or area to focus on
        db: Database session
        
    Returns:
        Complete financial analysis with AI insights
        
    Raises:
        HTTPException: If user not found or analysis fails
    """
    logger.info(f"Starting financial analysis for user {user_id}")
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    try:
        # Initialize financial agent
        agent = FinancialAgent()
        
        # Perform comprehensive analysis
        analysis_result = agent.analyze_user_finances(
            db=db,
            user_id=user_id,
            specific_query=specific_query,
            months_back=months_back
        )
        
        logger.info(f"Successfully completed analysis for user {user_id}")
        return analysis_result
        
    except ValueError as e:
        logger.error(f"Validation error for user {user_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error analyzing finances for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete financial analysis: {str(e)}"
        )

