from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal


class GoalCreate(BaseModel):
    """Schema для создания новой финансовой цели."""
    goal_name: str = Field(..., min_length=1, max_length=200, description="Название цели")
    goal_type: str = Field(..., description="Тип цели: real_estate, travel, education, emergency, other")
    target_amount: Decimal = Field(..., gt=0, description="Целевая сумма")
    deadline_months: int = Field(..., gt=0, le=360, description="Срок в месяцах (до 30 лет)")
    currency: str = Field(default='KZT', description="Валюта")
    
    @validator('goal_type')
    def validate_goal_type(cls, v):
        allowed_types = ['real_estate', 'travel', 'education', 'emergency', 'other']
        if v not in allowed_types:
            raise ValueError(f"goal_type must be one of {allowed_types}")
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        allowed_currencies = ['KZT', 'USD', 'EUR', 'RUB']
        if v not in allowed_currencies:
            raise ValueError(f"currency must be one of {allowed_currencies}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "goal_name": "Покупка квартиры",
                "goal_type": "real_estate",
                "target_amount": 20000000,
                "deadline_months": 60,
                "currency": "KZT"
            }
        }


class GoalUpdate(BaseModel):
    """Schema для обновления финансовой цели."""
    goal_name: Optional[str] = Field(None, min_length=1, max_length=200)
    target_amount: Optional[Decimal] = Field(None, gt=0)
    deadline_months: Optional[int] = Field(None, gt=0, le=360)
    current_savings: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['active', 'achieved', 'failed', 'cancelled']
            if v not in allowed_statuses:
                raise ValueError(f"status must be one of {allowed_statuses}")
        return v


class MLPrediction(BaseModel):
    """Schema для ML предсказания."""
    probability: float = Field(..., ge=0, le=1, description="Вероятность достижения цели")
    recommended_monthly_savings: Decimal = Field(..., description="Рекомендуемая ежемесячная сумма")
    can_achieve: bool = Field(..., description="Достижимо ли в заданный срок")
    risk_level: str = Field(..., description="Уровень риска: low, medium, high")
    insights: List[str] = Field(default=[], description="Персонализированные рекомендации")
    scenarios: Dict = Field(default={}, description="Различные сценарии достижения")
    
    class Config:
        json_schema_extra = {
            "example": {
                "probability": 0.75,
                "recommended_monthly_savings": 350000,
                "can_achieve": True,
                "risk_level": "low",
                "insights": [
                    "✅ Отличные шансы! Вы на правильном пути к достижению цели.",
                    "👍 У вас хороший уровень сбережений (22%). Продолжайте в том же духе!"
                ],
                "scenarios": {
                    "optimistic": {
                        "months_needed": 48,
                        "monthly_savings": 420000,
                        "description": "При увеличении дохода на 20%"
                    }
                }
            }
        }


class FinancialProfile(BaseModel):
    """Schema для финансового профиля пользователя."""
    avg_monthly_income: Decimal
    avg_monthly_expenses: Decimal
    current_savings: Decimal
    expense_volatility: float
    income_volatility: float
    transaction_count: int
    category_breakdown: Dict
    trend: str
    analysis_period_months: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "avg_monthly_income": 500000,
                "avg_monthly_expenses": 350000,
                "current_savings": 2000000,
                "expense_volatility": 25000,
                "income_volatility": 10000,
                "transaction_count": 145,
                "category_breakdown": {
                    "purchase": 200000,
                    "withdrawal": 100000,
                    "transfer": 50000
                },
                "trend": "improving"
            }
        }


class GoalResponse(BaseModel):
    """Schema для ответа с информацией о цели."""
    id: int
    user_id: int
    goal_name: str
    goal_type: str
    target_amount: Decimal
    current_savings: Decimal
    deadline_months: int
    currency: str
    predicted_probability: Optional[float]
    recommended_monthly_savings: Optional[Decimal]
    risk_level: Optional[str]
    ai_insights: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Дополнительные поля
    prediction: Optional[MLPrediction] = None
    financial_profile: Optional[FinancialProfile] = None
    progress_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "goal_name": "Покупка квартиры",
                "goal_type": "real_estate",
                "target_amount": 20000000,
                "current_savings": 2000000,
                "deadline_months": 60,
                "currency": "KZT",
                "predicted_probability": 0.75,
                "recommended_monthly_savings": 350000,
                "risk_level": "low",
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "progress_percentage": 10.0
            }
        }


class GoalListResponse(BaseModel):
    """Schema для списка целей."""
    goals: List[GoalResponse]
    total: int
    active_goals: int
    achieved_goals: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "goals": [],
                "total": 5,
                "active_goals": 3,
                "achieved_goals": 2
            }
        }


class GoalRecommendations(BaseModel):
    """Schema для рекомендаций по целям."""
    current_savings_rate: float
    monthly_surplus: Decimal
    financial_health: str
    recommendations: Dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_savings_rate": 0.22,
                "monthly_surplus": 150000,
                "financial_health": "good",
                "recommendations": {
                    "short_term": {
                        "suggested_amount": 1350000,
                        "timeframe": "6-12 месяцев",
                        "examples": ["Отпуск", "Техника", "Курсы"]
                    }
                }
            }
        }

