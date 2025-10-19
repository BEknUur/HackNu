"""
Financial Data Processor

Processes financial data for ML predictions and analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models.account import Account
from models.transaction import Transaction

logger = logging.getLogger(__name__)


class FinancialDataProcessor:
    """Process financial data for ML models and analysis."""
    
    @staticmethod
    def calculate_user_financial_profile(
        db: Session,
        user_id: int,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Calculate user's financial profile for ML predictions.
        
        Args:
            db: Database session
            user_id: User ID
            months: Number of months to analyze
            
        Returns:
            Financial profile dictionary
        """
        start_date = datetime.now() - timedelta(days=months * 30)
        
        accounts = db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.deleted_at.is_(None),
                Account.status == 'active'
            )
        ).all()
        
        current_savings = sum(float(acc.balance) for acc in accounts)
        
        transactions = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.created_at >= start_date,
                Transaction.deleted_at.is_(None)
            )
        ).all()
        
        income_transactions = [t for t in transactions if t.transaction_type == 'deposit']
        total_income = sum(float(t.amount) for t in income_transactions)
        avg_monthly_income = total_income / months if months > 0 else 0.0
        
        expense_types = ['purchase', 'withdrawal', 'transfer']
        expense_transactions = [t for t in transactions if t.transaction_type in expense_types]
        total_expenses = sum(float(t.amount) for t in expense_transactions)
        avg_monthly_expenses = total_expenses / months if months > 0 else 0.0
        
        monthly_expenses: Dict[str, float] = {}
        for t in expense_transactions:
            month_key = t.created_at.strftime("%Y-%m")
            monthly_expenses[month_key] = monthly_expenses.get(month_key, 0.0) + float(t.amount)
        
        expense_volatility = FinancialDataProcessor._calculate_std_dev(
            list(monthly_expenses.values())
        )
        
        profile = {
            'user_id': user_id,
            'current_savings': current_savings,
            'avg_monthly_income': avg_monthly_income,
            'avg_monthly_expenses': avg_monthly_expenses,
            'expense_volatility': expense_volatility,
            'total_accounts': len(accounts),
            'transaction_count': len(transactions),
            'analysis_period_months': months
        }
        
        logger.info(f"Financial profile calculated for user {user_id}")
        return profile
    
    @staticmethod
    def prepare_ml_features(
        financial_profile: Dict[str, Any],
        goal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare features for ML model prediction.
        
        Args:
            financial_profile: User's financial profile
            goal_data: Goal information
            
        Returns:
            Feature dictionary for ML model
        """
        avg_income = financial_profile['avg_monthly_income']
        avg_expenses = financial_profile['avg_monthly_expenses']
        current_savings = financial_profile['current_savings']
        target_amount = float(goal_data.get('target_amount', 0))
        deadline_months = int(goal_data.get('deadline_months', 12))
        
        monthly_savings_capacity = avg_income - avg_expenses
        
        features = {
            'avg_monthly_income': avg_income,
            'avg_monthly_expenses': avg_expenses,
            'current_savings': current_savings,
            'expense_volatility': financial_profile['expense_volatility'],
            'target_amount': target_amount,
            'deadline_months': deadline_months,
            'goal_type': goal_data.get('goal_type', 'other'),
            'monthly_savings_capacity': monthly_savings_capacity,
            'savings_rate': (
                monthly_savings_capacity / avg_income if avg_income > 0 else 0.0
            ),
            'required_monthly_savings': (
                (target_amount - current_savings) / deadline_months
                if deadline_months > 0 else 0.0
            )
        }
        
        return features
    
    @staticmethod
    def _calculate_std_dev(values: list) -> float:
        """Calculate standard deviation of values."""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

