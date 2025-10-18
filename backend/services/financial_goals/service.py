"""
Business logic for Financial Goals service.
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import json
import logging

from models.financial_goal import FinancialGoal
from ml_models.financial_goal_predictor import predictor
from ml_models.data_processor import FinancialDataProcessor
from .schemas import GoalCreate, GoalUpdate

logger = logging.getLogger(__name__)


class FinancialGoalService:
    """Сервис для работы с финансовыми целями."""
    
    @staticmethod
    def create_goal(
        db: Session,
        user_id: int,
        goal_data: GoalCreate
    ) -> tuple[FinancialGoal, Dict]:
        """
        Создание новой финансовой цели с ML предсказанием.
        
        Args:
            db: Database session
            user_id: ID пользователя
            goal_data: Данные цели
        
        Returns:
            Tuple[FinancialGoal, Dict]: Созданная цель и предсказание
        """
        try:
            # Получаем финансовый профиль пользователя
            financial_profile = FinancialDataProcessor.calculate_user_financial_profile(
                db, user_id, months=6
            )
            
            # Подготавливаем данные для ML модели
            ml_input = FinancialDataProcessor.prepare_ml_features(
                financial_profile,
                goal_data.model_dump()
            )
            
            # Получаем предсказание от ML модели
            prediction = predictor.predict(ml_input)
            
            # Создаем цель в БД
            goal = FinancialGoal(
                user_id=user_id,
                goal_name=goal_data.goal_name,
                goal_type=goal_data.goal_type,
                target_amount=goal_data.target_amount,
                current_savings=financial_profile['current_savings'],
                deadline_months=goal_data.deadline_months,
                currency=goal_data.currency,
                predicted_probability=prediction['probability'],
                recommended_monthly_savings=prediction['recommended_monthly_savings'],
                risk_level=prediction['risk_level'],
                ai_insights=json.dumps(prediction['insights'], ensure_ascii=False)
            )
            
            db.add(goal)
            db.commit()
            db.refresh(goal)
            
            logger.info(f"Goal created: id={goal.id}, user={user_id}, probability={prediction['probability']}")
            
            return goal, prediction
            
        except Exception as e:
            logger.error(f"Error creating goal for user {user_id}: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_goal(
        db: Session,
        goal_id: int,
        user_id: int
    ) -> Optional[FinancialGoal]:
        """Получить цель по ID."""
        return db.query(FinancialGoal).filter(
            and_(
                FinancialGoal.id == goal_id,
                FinancialGoal.user_id == user_id,
                FinancialGoal.deleted_at.is_(None)
            )
        ).first()
    
    @staticmethod
    def get_user_goals(
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FinancialGoal]:
        """Получить все цели пользователя."""
        query = db.query(FinancialGoal).filter(
            and_(
                FinancialGoal.user_id == user_id,
                FinancialGoal.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.filter(FinancialGoal.status == status)
        
        return query.order_by(FinancialGoal.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_goal(
        db: Session,
        goal_id: int,
        user_id: int,
        update_data: GoalUpdate
    ) -> Optional[FinancialGoal]:
        """
        Обновление финансовой цели.
        При изменении параметров пересчитывает предсказание.
        """
        try:
            goal = FinancialGoalService.get_goal(db, goal_id, user_id)
            if not goal:
                return None
            
            # Обновляем поля
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Проверяем, изменились ли критичные параметры
            recalculate_prediction = any(
                field in update_dict
                for field in ['target_amount', 'deadline_months', 'current_savings']
            )
            
            for field, value in update_dict.items():
                setattr(goal, field, value)
            
            # Пересчитываем предсказание если нужно
            if recalculate_prediction:
                financial_profile = FinancialDataProcessor.calculate_user_financial_profile(
                    db, user_id, months=6
                )
                
                ml_input = {
                    'avg_monthly_income': financial_profile['avg_monthly_income'],
                    'avg_monthly_expenses': financial_profile['avg_monthly_expenses'],
                    'current_savings': float(goal.current_savings),
                    'target_amount': float(goal.target_amount),
                    'deadline_months': goal.deadline_months,
                    'expense_volatility': financial_profile['expense_volatility']
                }
                
                prediction = predictor.predict(ml_input)
                
                goal.predicted_probability = prediction['probability']
                goal.recommended_monthly_savings = prediction['recommended_monthly_savings']
                goal.risk_level = prediction['risk_level']
                goal.ai_insights = json.dumps(prediction['insights'], ensure_ascii=False)
            
            goal.updated_at = datetime.now()
            db.commit()
            db.refresh(goal)
            
            logger.info(f"Goal updated: id={goal_id}")
            return goal
            
        except Exception as e:
            logger.error(f"Error updating goal {goal_id}: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def delete_goal(
        db: Session,
        goal_id: int,
        user_id: int
    ) -> bool:
        """Мягкое удаление цели."""
        try:
            goal = FinancialGoalService.get_goal(db, goal_id, user_id)
            if not goal:
                return False
            
            goal.deleted_at = datetime.now()
            goal.status = 'cancelled'
            db.commit()
            
            logger.info(f"Goal deleted: id={goal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting goal {goal_id}: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_goal_analysis(
        db: Session,
        goal_id: int,
        user_id: int
    ) -> Optional[Dict]:
        """
        Получить подробный анализ цели.
        Пересчитывает актуальное предсказание на основе текущих данных.
        """
        try:
            goal = FinancialGoalService.get_goal(db, goal_id, user_id)
            if not goal:
                return None
            
            # Получаем актуальный финансовый профиль
            financial_profile = FinancialDataProcessor.calculate_user_financial_profile(
                db, user_id, months=6
            )
            
            # Пересчитываем предсказание
            ml_input = {
                'avg_monthly_income': financial_profile['avg_monthly_income'],
                'avg_monthly_expenses': financial_profile['avg_monthly_expenses'],
                'current_savings': float(goal.current_savings),
                'target_amount': float(goal.target_amount),
                'deadline_months': goal.deadline_months,
                'expense_volatility': financial_profile['expense_volatility']
            }
            
            prediction = predictor.predict(ml_input)
            
            # Рассчитываем прогресс
            progress_percentage = (float(goal.current_savings) / float(goal.target_amount)) * 100 if goal.target_amount > 0 else 0
            
            # Рассчитываем сколько осталось времени
            months_passed = (datetime.now() - goal.created_at).days / 30
            months_remaining = max(0, goal.deadline_months - months_passed)
            
            analysis = {
                'goal': {
                    'id': goal.id,
                    'name': goal.goal_name,
                    'type': goal.goal_type,
                    'target_amount': float(goal.target_amount),
                    'current_savings': float(goal.current_savings),
                    'deadline_months': goal.deadline_months,
                    'currency': goal.currency,
                    'status': goal.status
                },
                'progress': {
                    'percentage': round(progress_percentage, 2),
                    'remaining_amount': float(goal.target_amount) - float(goal.current_savings),
                    'months_passed': round(months_passed, 1),
                    'months_remaining': round(months_remaining, 1)
                },
                'prediction': prediction,
                'financial_profile': financial_profile,
                'created_at': goal.created_at.isoformat(),
                'updated_at': goal.updated_at.isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing goal {goal_id}: {e}")
            raise
    
    @staticmethod
    def get_user_financial_summary(
        db: Session,
        user_id: int
    ) -> Dict:
        """
        Получить общую финансовую сводку пользователя.
        """
        try:
            # Финансовый профиль
            financial_profile = FinancialDataProcessor.calculate_user_financial_profile(
                db, user_id, months=6
            )
            
            # Статистика по целям
            all_goals = FinancialGoalService.get_user_goals(db, user_id)
            active_goals = [g for g in all_goals if g.status == 'active']
            achieved_goals = [g for g in all_goals if g.status == 'achieved']
            
            total_target = sum(float(g.target_amount) for g in active_goals)
            total_saved = sum(float(g.current_savings) for g in active_goals)
            
            # Рекомендации
            recommendations = predictor.get_goal_recommendations(
                avg_income=financial_profile['avg_monthly_income'],
                avg_expenses=financial_profile['avg_monthly_expenses'],
                current_savings=financial_profile['current_savings']
            )
            
            summary = {
                'financial_profile': financial_profile,
                'goals_summary': {
                    'total_goals': len(all_goals),
                    'active_goals': len(active_goals),
                    'achieved_goals': len(achieved_goals),
                    'total_target_amount': total_target,
                    'total_current_savings': total_saved,
                    'overall_progress': (total_saved / total_target * 100) if total_target > 0 else 0
                },
                'recommendations': recommendations
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting financial summary for user {user_id}: {e}")
            raise
    
    @staticmethod
    def update_goal_progress(
        db: Session,
        goal_id: int,
        user_id: int,
        new_savings_amount: float
    ) -> Optional[FinancialGoal]:
        """
        Обновить прогресс по цели (текущие сбережения).
        """
        try:
            goal = FinancialGoalService.get_goal(db, goal_id, user_id)
            if not goal:
                return None
            
            goal.current_savings = new_savings_amount
            
            # Проверяем достигнута ли цель
            if new_savings_amount >= goal.target_amount:
                goal.status = 'achieved'
            
            goal.updated_at = datetime.now()
            db.commit()
            db.refresh(goal)
            
            logger.info(f"Goal progress updated: id={goal_id}, new_amount={new_savings_amount}")
            return goal
            
        except Exception as e:
            logger.error(f"Error updating goal progress {goal_id}: {e}")
            db.rollback()
            raise

