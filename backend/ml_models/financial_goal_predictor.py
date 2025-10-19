"""
Financial Goal Predictor

ML-based predictor for financial goal achievement probability.
Uses rule-based logic for predictions (can be replaced with trained ML model).
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FinancialGoalPredictor:
    """Predicts probability of achieving financial goals."""
    
    def __init__(self):
        """Initialize the predictor."""
        self.model_loaded = True
        logger.info("Financial goal predictor initialized")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict goal achievement probability and provide recommendations.
        
        Args:
            features: Dictionary containing:
                - avg_monthly_income: Average monthly income
                - avg_monthly_expenses: Average monthly expenses
                - current_savings: Current savings amount
                - target_amount: Target goal amount
                - deadline_months: Months until deadline
                - expense_volatility: Volatility in expenses
                
        Returns:
            Prediction dictionary with probability, recommendations, and risk level
        """
        avg_income = features.get('avg_monthly_income', 0.0)
        avg_expenses = features.get('avg_monthly_expenses', 0.0)
        current_savings = features.get('current_savings', 0.0)
        target_amount = features.get('target_amount', 0.0)
        deadline_months = features.get('deadline_months', 12)
        expense_volatility = features.get('expense_volatility', 0.0)
        
        try:
            monthly_savings_capacity = avg_income - avg_expenses
            required_monthly_savings = (
                (target_amount - current_savings) / deadline_months 
                if deadline_months > 0 else 0.0
            )
            
            probability = self._calculate_probability(
                monthly_savings_capacity,
                required_monthly_savings,
                current_savings,
                target_amount,
                deadline_months,
                expense_volatility,
                avg_income
            )
            
            risk_level = self._determine_risk_level(
                probability,
                required_monthly_savings,
                monthly_savings_capacity,
                expense_volatility,
                avg_income
            )
            
            recommended_monthly_savings = self._calculate_recommended_savings(
                target_amount,
                current_savings,
                deadline_months,
                monthly_savings_capacity,
                probability
            )
            
            insights = self._generate_insights(
                probability,
                risk_level,
                monthly_savings_capacity,
                required_monthly_savings,
                recommended_monthly_savings,
                deadline_months
            )
            
            result = {
                'probability': round(probability, 4),
                'recommended_monthly_savings': round(recommended_monthly_savings, 2),
                'risk_level': risk_level,
                'insights': insights,
                'model_version': '1.0',
                'prediction_date': datetime.now().isoformat()
            }
            
            logger.info(f"Prediction completed: probability={probability:.2f}, risk={risk_level}")
            return result
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            required_monthly = (target_amount - current_savings) / max(deadline_months, 1)
            
            return {
                'probability': 0.5,
                'recommended_monthly_savings': round(required_monthly, 2),
                'risk_level': 'medium',
                'insights': ['Unable to complete detailed analysis. Please review your financial data.'],
                'model_version': '1.0',
                'error': str(e)
            }
    
    def _calculate_probability(
        self,
        monthly_savings_capacity: float,
        required_monthly_savings: float,
        current_savings: float,
        target_amount: float,
        deadline_months: int,
        expense_volatility: float,
        avg_income: float
    ) -> float:
        """Calculate probability of goal achievement (0-1)."""
        
        # Base probability on savings capacity vs required savings
        if required_monthly_savings <= 0:
            return 1.0  # Already achieved
        
        if monthly_savings_capacity <= 0:
            return 0.1  # Very low if no savings capacity
        
        # Ratio of capacity to requirement
        capacity_ratio = monthly_savings_capacity / required_monthly_savings
        
        # Base probability from capacity ratio
        if capacity_ratio >= 1.5:
            base_prob = 0.9
        elif capacity_ratio >= 1.2:
            base_prob = 0.8
        elif capacity_ratio >= 1.0:
            base_prob = 0.7
        elif capacity_ratio >= 0.8:
            base_prob = 0.6
        elif capacity_ratio >= 0.6:
            base_prob = 0.4
        elif capacity_ratio >= 0.4:
            base_prob = 0.3
        else:
            base_prob = 0.2
        
        # Adjust for time horizon
        if deadline_months > 24:
            base_prob *= 0.9  # Longer term = more uncertainty
        elif deadline_months < 6:
            base_prob *= 0.95  # Short term = less flexibility
        
        # Adjust for volatility
        if avg_income > 0:
            volatility_ratio = expense_volatility / avg_income
            if volatility_ratio > 0.3:
                base_prob *= 0.85  # High volatility reduces probability
            elif volatility_ratio > 0.2:
                base_prob *= 0.92
        
        # Adjust for current progress
        progress_ratio = current_savings / target_amount if target_amount > 0 else 0
        if progress_ratio > 0.5:
            base_prob += 0.05  # Boost if already halfway
        elif progress_ratio > 0.25:
            base_prob += 0.03
        
        # Ensure probability is between 0 and 1
        return max(0.05, min(0.99, base_prob))
    
    def _determine_risk_level(
        self,
        probability: float,
        required_monthly_savings: float,
        monthly_savings_capacity: float,
        expense_volatility: float,
        avg_income: float
    ) -> str:
        """Determine risk level: low, medium, or high."""
        
        if probability >= 0.8:
            return 'low'
        elif probability >= 0.6:
            # Check if tight margin
            if monthly_savings_capacity < required_monthly_savings * 1.1:
                return 'medium'
            return 'low'
        elif probability >= 0.4:
            return 'medium'
        else:
            return 'high'
    
    def _calculate_recommended_savings(
        self,
        target_amount: float,
        current_savings: float,
        deadline_months: int,
        monthly_savings_capacity: float,
        probability: float
    ) -> float:
        """Calculate recommended monthly savings amount."""
        
        remaining_amount = target_amount - current_savings
        
        if deadline_months <= 0:
            return remaining_amount
        
        # Base recommendation with buffer
        buffer_multiplier = 1.1 if probability < 0.7 else 1.05
        recommended = (remaining_amount / deadline_months) * buffer_multiplier
        
        # Don't exceed capacity
        recommended = min(recommended, monthly_savings_capacity * 0.9)
        
        # Ensure minimum
        recommended = max(recommended, remaining_amount / deadline_months)
        
        return recommended
    
    def _generate_insights(
        self,
        probability: float,
        risk_level: str,
        monthly_savings_capacity: float,
        required_monthly_savings: float,
        recommended_monthly_savings: float,
        deadline_months: int
    ) -> List[str]:
        """Generate actionable insights based on prediction."""
        
        insights = []
        
        # Probability-based insights
        if probability >= 0.8:
            insights.append(f"You have a high chance ({probability*100:.0f}%) of achieving this goal.")
        elif probability >= 0.6:
            insights.append(f"You have a moderate chance ({probability*100:.0f}%) of achieving this goal.")
        else:
            insights.append(f"Achieving this goal may be challenging ({probability*100:.0f}% probability).")
        
        # Capacity vs requirement
        if monthly_savings_capacity < required_monthly_savings:
            shortage = required_monthly_savings - monthly_savings_capacity
            insights.append(
                f"Your current savings capacity (${monthly_savings_capacity:.2f}/month) "
                f"is ${shortage:.2f} short of what's needed."
            )
            insights.append("Consider increasing income or reducing expenses.")
        else:
            surplus = monthly_savings_capacity - required_monthly_savings
            insights.append(
                f"You have ${surplus:.2f}/month extra capacity beyond what's required."
            )
        
        # Recommendation
        insights.append(
            f"Save ${recommended_monthly_savings:.2f} per month to stay on track with a safety buffer."
        )
        
        # Timeline insight
        if deadline_months < 12:
            insights.append("This is a short-term goal. Focus on consistent monthly savings.")
        elif deadline_months > 24:
            insights.append("This is a long-term goal. Regular reviews and adjustments are important.")
        
        # Risk-based advice
        if risk_level == 'high':
            insights.append("Consider extending the deadline or reducing the target amount.")
        elif risk_level == 'medium':
            insights.append("Stay vigilant about unexpected expenses.")
        
        return insights
    
    def get_goal_recommendations(
        self,
        avg_income: float,
        avg_expenses: float,
        current_savings: float
    ) -> Dict[str, Any]:
        """
        Get general recommendations for setting financial goals.
        
        Args:
            avg_income: Average monthly income
            avg_expenses: Average monthly expenses
            current_savings: Current savings amount
            
        Returns:
            Recommendations dictionary
        """
        monthly_savings_capacity = avg_income - avg_expenses
        savings_rate = monthly_savings_capacity / avg_income if avg_income > 0 else 0
        
        recommendations = {
            'monthly_savings_capacity': monthly_savings_capacity,
            'savings_rate_percentage': savings_rate * 100,
            'recommended_emergency_fund': avg_expenses * 6,  # 6 months of expenses
            'has_emergency_fund': current_savings >= avg_expenses * 3,
            'suggestions': []
        }
        
        # Generate suggestions
        if savings_rate < 0.1:
            recommendations['suggestions'].append(
                "Try to save at least 10% of your income."
            )
        elif savings_rate < 0.2:
            recommendations['suggestions'].append(
                "Good start! Try to increase savings to 20% of income."
            )
        else:
            recommendations['suggestions'].append(
                "Excellent savings rate! You're on track for financial security."
            )
        
        if not recommendations['has_emergency_fund']:
            recommendations['suggestions'].append(
                "Priority: Build an emergency fund of 3-6 months of expenses."
            )
        
        if monthly_savings_capacity > 0:
            recommendations['suggestions'].append(
                f"You can comfortably save ${monthly_savings_capacity:.2f} per month."
            )
        
        return recommendations


# Create singleton instance
predictor = FinancialGoalPredictor()

