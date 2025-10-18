import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class FinancialGoalPredictor:
    """
    ML модель для прогнозирования достижения финансовых целей.
    
    Использует эвристический подход, основанный на финансовой математике:
    - Анализ доходов и расходов
    - Расчет требуемых накоплений
    - Оценка вероятности достижения цели
    - Генерация персонализированных рекомендаций
    """
    
    def __init__(self, model_path: str = "ml_models/saved_models/"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        # Пороги для классификации риска
        self.risk_thresholds = {
            'low': 0.7,      # >= 70% вероятность
            'medium': 0.4,   # 40-70% вероятность
            'high': 0.4      # < 40% вероятность
        }
        
        # Рекомендуемые коэффициенты сбережений
        self.savings_rate_recommendations = {
            'conservative': 0.3,  # 30% от дохода
            'moderate': 0.2,      # 20% от дохода
            'aggressive': 0.4     # 40% от дохода
        }
    
    def predict(self, user_data: Dict) -> Dict:
        """
        Делает предсказание для конкретного пользователя.
        
        Args:
            user_data: {
                'avg_monthly_income': float,
                'avg_monthly_expenses': float,
                'current_savings': float,
                'target_amount': float,
                'deadline_months': int,
                'expense_volatility': float (optional)
            }
        
        Returns:
            {
                'probability': float,                  # Вероятность достижения (0-1)
                'recommended_monthly_savings': float,  # Рекомендуемая сумма
                'can_achieve': bool,                   # Достижимо ли
                'risk_level': str,                     # 'low', 'medium', 'high'
                'insights': List[str],                 # Персонализированные советы
                'scenarios': Dict                      # Разные сценарии
            }
        """
        try:
            # Валидация входных данных
            self._validate_input(user_data)
            
            # Основной расчет
            prediction = self._calculate_prediction(user_data)
            
            # Генерация сценариев
            scenarios = self._generate_scenarios(user_data)
            prediction['scenarios'] = scenarios
            
            # Генерация инсайтов
            insights = self._generate_insights(user_data, prediction)
            prediction['insights'] = insights
            
            logger.info(f"Prediction completed: probability={prediction['probability']:.2f}")
            return prediction
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            raise
    
    def _validate_input(self, user_data: Dict) -> None:
        """Валидация входных данных."""
        required_fields = [
            'avg_monthly_income',
            'avg_monthly_expenses',
            'current_savings',
            'target_amount',
            'deadline_months'
        ]
        
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Missing required field: {field}")
            
            if user_data[field] < 0:
                raise ValueError(f"Field {field} cannot be negative")
        
        if user_data['deadline_months'] <= 0:
            raise ValueError("Deadline must be greater than 0")
    
    def _calculate_prediction(self, user_data: Dict) -> Dict:
        """Основной расчет предсказания."""
        avg_income = float(user_data['avg_monthly_income'])
        avg_expenses = float(user_data['avg_monthly_expenses'])
        current_savings = float(user_data['current_savings'])
        target_amount = float(user_data['target_amount'])
        deadline_months = int(user_data['deadline_months'])
        
        # Текущая способность к накоплению
        monthly_surplus = max(0, avg_income - avg_expenses)
        
        # Сколько нужно накопить
        remaining_amount = max(0, target_amount - current_savings)
        
        # Требуемая ежемесячная сумма
        if deadline_months > 0:
            required_monthly = remaining_amount / deadline_months
        else:
            required_monthly = remaining_amount
        
        # Базовая вероятность (отношение возможностей к требованиям)
        if required_monthly > 0:
            base_probability = min(1.0, monthly_surplus / required_monthly)
        else:
            base_probability = 1.0  # Цель уже достигнута
        
        # Корректировка вероятности с учетом волатильности
        expense_volatility = user_data.get('expense_volatility', 0.1)
        volatility_penalty = min(0.2, expense_volatility * 0.5)  # Максимум 20% штрафа
        adjusted_probability = max(0.0, base_probability - volatility_penalty)
        
        # Учитываем горизонт планирования (чем дальше, тем выше риск)
        time_penalty = min(0.1, (deadline_months / 120) * 0.1)  # Макс 10% за 10 лет
        final_probability = max(0.0, adjusted_probability - time_penalty)
        
        # Рекомендуемая сумма (с 15% запасом)
        recommended_savings = required_monthly * 1.15
        
        # Определение уровня риска
        if final_probability >= self.risk_thresholds['low']:
            risk_level = 'low'
        elif final_probability >= self.risk_thresholds['medium']:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        # Проверка достижимости
        can_achieve = monthly_surplus >= required_monthly * 0.8  # 80% порог
        
        return {
            'probability': round(final_probability, 3),
            'recommended_monthly_savings': round(recommended_savings, 2),
            'can_achieve': can_achieve,
            'risk_level': risk_level,
            'monthly_surplus': round(monthly_surplus, 2),
            'required_monthly': round(required_monthly, 2),
            'remaining_amount': round(remaining_amount, 2)
        }
    
    def _generate_scenarios(self, user_data: Dict) -> Dict:
        """
        Генерация разных сценариев достижения цели.
        """
        target_amount = float(user_data['target_amount'])
        current_savings = float(user_data['current_savings'])
        avg_income = float(user_data['avg_monthly_income'])
        avg_expenses = float(user_data['avg_monthly_expenses'])
        deadline_months = int(user_data['deadline_months'])
        
        monthly_surplus = max(0, avg_income - avg_expenses)
        remaining = target_amount - current_savings
        
        scenarios = {}
        
        # Оптимистичный сценарий (увеличение дохода на 20%)
        optimistic_income = avg_income * 1.2
        optimistic_surplus = optimistic_income - avg_expenses
        if optimistic_surplus > 0:
            optimistic_months = int(remaining / optimistic_surplus)
            scenarios['optimistic'] = {
                'months_needed': optimistic_months,
                'monthly_savings': round(optimistic_surplus, 2),
                'description': 'При увеличении дохода на 20%'
            }
        
        # Реалистичный сценарий (текущий темп)
        if monthly_surplus > 0:
            realistic_months = int(remaining / monthly_surplus)
            scenarios['realistic'] = {
                'months_needed': realistic_months,
                'monthly_savings': round(monthly_surplus, 2),
                'description': 'При текущем уровне доходов и расходов'
            }
        
        # Пессимистичный сценарий (увеличение расходов на 10%)
        pessimistic_expenses = avg_expenses * 1.1
        pessimistic_surplus = max(0, avg_income - pessimistic_expenses)
        if pessimistic_surplus > 0:
            pessimistic_months = int(remaining / pessimistic_surplus)
            scenarios['pessimistic'] = {
                'months_needed': pessimistic_months,
                'monthly_savings': round(pessimistic_surplus, 2),
                'description': 'При увеличении расходов на 10%'
            }
        
        # Агрессивный сценарий (сокращение расходов на 20%)
        aggressive_expenses = avg_expenses * 0.8
        aggressive_surplus = avg_income - aggressive_expenses
        if aggressive_surplus > 0:
            aggressive_months = int(remaining / aggressive_surplus)
            scenarios['aggressive'] = {
                'months_needed': aggressive_months,
                'monthly_savings': round(aggressive_surplus, 2),
                'description': 'При сокращении расходов на 20%'
            }
        
        return scenarios
    
    def _generate_insights(self, user_data: Dict, prediction: Dict) -> List[str]:
        """Генерация персонализированных советов."""
        insights = []
        
        avg_income = float(user_data['avg_monthly_income'])
        avg_expenses = float(user_data['avg_monthly_expenses'])
        current_savings = float(user_data['current_savings'])
        target_amount = float(user_data['target_amount'])
        deadline_months = int(user_data['deadline_months'])
        
        probability = prediction['probability']
        recommended_savings = prediction['recommended_monthly_savings']
        monthly_surplus = prediction['monthly_surplus']
        risk_level = prediction['risk_level']
        
        # Анализ вероятности достижения
        if probability >= 0.8:
            insights.append("✅ Отличные шансы! Вы на правильном пути к достижению цели.")
        elif probability >= 0.5:
            insights.append("⚠️ Цель достижима, но требует дисциплины и возможно корректировки расходов.")
        else:
            insights.append("🔴 Текущий план требует серьезной корректировки. Рассмотрите изменение срока или суммы цели.")
        
        # Анализ рекомендуемой суммы
        savings_to_income_ratio = recommended_savings / avg_income if avg_income > 0 else 0
        if savings_to_income_ratio > 0.5:
            insights.append(f"💡 Рекомендуемая сумма ({recommended_savings:,.0f} ₸) составляет более 50% дохода. "
                          f"Рассмотрите увеличение срока до {int(deadline_months * 1.5)} месяцев.")
        elif savings_to_income_ratio > 0.3:
            insights.append(f"📊 Для достижения цели потребуется откладывать около {savings_to_income_ratio*100:.0f}% дохода.")
        
        # Анализ текущего уровня сбережений
        current_savings_rate = monthly_surplus / avg_income if avg_income > 0 else 0
        if current_savings_rate < 0.1:
            insights.append(f"⚡ Текущий уровень сбережений низкий ({current_savings_rate*100:.1f}%). "
                          f"Рекомендуем начать с оптимизации расходов.")
        elif current_savings_rate >= 0.2:
            insights.append(f"👍 У вас хороший уровень сбережений ({current_savings_rate*100:.0f}%). Продолжайте в том же духе!")
        
        # Рекомендации по срокам
        if recommended_savings > monthly_surplus * 1.5:
            suggested_months = int((target_amount - current_savings) / monthly_surplus) if monthly_surplus > 0 else deadline_months * 2
            insights.append(f"⏰ Рекомендуем увеличить срок до {suggested_months} месяцев для более комфортного достижения цели.")
        
        # Анализ риска
        if risk_level == 'high':
            insights.append("🎯 Высокий уровень риска. Рассмотрите: увеличение дохода, сокращение расходов или изменение параметров цели.")
        elif risk_level == 'medium':
            insights.append("📈 Средний уровень риска. Создайте подушку безопасности на непредвиденные расходы.")
        
        # Совет по дополнительному доходу
        if probability < 0.6 and avg_income > 0:
            needed_extra = recommended_savings - monthly_surplus
            if needed_extra > 0:
                insights.append(f"💰 Рассмотрите дополнительный источник дохода на {needed_extra:,.0f} ₸/месяц.")
        
        # Прогресс к цели
        progress = (current_savings / target_amount * 100) if target_amount > 0 else 0
        if progress >= 50:
            insights.append(f"🎉 Вы уже прошли {progress:.0f}% пути к цели! Не останавливайтесь!")
        elif progress < 10:
            insights.append(f"🚀 Начало пути. Важно выработать привычку регулярных накоплений.")
        
        return insights
    
    def get_goal_recommendations(
        self,
        avg_income: float,
        avg_expenses: float,
        current_savings: float
    ) -> Dict:
        """
        Получить рекомендации по постановке финансовых целей.
        
        Args:
            avg_income: Средний месячный доход
            avg_expenses: Средние месячные расходы
            current_savings: Текущие сбережения
        
        Returns:
            Рекомендации по оптимальным параметрам целей
        """
        monthly_surplus = max(0, avg_income - avg_expenses)
        savings_rate = monthly_surplus / avg_income if avg_income > 0 else 0
        
        # Рекомендуемые суммы целей на разные сроки
        recommendations = {
            'short_term': {  # 6-12 месяцев
                'suggested_amount': monthly_surplus * 9,
                'timeframe': '6-12 месяцев',
                'examples': ['Отпуск', 'Техника', 'Курсы']
            },
            'medium_term': {  # 1-3 года
                'suggested_amount': monthly_surplus * 24,
                'timeframe': '1-3 года',
                'examples': ['Автомобиль', 'Ремонт', 'Свадьба']
            },
            'long_term': {  # 3+ года
                'suggested_amount': monthly_surplus * 48,
                'timeframe': '3+ года',
                'examples': ['Квартира', 'Образование детей', 'Пенсия']
            }
        }
        
        return {
            'current_savings_rate': round(savings_rate, 3),
            'monthly_surplus': round(monthly_surplus, 2),
            'recommendations': recommendations,
            'financial_health': 'good' if savings_rate >= 0.2 else 'needs_improvement'
        }


# Глобальный инстанс предиктора
predictor = FinancialGoalPredictor()

