"""
Financial Agent

Main agent that orchestrates financial analysis and AI-powered insights
using Gemini and financial data analyzer.
"""

import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .financial_analyzer import FinancialAnalyzer
from .gemini_wrapper import FINANCIAL_ADVISOR_SYSTEM_PROMPT, GeminiWrapper

logger = logging.getLogger(__name__)


class FinancialAgent:
    """
    Main financial agent that combines data analysis with AI insights.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7
    ):
        """
        Initialize financial agent.
        
        Args:
            api_key: Google API key for Gemini
            model_name: Gemini model to use
            temperature: Sampling temperature
        """
        self.gemini = GeminiWrapper(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        # Set financial advisor system prompt
        self.gemini.set_system_prompt(FINANCIAL_ADVISOR_SYSTEM_PROMPT)
        
        logger.info("Financial agent initialized")
    
    def analyze_user_finances(
        self,
        db: Session,
        user_id: int,
        specific_query: Optional[str] = None,
        months_back: int = 6
    ) -> Dict[str, Any]:
        """
        Perform comprehensive financial analysis for a user.
        
        Args:
            db: Database session
            user_id: User ID to analyze
            specific_query: Optional specific question/focus area
            months_back: Number of months to analyze
        
        Returns:
            Complete analysis with AI insights and recommendations
        """
        logger.info(f"Starting financial analysis for user {user_id}")
        
        try:
            # Step 1: Gather and analyze financial data
            analyzer = FinancialAnalyzer(db, user_id)
            financial_data = analyzer.get_comprehensive_analysis(months_back)
            
            # Step 2: Format data for AI context
            context = self._format_context_for_ai(financial_data)
            
            # Step 3: Generate AI insights
            prompt = self._build_analysis_prompt(specific_query)
            ai_response = self.gemini.generate_with_retry(prompt, context)
            
            # Step 4: Combine everything into final response
            result = {
                "user_id": user_id,
                "analysis_period_months": months_back,
                "financial_data": financial_data,
                "ai_insights": ai_response,
                "specific_query": specific_query,
                "status": "success"
            }
            
            logger.info(f"Successfully completed analysis for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing finances for user {user_id}: {e}")
            raise
    
    
    def _format_context_for_ai(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format financial data into context for AI.
        
        Args:
            financial_data: Raw financial analysis data
        
        Returns:
            Formatted context dictionary
        """
        transactions_analysis = financial_data['transactions_analysis']
        
        context = {
            "user_profile": json.dumps(financial_data['user_info'], indent=2),
            "accounts": json.dumps(financial_data['accounts_summary'], indent=2),
            "transactions": json.dumps({
                "total_count": transactions_analysis['total_transactions'],
                "by_type": transactions_analysis['by_type'],
                "recent": transactions_analysis['recent_transactions'][:10]
            }, indent=2),
            "spending_analysis": json.dumps(financial_data['spending_breakdown'], indent=2),
            "income_analysis": json.dumps(financial_data['income_analysis'], indent=2),
            "financial_goals": json.dumps(financial_data['financial_goals'], indent=2),
            "financial_health": json.dumps(financial_data['financial_health'], indent=2),
            "recommendations_flags": json.dumps(financial_data['recommendations_data'], indent=2)
        }
        
        return context
    
    def _build_analysis_prompt(self, specific_query: Optional[str] = None) -> str:
        """
        Build the prompt for comprehensive analysis.
        
        Args:
            specific_query: Optional specific area to focus on or question to answer
        
        Returns:
            Formatted prompt
        """
        if specific_query:
            if any(keyword in specific_query.lower() for keyword in ['budget', 'бюджет']):
                return f"""Based on the user's financial data, create a detailed monthly budget plan.

Include:
1. Recommended budget allocation by category (in percentages and amounts)
2. Savings target for the month
3. Discretionary spending limit
4. Emergency fund recommendations
5. Budget adjustment suggestions

Special focus on: {specific_query}

Format the budget as a clear, actionable plan with specific amounts."""
            
            return f"""Please provide a comprehensive financial analysis with special attention to: {specific_query}

Include:
1. Overall Financial Overview
2. Key Insights and Findings
3. Detailed Analysis (focusing on: {specific_query})
4. Specific Recommendations
5. Action Steps

Base your analysis entirely on the provided financial data. Be specific with numbers and percentages."""
        
        return """Please provide a comprehensive financial analysis for this user.

Include:
1. Financial Overview - Brief summary of current financial situation
2. Key Insights - 5 most important findings from the data
3. Spending Analysis - Patterns, trends, and areas of concern
4. Income & Savings Analysis - Income stability and savings behavior
5. Financial Goals Review - Progress and feasibility of goals
6. Financial Health Assessment - Overall financial wellness
7. Prioritized Recommendations - Top 5 actionable steps
8. Next Steps - Immediate actions to take

Base your analysis entirely on the provided financial data. Be specific with numbers and percentages."""

