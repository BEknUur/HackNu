"""
Financial Goals Tools for RAG Agent

This module provides LangChain tools for managing financial goals and planning.
Users can create savings goals, track progress, get AI analysis, and view
their overall financial summary.

Tools:
- get_my_financial_goals: View all financial goals
- create_financial_goal: Create a new savings goal with AI analysis
- get_goal_analysis: Get AI predictions for goal achievability
- get_financial_summary: View complete financial overview
"""

from langchain_core.tools import tool
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from services.financial_goals.service import FinancialGoalService
from services.financial_goals.schemas import GoalCreate


# Global context for user_id and db session
_goal_context: Dict[str, Any] = {}


def set_goal_context(user_id: int, db):
    """
    Set the context for financial goal tools.
    
    Args:
        user_id: The ID of the user making the request
        db: SQLAlchemy database session
    """
    global _goal_context
    _goal_context = {"user_id": user_id, "db": db}


@tool
def get_my_financial_goals(status_filter: Optional[str] = None) -> str:
    """
    View all your financial goals and savings plans.
    
    This tool shows your active financial goals, including target amounts,
    current savings, deadlines, and progress. You can filter by status to
    see only active goals or include completed/failed goals.
    
    Args:
        status_filter: Optional filter ('active', 'achieved', 'failed', 'cancelled')
        
    Returns:
        A formatted list of financial goals with progress indicators and
        AI predictions.
        
    Examples:
        User: "Show my financial goals"
        User: "What am I saving for?"
        User: "What are my active savings goals?"
        User: "Show all my goals"
        User: "What financial plans do I have?"
    """
    try:
        user_id = _goal_context.get("user_id")
        db = _goal_context.get("db")
        
        if not user_id or not db:
            return "Error: Goal context not set. Please try again."
        
        # Get goals
        goals = FinancialGoalService.get_user_goals(
            db, user_id, status=status_filter, skip=0, limit=100
        )
        
        if not goals:
            if status_filter:
                return f"You don't have any {status_filter} financial goals yet."
            return "You don't have any financial goals yet. Would you like to create one?"
        
        # Format goals list
        response = f"🎯 Your Financial Goals ({len(goals)} total"
        if status_filter:
            response += f", {status_filter} only"
        response += "):\n\n"
        
        for goal in goals:
            # Status emoji
            status_emoji = {
                'active': '⏳',
                'achieved': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(goal.status, '📊')
            
            # Calculate progress
            progress = (float(goal.current_savings) / float(goal.target_amount) * 100) if goal.target_amount > 0 else 0
            
            response += f"{status_emoji} Goal #{goal.id}: {goal.title}\n"
            response += f"   Target: {goal.target_amount} {goal.currency}\n"
            response += f"   Current Savings: {goal.current_savings} {goal.currency}\n"
            response += f"   Progress: {progress:.1f}%\n"
            
            # Progress bar
            progress_blocks = int(progress / 10)
            progress_bar = "█" * progress_blocks + "░" * (10 - progress_blocks)
            response += f"   [{progress_bar}]\n"
            
            if goal.deadline:
                days_remaining = (goal.deadline.date() - datetime.now().date()).days
                if days_remaining > 0:
                    response += f"   ⏰ Deadline: {goal.deadline.strftime('%Y-%m-%d')} ({days_remaining} days remaining)\n"
                else:
                    response += f"   ⏰ Deadline: {goal.deadline.strftime('%Y-%m-%d')} (overdue)\n"
            
            # AI prediction if available
            if goal.predicted_probability is not None:
                prob_percent = goal.predicted_probability * 100
                if prob_percent >= 70:
                    emoji = "🟢"
                elif prob_percent >= 40:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                response += f"   {emoji} AI Prediction: {prob_percent:.0f}% chance of success\n"
            
            if goal.recommended_monthly_savings:
                response += f"   💡 Recommended: Save {goal.recommended_monthly_savings} {goal.currency}/month\n"
            
            response += f"   Status: {goal.status.title()}\n\n"
        
        # Summary stats
        active_goals = [g for g in goals if g.status == 'active']
        if active_goals:
            total_target = sum(float(g.target_amount) for g in active_goals)
            total_saved = sum(float(g.current_savings) for g in active_goals)
            overall_progress = (total_saved / total_target * 100) if total_target > 0 else 0
            
            response += f"{'='*50}\n"
            response += f"📊 Overall Progress: {overall_progress:.1f}%\n"
            response += f"💰 Total Target: {total_target:.2f}\n"
            response += f"💵 Total Saved: {total_saved:.2f}\n"
        
        return response
        
    except Exception as e:
        return f"Error getting financial goals: {str(e)}"


@tool
def create_financial_goal(
    title: str,
    target_amount: float,
    currency: str = "USD",
    deadline_days: int = 365,
    description: Optional[str] = None
) -> str:
    """
    Create a new financial savings goal with AI analysis.
    
    This tool creates a savings goal and automatically analyzes your financial
    profile to predict your chances of success. The AI will provide
    personalized recommendations for monthly savings and strategy.
    
    Args:
        title: Name of the goal (e.g., "Save for vacation", "Buy a car")
        target_amount: Amount you want to save
        currency: Currency code (default: 'USD')
        deadline_days: Days from now to achieve goal (default: 365)
        description: Optional detailed description of the goal
        
    Returns:
        A confirmation message with goal details and AI analysis including
        success probability and recommended monthly savings.
        
    Examples:
        User: "I want to save $10,000 for a car"
        User: "Create a goal to save $5,000 for vacation in 6 months"
        User: "Help me save $20,000 for a house down payment"
        User: "I need to save $3,000 in 90 days"
    """
    try:
        user_id = _goal_context.get("user_id")
        db = _goal_context.get("db")
        
        if not user_id or not db:
            return "Error: Goal context not set. Please try again."
        
        # Calculate deadline
        deadline = datetime.now() + timedelta(days=deadline_days)
        
        # Create goal data
        goal_data = GoalCreate(
            title=title,
            description=description or f"Save {target_amount} {currency} for {title.lower()}",
            target_amount=target_amount,
            current_savings=0,
            currency=currency,
            deadline=deadline
        )
        
        # Create goal with AI prediction
        goal_obj, prediction = FinancialGoalService.create_goal(db, user_id, goal_data)
        
        # Calculate progress (should be 0 for new goal)
        progress = (float(goal_obj.current_savings) / float(goal_obj.target_amount) * 100) if goal_obj.target_amount > 0 else 0
        
        # Format response
        response = "✅ Financial Goal Created!\n\n"
        response += f"🎯 Goal: {goal_obj.title}\n"
        response += f"💰 Target: {goal_obj.target_amount} {goal_obj.currency}\n"
        response += f"⏰ Deadline: {goal_obj.deadline.strftime('%Y-%m-%d')} ({deadline_days} days)\n\n"
        
        # AI Analysis
        response += "🤖 AI Analysis:\n"
        
        probability = prediction.get('probability', 0.5)
        prob_percent = probability * 100
        
        if prob_percent >= 70:
            response += f"   🟢 Success Probability: {prob_percent:.0f}% - Excellent chance!\n"
        elif prob_percent >= 40:
            response += f"   🟡 Success Probability: {prob_percent:.0f}% - Moderate challenge\n"
        else:
            response += f"   🔴 Success Probability: {prob_percent:.0f}% - Challenging goal\n"
        
        can_achieve = prediction.get('can_achieve', False)
        response += f"   {'✅' if can_achieve else '⚠️'} Assessment: {'Achievable' if can_achieve else 'May need adjustment'}\n"
        
        recommended_savings = prediction.get('recommended_monthly_savings', 0)
        if recommended_savings:
            response += f"\n💡 Recommendation:\n"
            response += f"   Save {recommended_savings:.2f} {goal_obj.currency} per month\n"
        
        risk_level = prediction.get('risk_level', 'medium')
        risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(risk_level, '🟡')
        response += f"   {risk_emoji} Risk Level: {risk_level.title()}\n"
        
        # Insights
        insights = prediction.get('insights', {})
        if insights:
            response += f"\n📊 Key Insights:\n"
            for key, value in insights.items():
                if isinstance(value, (int, float)):
                    response += f"   • {key.replace('_', ' ').title()}: {value:.2f}\n"
                else:
                    response += f"   • {key.replace('_', ' ').title()}: {value}\n"
        
        response += f"\nGoal ID: #{goal_obj.id} - Track progress with 'show my goals'"
        
        return response
        
    except Exception as e:
        return f"Error creating financial goal: {str(e)}"


@tool
def get_goal_analysis(goal_id: int) -> str:
    """
    Get detailed AI analysis for a specific financial goal.
    
    This tool provides in-depth analysis of a goal including success
    probability, recommended strategies, risk factors, and different
    scenarios (optimistic, realistic, pessimistic).
    
    Args:
        goal_id: The ID of the goal to analyze
        
    Returns:
        A detailed analysis report with AI predictions and recommendations.
        
    Examples:
        User: "Can I achieve goal 3?"
        User: "Analyze my savings goal"
        User: "What are my chances for goal 1?"
        User: "Is goal 2 realistic?"
    """
    try:
        user_id = _goal_context.get("user_id")
        db = _goal_context.get("db")
        
        if not user_id or not db:
            return "Error: Goal context not set. Please try again."
        
        # Get goal
        goal = FinancialGoalService.get_goal(db, goal_id, user_id)
        
        if not goal:
            return f"Goal #{goal_id} not found or you don't have permission to view it."
        
        # Get AI analysis
        try:
            analysis = FinancialGoalService.analyze_goal(db, goal_id, user_id)
        except:
            # Fallback if analysis endpoint doesn't exist
            analysis = {
                'probability': goal.predicted_probability or 0.5,
                'recommended_monthly_savings': goal.recommended_monthly_savings or 0,
                'risk_level': goal.risk_level or 'medium'
            }
        
        # Calculate progress
        progress = (float(goal.current_savings) / float(goal.target_amount) * 100) if goal.target_amount > 0 else 0
        remaining = float(goal.target_amount) - float(goal.current_savings)
        
        # Format response
        response = f"📊 AI Analysis for Goal #{goal.id}: {goal.title}\n\n"
        
        response += "📈 Current Status:\n"
        response += f"   Target: {goal.target_amount} {goal.currency}\n"
        response += f"   Saved: {goal.current_savings} {goal.currency} ({progress:.1f}%)\n"
        response += f"   Remaining: {remaining:.2f} {goal.currency}\n"
        
        if goal.deadline:
            days_remaining = (goal.deadline.date() - datetime.now().date()).days
            response += f"   Days Remaining: {days_remaining}\n"
            
            if days_remaining > 0 and remaining > 0:
                daily_needed = remaining / days_remaining
                response += f"   Daily Savings Needed: {daily_needed:.2f} {goal.currency}\n"
        
        response += "\n🤖 AI Predictions:\n"
        
        probability = analysis.get('probability', goal.predicted_probability or 0.5)
        prob_percent = probability * 100
        
        if prob_percent >= 70:
            response += f"   🟢 Success Rate: {prob_percent:.0f}% - Very Likely\n"
        elif prob_percent >= 40:
            response += f"   🟡 Success Rate: {prob_percent:.0f}% - Moderately Likely\n"
        else:
            response += f"   🔴 Success Rate: {prob_percent:.0f}% - Challenging\n"
        
        recommended = analysis.get('recommended_monthly_savings', goal.recommended_monthly_savings or 0)
        if recommended:
            response += f"   💰 Recommended Monthly: {recommended:.2f} {goal.currency}\n"
        
        risk = analysis.get('risk_level', goal.risk_level or 'medium')
        risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(risk, '🟡')
        response += f"   {risk_emoji} Risk Level: {risk.title()}\n"
        
        # Additional insights
        if isinstance(analysis, dict) and 'insights' in analysis:
            response += "\n💡 Key Insights:\n"
            insights = analysis['insights']
            if isinstance(insights, dict):
                for key, value in insights.items():
                    response += f"   • {key.replace('_', ' ').title()}: {value}\n"
        
        return response
        
    except Exception as e:
        return f"Error analyzing goal: {str(e)}"


@tool
def get_financial_summary() -> str:
    """
    Get a complete overview of your financial situation.
    
    This tool provides a comprehensive financial summary including all
    accounts, total balance, active goals, progress, and AI-powered
    insights about your financial health.
    
    Returns:
        A detailed financial summary report with accounts, goals, and
        overall financial health assessment.
        
    Examples:
        User: "What's my financial situation?"
        User: "Give me a financial overview"
        User: "Show my complete financial status"
        User: "How am I doing financially?"
    """
    try:
        user_id = _goal_context.get("user_id")
        db = _goal_context.get("db")
        
        if not user_id or not db:
            return "Error: Goal context not set. Please try again."
        
        try:
            # Get financial summary from service
            summary = FinancialGoalService.get_financial_summary(db, user_id)
        except:
            # Fallback if summary endpoint doesn't exist
            summary = {}
        
        # Get accounts
        from services.account import service as account_service
        accounts = account_service.get_user_accounts(user_id, db, include_deleted=False)
        
        # Get goals
        goals = FinancialGoalService.get_user_goals(db, user_id, status='active', skip=0, limit=100)
        
        # Format response
        response = "💼 Your Financial Summary\n"
        response += "="*50 + "\n\n"
        
        # Accounts section
        response += "🏦 Accounts:\n"
        if accounts:
            total_by_currency = {}
            for account in accounts:
                if account.status == 'active':
                    response += f"   • {account.account_type.title()} (#{account.id}): "
                    response += f"{account.balance} {account.currency}\n"
                    
                    currency = account.currency
                    if currency not in total_by_currency:
                        total_by_currency[currency] = 0
                    total_by_currency[currency] += float(account.balance)
            
            response += "\n   Total Balance:\n"
            for currency, total in total_by_currency.items():
                response += f"   💰 {total:.2f} {currency}\n"
        else:
            response += "   No active accounts\n"
        
        # Goals section
        response += "\n🎯 Financial Goals:\n"
        if goals:
            response += f"   Active Goals: {len(goals)}\n"
            total_target = sum(float(g.target_amount) for g in goals)
            total_saved = sum(float(g.current_savings) for g in goals)
            overall_progress = (total_saved / total_target * 100) if total_target > 0 else 0
            
            response += f"   Total Target: {total_target:.2f}\n"
            response += f"   Total Saved: {total_saved:.2f}\n"
            response += f"   Overall Progress: {overall_progress:.1f}%\n"
            
            # Show top 3 goals
            response += "\n   Top Goals:\n"
            for idx, goal in enumerate(goals[:3], 1):
                progress = (float(goal.current_savings) / float(goal.target_amount) * 100) if goal.target_amount > 0 else 0
                response += f"   {idx}. {goal.title}: {progress:.0f}% complete\n"
        else:
            response += "   No active goals\n"
        
        # Financial health indicators from summary
        if summary:
            response += "\n📊 Financial Health:\n"
            if 'total_accounts' in summary:
                response += f"   Accounts: {summary['total_accounts']}\n"
            if 'active_goals' in summary:
                response += f"   Active Goals: {summary['active_goals']}\n"
            if 'savings_rate' in summary:
                response += f"   Savings Rate: {summary['savings_rate']}%\n"
        
        response += "\n" + "="*50
        
        return response
        
    except Exception as e:
        return f"Error getting financial summary: {str(e)}"
