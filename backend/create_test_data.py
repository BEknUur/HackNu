"""
Create test data for Financial Assistant

This script creates a test user with accounts, transactions, and financial goals.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from database import SessionLocal
from models.user import User
from models.account import Account
from models.transaction import Transaction
from models.financial_goal import FinancialGoal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_test_user(db):
    """Create a test user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == "test@zamanbank.kz").first()
    if existing_user:
        print(f"✓ User already exists: {existing_user.name} {existing_user.surname} (ID: {existing_user.id})")
        return existing_user
    
    user = User(
        name="Arman",
        surname="Suleimenov",
        email="test@zamanbank.kz",
        phone="+77011234567",
        password_hash=pwd_context.hash("test123"),
        created_at=datetime.now() - timedelta(days=365)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✓ Created user: {user.name} {user.surname} (ID: {user.id})")
    return user


def create_test_accounts(db, user_id):
    """Create test accounts."""
    # Check if accounts already exist
    existing_accounts = db.query(Account).filter(Account.user_id == user_id).all()
    if existing_accounts:
        print(f"✓ Accounts already exist: {len(existing_accounts)} accounts")
        return existing_accounts
    
    accounts = [
        Account(
            user_id=user_id,
            account_type="checking",
            balance=Decimal("450000.00"),
            currency="KZT",
            status="active",
            created_at=datetime.now() - timedelta(days=300)
        ),
        Account(
            user_id=user_id,
            account_type="savings",
            balance=Decimal("850000.00"),
            currency="KZT",
            status="active",
            created_at=datetime.now() - timedelta(days=200)
        ),
        Account(
            user_id=user_id,
            account_type="checking",
            balance=Decimal("2500.00"),
            currency="USD",
            status="active",
            created_at=datetime.now() - timedelta(days=150)
        )
    ]
    
    for account in accounts:
        db.add(account)
    
    db.commit()
    for account in accounts:
        db.refresh(account)
    
    print(f"✓ Created {len(accounts)} accounts")
    return accounts


def create_test_transactions(db, user_id, accounts):
    """Create test transactions for the last 6 months."""
    # Check if transactions already exist
    existing_txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    if existing_txns:
        print(f"✓ Transactions already exist: {len(existing_txns)} transactions")
        return existing_txns
    
    checking_account = next(acc for acc in accounts if acc.account_type == "checking" and acc.currency == "KZT")
    savings_account = next(acc for acc in accounts if acc.account_type == "savings")
    
    transactions = []
    
    # Generate monthly income (salary deposits)
    for i in range(6):
        date = datetime.now() - timedelta(days=30*i + 1)
        txn = Transaction(
            user_id=user_id,
            account_id=checking_account.id,
            amount=Decimal("450000.00"),
            currency="KZT",
            transaction_type="deposit",
            description=f"Salary - Month {i+1}",
            created_at=date
        )
        transactions.append(txn)
    
    # Generate various expenses
    expense_categories = [
        ("purchase", "Grocery shopping", 45000),
        ("purchase", "Restaurant", 25000),
        ("purchase", "Online shopping", 35000),
        ("purchase", "Gas station", 20000),
        ("purchase", "Utilities payment", 15000),
        ("withdrawal", "ATM withdrawal", 30000),
        ("transfer", "Transfer to savings", 80000),
        ("purchase", "Pharmacy", 8000),
        ("purchase", "Cinema tickets", 6000),
        ("purchase", "Coffee shop", 3500),
    ]
    
    for month in range(6):
        for txn_type, desc, base_amount in expense_categories:
            date = datetime.now() - timedelta(days=30*month + (hash(desc) % 28) + 1)
            # Add some variation to amounts
            amount = base_amount * (0.8 + (hash(desc + str(month)) % 40) / 100)
            
            txn = Transaction(
                user_id=user_id,
                account_id=checking_account.id,
                amount=Decimal(str(amount)),
                currency="KZT",
                transaction_type=txn_type,
                description=desc,
                created_at=date
            )
            transactions.append(txn)
    
    # Add transfers to savings
    for i in range(6):
        date = datetime.now() - timedelta(days=30*i + 15)
        txn = Transaction(
            user_id=user_id,
            account_id=savings_account.id,
            amount=Decimal("80000.00"),
            currency="KZT",
            transaction_type="deposit",
            description="Monthly savings",
            created_at=date
        )
        transactions.append(txn)
    
    for txn in transactions:
        db.add(txn)
    
    db.commit()
    print(f"✓ Created {len(transactions)} transactions")
    return transactions


def create_test_financial_goals(db, user_id):
    """Create test financial goals."""
    # Check if goals already exist
    existing_goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id).all()
    if existing_goals:
        print(f"✓ Financial goals already exist: {len(existing_goals)} goals")
        return existing_goals
    
    goals = [
        FinancialGoal(
            user_id=user_id,
            goal_name="Emergency Fund",
            goal_type="emergency",
            target_amount=Decimal("2000000.00"),
            current_savings=Decimal("850000.00"),
            deadline_months=18,
            currency="KZT",
            predicted_probability=0.75,
            recommended_monthly_savings=Decimal("65000.00"),
            risk_level="medium",
            ai_insights='{"insights": ["You are 42.5% towards your emergency fund goal"]}',
            status="active",
            created_at=datetime.now() - timedelta(days=120)
        ),
        FinancialGoal(
            user_id=user_id,
            goal_name="New Car",
            goal_type="other",
            target_amount=Decimal("8000000.00"),
            current_savings=Decimal("1200000.00"),
            deadline_months=36,
            currency="KZT",
            predicted_probability=0.68,
            recommended_monthly_savings=Decimal("190000.00"),
            risk_level="medium",
            ai_insights='{"insights": ["Saving for a new car requires consistent monthly contributions"]}',
            status="active",
            created_at=datetime.now() - timedelta(days=60)
        ),
        FinancialGoal(
            user_id=user_id,
            goal_name="Vacation to Turkey",
            goal_type="travel",
            target_amount=Decimal("500000.00"),
            current_savings=Decimal("450000.00"),
            deadline_months=3,
            currency="KZT",
            predicted_probability=0.92,
            recommended_monthly_savings=Decimal("20000.00"),
            risk_level="low",
            ai_insights='{"insights": ["You are almost there! Just 3 more months"]}',
            status="active",
            created_at=datetime.now() - timedelta(days=150)
        )
    ]
    
    for goal in goals:
        db.add(goal)
    
    db.commit()
    print(f"✓ Created {len(goals)} financial goals")
    return goals


def main():
    """Main function to create all test data."""
    print("\n" + "="*80)
    print("Creating Test Data for Financial Assistant")
    print("="*80 + "\n")
    
    db = SessionLocal()
    
    try:
        # Create test user
        user = create_test_user(db)
        
        # Create accounts
        accounts = create_test_accounts(db, user.id)
        
        # Create transactions
        transactions = create_test_transactions(db, user.id, accounts)
        
        # Create financial goals
        goals = create_test_financial_goals(db, user.id)
        
        print("\n" + "="*80)
        print("✅ Test Data Creation Complete!")
        print("="*80)
        print(f"\nTest User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Password: test123")
        print(f"\nAccounts: {len(accounts)}")
        print(f"Transactions: {len(transactions)}")
        print(f"Financial Goals: {len(goals)}")
        print("\nYou can now test the Financial Assistant with user ID:", user.id)
        print("="*80 + "\n")
        
        return user.id
        
    except Exception as e:
        print(f"\n✗ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    main()

