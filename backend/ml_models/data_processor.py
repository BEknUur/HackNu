"""
Data processor для подготовки финансовых данных пользователя.
Анализирует транзакции и счета для создания финансового профиля.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FinancialDataProcessor:
    """
    Процессор для анализа финансовых данных пользователя.
    Извлекает и обрабатывает информацию о доходах, расходах и паттернах трат.
    """
    
    @staticmethod
    def calculate_user_financial_profile(
        db: Session,
        user_id: int,
        months: int = 6
    ) -> Dict:
        """
        Анализирует финансовый профиль пользователя за последние N месяцев.
        
        Args:
            db: Database session
            user_id: ID пользователя
            months: Количество месяцев для анализа (по умолчанию 6)
        
        Returns:
            {
                'avg_monthly_income': float,
                'avg_monthly_expenses': float,
                'current_savings': float,
                'expense_volatility': float,
                'income_volatility': float,
                'transaction_count': int,
                'category_breakdown': Dict,
                'trend': str  # 'improving', 'stable', 'declining'
            }
        """
        from models.transaction import Transaction
     
        
        try:
            # Период анализа
            start_date = datetime.now() - timedelta(days=months * 30)
            
            # Получаем транзакции пользователя
            transactions = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= start_date,
                Transaction.deleted_at.is_(None)
            ).all()
            
            if not transactions:
                logger.warning(f"No transactions found for user {user_id}")
                return FinancialDataProcessor._get_default_profile(db, user_id)
            
            # Анализ доходов
            income_data = FinancialDataProcessor._analyze_income(transactions, months)
            
            # Анализ расходов
            expense_data = FinancialDataProcessor._analyze_expenses(transactions, months)
            
            # Текущие сбережения
            current_savings = FinancialDataProcessor._get_current_savings(db, user_id)
            
            # Определение тренда
            trend = FinancialDataProcessor._determine_trend(
                income_data['monthly_income_list'],
                expense_data['monthly_expense_list']
            )
            
            profile = {
                'avg_monthly_income': income_data['avg_monthly_income'],
                'avg_monthly_expenses': expense_data['avg_monthly_expenses'],
                'current_savings': current_savings,
                'expense_volatility': expense_data['volatility'],
                'income_volatility': income_data['volatility'],
                'transaction_count': len(transactions),
                'category_breakdown': expense_data['category_breakdown'],
                'trend': trend,
                'analysis_period_months': months,
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Financial profile calculated for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error calculating financial profile for user {user_id}: {e}")
            return FinancialDataProcessor._get_default_profile(db, user_id)
    
    @staticmethod
    def _analyze_income(transactions: List, months: int) -> Dict:
        """Анализ доходов."""
        # Типы транзакций, считающиеся доходом
        income_types = ['deposit']
        
        income_transactions = [
            t for t in transactions
            if t.transaction_type in income_types and float(t.amount) > 0
        ]
        
        if not income_transactions:
            return {
                'avg_monthly_income': 0.0,
                'volatility': 0.0,
                'monthly_income_list': []
            }
        
        # Группируем по месяцам
        monthly_incomes = {}
        for t in income_transactions:
            month_key = t.created_at.strftime('%Y-%m')
            if month_key not in monthly_incomes:
                monthly_incomes[month_key] = 0.0
            monthly_incomes[month_key] += float(t.amount)
        
        # Список доходов по месяцам
        monthly_income_list = list(monthly_incomes.values())
        
        # Средний месячный доход
        avg_monthly_income = sum(monthly_income_list) / max(len(monthly_income_list), 1)
        
        # Волатильность (стандартное отклонение)
        volatility = float(np.std(monthly_income_list)) if len(monthly_income_list) > 1 else 0.0
        
        return {
            'avg_monthly_income': round(avg_monthly_income, 2),
            'volatility': round(volatility, 2),
            'monthly_income_list': monthly_income_list
        }
    
    @staticmethod
    def _analyze_expenses(transactions: List, months: int) -> Dict:
        """Анализ расходов."""
        # Типы транзакций, считающиеся расходом
        expense_types = ['purchase', 'withdrawal', 'transfer']
        
        expense_transactions = [
            t for t in transactions
            if t.transaction_type in expense_types and float(t.amount) > 0
        ]
        
        if not expense_transactions:
            return {
                'avg_monthly_expenses': 0.0,
                'volatility': 0.0,
                'monthly_expense_list': [],
                'category_breakdown': {}
            }
        
        # Группируем по месяцам
        monthly_expenses = {}
        for t in expense_transactions:
            month_key = t.created_at.strftime('%Y-%m')
            if month_key not in monthly_expenses:
                monthly_expenses[month_key] = 0.0
            monthly_expenses[month_key] += float(t.amount)
        
        # Список расходов по месяцам
        monthly_expense_list = list(monthly_expenses.values())
        
        # Средние месячные расходы
        avg_monthly_expenses = sum(monthly_expense_list) / max(len(monthly_expense_list), 1)
        
        # Волатильность
        volatility = float(np.std(monthly_expense_list)) if len(monthly_expense_list) > 1 else 0.0
        
        # Разбивка по категориям (на основе типа транзакции)
        category_breakdown = {}
        for t in expense_transactions:
            category = t.transaction_type
            if category not in category_breakdown:
                category_breakdown[category] = 0.0
            category_breakdown[category] += float(t.amount)
        
        return {
            'avg_monthly_expenses': round(avg_monthly_expenses, 2),
            'volatility': round(volatility, 2),
            'monthly_expense_list': monthly_expense_list,
            'category_breakdown': category_breakdown
        }
    
    @staticmethod
    def _get_current_savings(db: Session, user_id: int) -> float:
        """Получить текущие сбережения (общий баланс всех счетов)."""
        from models.account import Account
        
        accounts = db.query(Account).filter(
            Account.user_id == user_id,
            Account.status == 'active',
            Account.deleted_at.is_(None)
        ).all()
        
        total_balance = sum(float(acc.balance) for acc in accounts)
        return round(total_balance, 2)
    
    @staticmethod
    def _determine_trend(income_list: List[float], expense_list: List[float]) -> str:
        """
        Определяет финансовый тренд пользователя.
        
        Returns:
            'improving' - доходы растут, расходы снижаются
            'stable' - без значительных изменений
            'declining' - доходы падают, расходы растут
        """
        if not income_list or not expense_list:
            return 'stable'
        
        # Берем последние 3 месяца для тренда
        recent_count = min(3, len(income_list))
        
        recent_income = income_list[-recent_count:]
        recent_expenses = expense_list[-recent_count:]
        
        # Простой линейный тренд
        income_trend = np.polyfit(range(len(recent_income)), recent_income, 1)[0] if len(recent_income) > 1 else 0
        expense_trend = np.polyfit(range(len(recent_expenses)), recent_expenses, 1)[0] if len(recent_expenses) > 1 else 0
        
        # Определяем общий тренд
        if income_trend > 0 and expense_trend <= 0:
            return 'improving'
        elif income_trend < 0 and expense_trend > 0:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def _get_default_profile(db: Session, user_id: int) -> Dict:
        """Возвращает профиль по умолчанию если нет данных."""
        current_savings = FinancialDataProcessor._get_current_savings(db, user_id)
        
        return {
            'avg_monthly_income': 0.0,
            'avg_monthly_expenses': 0.0,
            'current_savings': current_savings,
            'expense_volatility': 0.0,
            'income_volatility': 0.0,
            'transaction_count': 0,
            'category_breakdown': {},
            'trend': 'stable',
            'analysis_period_months': 0,
            'last_updated': datetime.now().isoformat()
        }
    
    @staticmethod
    def prepare_ml_features(financial_profile: Dict, goal_data: Dict) -> Dict:
        """
        Подготавливает данные для ML модели.
        
        Args:
            financial_profile: Финансовый профиль пользователя
            goal_data: Данные о цели
        
        Returns:
            Словарь с фичами для предсказания
        """
        return {
            'avg_monthly_income': financial_profile['avg_monthly_income'],
            'avg_monthly_expenses': financial_profile['avg_monthly_expenses'],
            'current_savings': financial_profile['current_savings'],
            'target_amount': float(goal_data['target_amount']),
            'deadline_months': int(goal_data['deadline_months']),
            'expense_volatility': financial_profile['expense_volatility'],
            'income_volatility': financial_profile.get('income_volatility', 0.0),
            'trend': financial_profile.get('trend', 'stable')
        }

