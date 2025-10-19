"""
API routes for Financial Goals service.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models.financial_goal import FinancialGoal
import json
import logging

from .service import FinancialGoalService
from .schemas import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalListResponse,
    GoalRecommendations,
    MLPrediction
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financial-goals", tags=["Financial Goals"])


# Временная функция для получения текущего пользователя
# TODO: Заменить на реальную аутентификацию из JWT токена
def get_current_user_id(user_id: int = Query(1, description="User ID (temporary)")):
    """Временная функция для получения ID пользователя."""
    return user_id


def _enrich_goal_response(goal: FinancialGoal) -> GoalResponse:
    """
    Обогатить объект цели дополнительными данными для ответа.
    
    Args:
        goal: Объект финансовой цели из БД
    
    Returns:
        Обогащенный GoalResponse с прогрессом и предсказанием
    """
    response = GoalResponse.model_validate(goal)
    
    # Добавляем прогресс
    response.progress_percentage = (
        float(goal.current_savings) / float(goal.target_amount) * 100
        if goal.target_amount > 0 else 0
    )
    
    # Парсим инсайты если есть
    if goal.ai_insights:
        try:
            insights = json.loads(goal.ai_insights)
            response.prediction = MLPrediction(
                probability=goal.predicted_probability or 0.0,
                recommended_monthly_savings=goal.recommended_monthly_savings or 0,
                can_achieve=goal.predicted_probability >= 0.5 if goal.predicted_probability else False,
                risk_level=goal.risk_level or 'medium',
                insights=insights,
                scenarios={}
            )
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse ai_insights for goal {goal.id}")
    
    return response


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_goal(
    goal: GoalCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Создать новую финансовую цель с ML предсказанием.
    
    Система автоматически:
    - Анализирует финансовый профиль пользователя
    - Рассчитывает вероятность достижения цели
    - Дает персонализированные рекомендации
    - Предлагает оптимальную стратегию накопления
    """
    try:
        goal_obj, prediction = FinancialGoalService.create_goal(db, user_id, goal)
        
        # Преобразуем в response схему с обогащением
        response = _enrich_goal_response(goal_obj)
        
        # Обновляем предсказание из ML модели
        response.prediction = MLPrediction(**prediction)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in create_financial_goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create goal: {str(e)}"
        )


@router.get("/", response_model=GoalListResponse)
async def get_user_goals(
    user_id: int = Depends(get_current_user_id),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, achieved, failed, cancelled"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Получить список всех финансовых целей пользователя.
    
    Можно фильтровать по статусу и использовать пагинацию.
    """
    try:
        goals = FinancialGoalService.get_user_goals(
            db, user_id, status=status_filter, skip=skip, limit=limit
        )
        
        # Преобразуем в response с обогащением
        goals_response = [_enrich_goal_response(goal) for goal in goals]
        
        # Статистика
        all_goals = FinancialGoalService.get_user_goals(db, user_id)
        active_count = sum(1 for g in all_goals if g.status == 'active')
        achieved_count = sum(1 for g in all_goals if g.status == 'achieved')
        
        return GoalListResponse(
            goals=goals_response,
            total=len(all_goals),
            active_goals=active_count,
            achieved_goals=achieved_count
        )
        
    except Exception as e:
        logger.error(f"Error in get_user_goals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get goals: {str(e)}"
        )


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Получить детальную информацию о конкретной цели.
    """
    try:
        goal = FinancialGoalService.get_goal(db, goal_id, user_id)
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal with id {goal_id} not found"
            )
        
        return _enrich_goal_response(goal)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get goal: {str(e)}"
        )


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_update: GoalUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Обновить финансовую цель.
    
    При изменении критичных параметров (сумма, срок) система автоматически
    пересчитает предсказание и обновит рекомендации.
    """
    try:
        goal = FinancialGoalService.update_goal(db, goal_id, user_id, goal_update)
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal with id {goal_id} not found"
            )
        
        return _enrich_goal_response(goal)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update goal: {str(e)}"
        )


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Удалить финансовую цель (мягкое удаление).
    """
    try:
        success = FinancialGoalService.delete_goal(db, goal_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal with id {goal_id} not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete goal: {str(e)}"
        )


@router.get("/{goal_id}/analysis", response_model=dict)
async def get_goal_analysis(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Получить подробный анализ цели с актуальным ML предсказанием.
    
    Возвращает:
    - Текущий прогресс
    - Актуальное предсказание (пересчитанное)
    - Финансовый профиль
    - Различные сценарии достижения
    - Персонализированные рекомендации
    """
    try:
        analysis = FinancialGoalService.get_goal_analysis(db, goal_id, user_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal with id {goal_id} not found"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_goal_analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze goal: {str(e)}"
        )


@router.post("/{goal_id}/update-progress", response_model=GoalResponse)
async def update_goal_progress(
    goal_id: int,
    new_amount: float = Query(..., description="Новая сумма накоплений"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Обновить прогресс по цели (текущую сумму накоплений).
    
    При достижении целевой суммы статус автоматически меняется на 'achieved'.
    """
    try:
        goal = FinancialGoalService.update_goal_progress(db, goal_id, user_id, new_amount)
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal with id {goal_id} not found"
            )
        
        return _enrich_goal_response(goal)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_goal_progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}"
        )


@router.get("/user/financial-summary", response_model=dict)
async def get_financial_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Получить полную финансовую сводку пользователя.
    
    Включает:
    - Финансовый профиль (доходы, расходы, тренды)
    - Статистику по целям
    - Рекомендации по новым целям
    - Общую оценку финансового здоровья
    """
    try:
        summary = FinancialGoalService.get_user_financial_summary(db, user_id)
        return summary
        
    except Exception as e:
        logger.error(f"Error in get_financial_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial summary: {str(e)}"
        )


@router.get("/recommendations/goal-suggestions", response_model=GoalRecommendations)
async def get_goal_recommendations(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Получить персонализированные рекомендации по постановке финансовых целей.
    
    На основе анализа доходов и расходов система предложит оптимальные
    суммы и сроки для различных типов целей.
    """
    try:
        from ml_models.data_processor import FinancialDataProcessor
        from ml_models.financial_goal_predictor import predictor
        
        # Получаем финансовый профиль
        profile = FinancialDataProcessor.calculate_user_financial_profile(db, user_id)
        
        # Получаем рекомендации
        recommendations = predictor.get_goal_recommendations(
            avg_income=profile['avg_monthly_income'],
            avg_expenses=profile['avg_monthly_expenses'],
            current_savings=profile['current_savings']
        )
        
        return GoalRecommendations(**recommendations)
        
    except Exception as e:
        logger.error(f"Error in get_goal_recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )



