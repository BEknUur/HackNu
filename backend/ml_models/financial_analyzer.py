"""
Financial Data Analyzer

Aggregates and analyzes user financial data from the database to provide
comprehensive insights for the AI financial advisor.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from models.account import Account
from models.financial_goal import FinancialGoal
from models.transaction import Transaction
from models.user import User

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """Analyzes user financial data and generates insights."""
    
    def __init__(self, db: Session, user_id: int):
        """
        Initialize analyzer for a specific user.
        
        Args:
            db: Database session
            user_id: User ID to analyze
        """
        self.db = db
        self.user_id = user_id
        self.user = self._get_user()
        
        if not self.user:
            raise ValueError(f"User {user_id} not found")
    
    def _get_user(self) -> Optional[User]:
        """Get user from database."""
        return self.db.query(User).filter(User.id == self.user_id).first()
    
    def get_comprehensive_analysis(
        self,
        months_back: int = 6
    ) -> Dict[str, Any]:
        """
        Generate comprehensive financial analysis.
        
        Args:
            months_back: Number of months to analyze
        
        Returns:
            Complete financial analysis dictionary
        """
        logger.info(f"Generating comprehensive analysis for user {self.user_id}")
        
        analysis = {
            "user_info": self._get_user_info(),
            "accounts_summary": self._get_accounts_summary(),
            "transactions_analysis": self._get_transactions_analysis(months_back),
            "spending_breakdown": self._get_spending_breakdown(months_back),
            "income_analysis": self._get_income_analysis(months_back),
            "financial_goals": self._get_financial_goals_analysis(),
            "financial_health": self._calculate_financial_health(months_back),
            "recommendations_data": self._get_recommendations_data(months_back),
            "generated_at": datetime.now().isoformat()
        }
        
        return analysis
    
    def _get_user_info(self) -> Dict[str, Any]:
        """Get basic user information."""
        return {
            "user_id": self.user.id,
            "name": f"{self.user.name} {self.user.surname}",
            "email": self.user.email,
            "member_since": self.user.created_at.isoformat() if self.user.created_at else None
        }
    
    def _get_accounts_summary(self) -> Dict[str, Any]:
        """Get summary of all user accounts."""
        accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == self.user_id,
                Account.deleted_at.is_(None),
                Account.status == 'active'
            )
        ).all()
        
        accounts_list = []
        total_balance_by_currency = {}
        
        for account in accounts:
            balance = float(account.balance)
            currency = account.currency
            
            accounts_list.append({
                "id": account.id,
                "type": account.account_type,
                "balance": balance,
                "currency": currency,
                "status": account.status
            })
            
            # Aggregate by currency
            if currency not in total_balance_by_currency:
                total_balance_by_currency[currency] = 0
            total_balance_by_currency[currency] += balance
        
        return {
            "total_accounts": len(accounts),
            "accounts": accounts_list,
            "total_balance_by_currency": total_balance_by_currency,
            "account_types": list(set(acc['type'] for acc in accounts_list))
        }
    
    def _get_transactions_analysis(self, months_back: int) -> Dict[str, Any]:
        """Analyze transaction patterns."""
        start_date = datetime.now() - timedelta(days=months_back * 30)
        
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.created_at >= start_date,
                Transaction.deleted_at.is_(None)
            )
        ).order_by(desc(Transaction.created_at)).all()
        
        # Categorize transactions
        by_type = {}
        total_count = len(transactions)
        recent_transactions = []
        
        for txn in transactions[:20]:  # Last 20 transactions
            recent_transactions.append({
                "id": txn.id,
                "amount": float(txn.amount),
                "currency": txn.currency,
                "type": txn.transaction_type,
                "description": txn.description,
                "date": txn.created_at.isoformat()
            })
        
        for txn in transactions:
            txn_type = txn.transaction_type
            if txn_type not in by_type:
                by_type[txn_type] = {
                    "count": 0,
                    "total_amount": 0,
                    "currency": txn.currency
                }
            by_type[txn_type]["count"] += 1
            by_type[txn_type]["total_amount"] += float(txn.amount)
        
        return {
            "total_transactions": total_count,
            "period_months": months_back,
            "by_type": by_type,
            "recent_transactions": recent_transactions,
            "average_transactions_per_month": total_count / months_back if months_back > 0 else 0
        }
    
    def _get_spending_breakdown(self, months_back: int) -> Dict[str, Any]:
        """Analyze spending patterns."""
        start_date = datetime.now() - timedelta(days=months_back * 30)
        spending_types = ['purchase', 'withdrawal', 'transfer']
        
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type.in_(spending_types),
                Transaction.created_at >= start_date,
                Transaction.deleted_at.is_(None)
            )
        ).all()
        
        total_spending = 0.0
        by_category: Dict[str, float] = {}
        monthly_spending: Dict[str, float] = {}
        
        for txn in transactions:
            amount = float(txn.amount)
            total_spending += amount
            
            category = txn.transaction_type
            by_category[category] = by_category.get(category, 0.0) + amount
            
            month_key = txn.created_at.strftime("%Y-%m")
            monthly_spending[month_key] = monthly_spending.get(month_key, 0.0) + amount
        
        avg_monthly_spending = total_spending / months_back if months_back > 0 else 0.0
        volatility = self._calculate_volatility(list(monthly_spending.values()))
        
        return {
            "total_spending": total_spending,
            "average_monthly_spending": avg_monthly_spending,
            "by_category": by_category,
            "monthly_breakdown": monthly_spending,
            "spending_volatility": volatility,
            "highest_spending_month": (
                max(monthly_spending.items(), key=lambda x: x[1])[0] 
                if monthly_spending else None
            ),
            "highest_spending_amount": max(monthly_spending.values()) if monthly_spending else 0.0
        }
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) <= 1:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _get_income_analysis(self, months_back: int) -> Dict[str, Any]:
        """Analyze income patterns."""
        start_date = datetime.now() - timedelta(days=months_back * 30)
        income_types = ['deposit']
        
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type.in_(income_types),
                Transaction.created_at >= start_date,
                Transaction.deleted_at.is_(None)
            )
        ).all()
        
        total_income = 0.0
        monthly_income: Dict[str, float] = {}
        
        for txn in transactions:
            amount = float(txn.amount)
            total_income += amount
            
            month_key = txn.created_at.strftime("%Y-%m")
            monthly_income[month_key] = monthly_income.get(month_key, 0.0) + amount
        
        avg_monthly_income = total_income / months_back if months_back > 0 else 0.0
        
        return {
            "total_income": total_income,
            "average_monthly_income": avg_monthly_income,
            "monthly_breakdown": monthly_income,
            "income_transactions_count": len(transactions)
        }
    
    def _get_financial_goals_analysis(self) -> Dict[str, Any]:
        """Analyze financial goals progress."""
        goals = self.db.query(FinancialGoal).filter(
            and_(
                FinancialGoal.user_id == self.user_id,
                FinancialGoal.deleted_at.is_(None)
            )
        ).all()
        
        active_goals = []
        achieved_goals = []
        total_target = 0
        total_saved = 0
        
        for goal in goals:
            goal_data = {
                "id": goal.id,
                "name": goal.goal_name,
                "type": goal.goal_type,
                "target_amount": float(goal.target_amount),
                "current_savings": float(goal.current_savings),
                "deadline_months": goal.deadline_months,
                "currency": goal.currency,
                "status": goal.status,
                "progress_percentage": (float(goal.current_savings) / float(goal.target_amount) * 100) if goal.target_amount > 0 else 0,
                "predicted_probability": float(goal.predicted_probability) if goal.predicted_probability else None,
                "recommended_monthly_savings": float(goal.recommended_monthly_savings) if goal.recommended_monthly_savings else None,
                "risk_level": goal.risk_level
            }
            
            if goal.status == 'active':
                active_goals.append(goal_data)
                total_target += float(goal.target_amount)
                total_saved += float(goal.current_savings)
            elif goal.status == 'achieved':
                achieved_goals.append(goal_data)
        
        return {
            "total_goals": len(goals),
            "active_goals": active_goals,
            "achieved_goals": achieved_goals,
            "total_target_amount": total_target,
            "total_current_savings": total_saved,
            "overall_progress_percentage": (total_saved / total_target * 100) if total_target > 0 else 0
        }
    
    def _calculate_financial_health(self, months_back: int) -> Dict[str, Any]:
        """Calculate overall financial health metrics."""
        accounts = self._get_accounts_summary()
        spending = self._get_spending_breakdown(months_back)
        income = self._get_income_analysis(months_back)
        
        # Calculate key metrics
        avg_monthly_income = income['average_monthly_income']
        avg_monthly_spending = spending['average_monthly_spending']
        
        # Savings rate
        monthly_savings = avg_monthly_income - avg_monthly_spending
        savings_rate = (monthly_savings / avg_monthly_income * 100) if avg_monthly_income > 0 else 0
        
        # Expense ratio
        expense_ratio = (avg_monthly_spending / avg_monthly_income * 100) if avg_monthly_income > 0 else 0
        
        # Financial health score (0-100)
        health_score = self._calculate_health_score(
            savings_rate=savings_rate,
            expense_ratio=expense_ratio,
            spending_volatility=spending['spending_volatility'],
            avg_monthly_income=avg_monthly_income
        )
        
        return {
            "health_score": health_score,
            "savings_rate_percentage": savings_rate,
            "expense_ratio_percentage": expense_ratio,
            "average_monthly_savings": monthly_savings,
            "spending_stability": "stable" if spending['spending_volatility'] < avg_monthly_spending * 0.2 else "volatile",
            "financial_status": self._get_financial_status(health_score)
        }
    
    def _calculate_health_score(
        self,
        savings_rate: float,
        expense_ratio: float,
        spending_volatility: float,
        avg_monthly_income: float
    ) -> float:
        """Calculate financial health score (0-100)."""
        score = 0
        
        # Savings rate component (40 points max)
        if savings_rate >= 20:
            score += 40
        elif savings_rate >= 10:
            score += 30
        elif savings_rate >= 0:
            score += 20
        
        # Expense ratio component (30 points max)
        if expense_ratio <= 50:
            score += 30
        elif expense_ratio <= 70:
            score += 20
        elif expense_ratio <= 90:
            score += 10
        
        # Spending stability (30 points max)
        volatility_ratio = (
            spending_volatility / avg_monthly_income 
            if avg_monthly_income > 0 else 1
        )
        if volatility_ratio < 0.1:
            score += 30
        elif volatility_ratio < 0.2:
            score += 20
        elif volatility_ratio < 0.3:
            score += 10
        
        return min(100, max(0, score))
    
    def _get_financial_status(self, health_score: float) -> str:
        """Get financial status label based on health score."""
        if health_score >= 80:
            return "Excellent"
        elif health_score >= 60:
            return "Good"
        elif health_score >= 40:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _get_recommendations_data(self, months_back: int) -> Dict[str, Any]:
        """Gather data points for generating recommendations."""
        spending = self._get_spending_breakdown(months_back)
        income = self._get_income_analysis(months_back)
        health = self._calculate_financial_health(months_back)
        
        avg_monthly_income = income['average_monthly_income']
        avg_monthly_spending = spending['average_monthly_spending']
        
        return {
            "needs_budget_adjustment": health['expense_ratio_percentage'] > 80,
            "needs_savings_increase": health['savings_rate_percentage'] < 10,
            "spending_is_volatile": spending['spending_volatility'] > avg_monthly_income * 0.2,
            "has_negative_cash_flow": avg_monthly_income < avg_monthly_spending,
            "top_spending_categories": sorted(
                spending['by_category'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        }

