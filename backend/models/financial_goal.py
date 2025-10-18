from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Float, Text
from database import Base
from sqlalchemy.orm import relationship


class FinancialGoal(Base):
    """
    Модель для финансовых целей пользователей.
    Хранит цели накопления и ML-предсказания по их достижению.
    """
    __tablename__ = "financial_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Параметры цели
    goal_name = Column(String, nullable=False)  # 'квартира', 'путешествие', 'образование'
    goal_type = Column(String, nullable=False)  # 'real_estate', 'travel', 'education', 'emergency', 'other'
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_savings = Column(Numeric(15, 2), default=0.00)
    deadline_months = Column(Integer, nullable=False)  # Срок достижения цели в месяцах
    currency = Column(String(3), default='KZT')  # 'USD', 'EUR', 'KZT'
    
    # ML предсказания и рекомендации
    predicted_probability = Column(Float, nullable=True)  # Вероятность достижения (0-1)
    recommended_monthly_savings = Column(Numeric(15, 2), nullable=True)
    risk_level = Column(String, nullable=True)  # 'low', 'medium', 'high'
    ai_insights = Column(Text, nullable=True)  # JSON строка с инсайтами
    
    # Статус
    status = Column(String, default='active')  # 'active', 'achieved', 'failed', 'cancelled'
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="financial_goals")

