from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.account import Account
from models.user import User
from services.account.schemas import AccountRead, AccountCreate, AccountUpdate, AccountBalanceUpdate
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


def get_account_by_id(account_id: int, db: Session, include_deleted: bool = False) -> Account:
    """
    Get account by ID with optional deleted filter
    
    Args:
        account_id: Account ID
        db: Database session
        include_deleted: Whether to include deleted accounts
        
    Returns:
        Account object
        
    Raises:
        HTTPException: If account not found
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if not include_deleted and account.deleted_at:
        raise HTTPException(status_code=404, detail="Account is deleted")
    
    return account


def verify_user_exists(user_id: int, db: Session) -> User:
    """
    Verify that user exists and is not deleted
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user not found or deleted
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.deleted_at:
        raise HTTPException(status_code=404, detail="User is deleted")
    
    return user


def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db)
) -> AccountRead:
    """
    Create a new account for a user
    
    Args:
        account_data: Account creation data
        db: Database session
        
    Returns:
        Created account data
        
    Raises:
        HTTPException: If user not found or validation fails
    """
    # Verify user exists
    verify_user_exists(account_data.user_id, db)
    
    # Create new account
    new_account = Account(
        user_id=account_data.user_id,
        account_type=account_data.account_type,
        balance=account_data.balance or Decimal('0.00'),
        currency=account_data.currency,
        status='active'
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return AccountRead.from_orm(new_account)


def get_account(
    account_id: int,
    db: Session = Depends(get_db)
) -> AccountRead:
    """
    Get account by ID
    
    Args:
        account_id: Account ID
        db: Database session
        
    Returns:
        Account data
        
    Raises:
        HTTPException: If account not found
    """
    account = get_account_by_id(account_id, db)
    return AccountRead.from_orm(account)


def get_user_accounts(
    user_id: int,
    db: Session = Depends(get_db),
    include_deleted: bool = False
) -> List[AccountRead]:
    """
    Get all accounts for a specific user
    
    Args:
        user_id: User ID
        db: Database session
        include_deleted: Whether to include deleted accounts
        
    Returns:
        List of user's accounts
        
    Raises:
        HTTPException: If user not found
    """
    # Verify user exists
    verify_user_exists(user_id, db)
    
    # Build query
    query = db.query(Account).filter(Account.user_id == user_id)
    
    if not include_deleted:
        query = query.filter(Account.deleted_at.is_(None))
    
    accounts = query.all()
    
    return [AccountRead.from_orm(account) for account in accounts]


def get_all_accounts(
    db: Session = Depends(get_db),
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[AccountRead]:
    """
    Get all accounts with pagination
    
    Args:
        db: Database session
        include_deleted: Whether to include deleted accounts
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of accounts
    """
    query = db.query(Account)
    
    if not include_deleted:
        query = query.filter(Account.deleted_at.is_(None))
    
    accounts = query.offset(skip).limit(limit).all()
    
    return [AccountRead.from_orm(account) for account in accounts]


def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db)
) -> AccountRead:
    """
    Update account information
    
    Args:
        account_id: Account ID
        account_data: Updated account data
        db: Database session
        
    Returns:
        Updated account data
        
    Raises:
        HTTPException: If account not found
    """
    account = get_account_by_id(account_id, db)
    
    # Update only provided fields
    update_data = account_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(account, field, value)
    
    account.updated_at = datetime.now()
    
    db.commit()
    db.refresh(account)
    
    return AccountRead.from_orm(account)


def update_account_balance(
    account_id: int,
    balance_data: AccountBalanceUpdate,
    db: Session = Depends(get_db)
) -> AccountRead:
    """
    Update account balance (deposit or withdraw)
    
    Args:
        account_id: Account ID
        balance_data: Balance update data (amount and operation)
        db: Database session
        
    Returns:
        Updated account data
        
    Raises:
        HTTPException: If account not found, insufficient funds, or account is not active
    """
    account = get_account_by_id(account_id, db)
    
    # Check if account is active
    if account.status != 'active':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot perform operation on {account.status} account"
        )
    
    # Perform operation
    if balance_data.operation == 'deposit':
        account.balance += balance_data.amount
    elif balance_data.operation == 'withdraw':
        if account.balance < balance_data.amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient funds. Current balance: {account.balance}"
            )
        account.balance -= balance_data.amount
    
    account.updated_at = datetime.now()
    
    db.commit()
    db.refresh(account)
    
    return AccountRead.from_orm(account)


def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    soft_delete: bool = True
) -> dict:
    """
    Delete account (soft or hard delete)
    
    Args:
        account_id: Account ID
        db: Database session
        soft_delete: If True, marks account as deleted; if False, removes from database
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If account not found or has non-zero balance
    """
    account = get_account_by_id(account_id, db)
    
    # Check if account has balance
    if account.balance != Decimal('0.00'):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete account with non-zero balance: {account.balance} {account.currency}"
        )
    
    if soft_delete:
        # Soft delete: mark as deleted
        account.deleted_at = datetime.now()
        account.status = 'closed'
        db.commit()
        return {"message": "Account soft deleted successfully"}
    else:
        # Hard delete: remove from database
        db.delete(account)
        db.commit()
        return {"message": "Account permanently deleted"}


def restore_account(
    account_id: int,
    db: Session = Depends(get_db)
) -> AccountRead:
    """
    Restore a soft-deleted account
    
    Args:
        account_id: Account ID
        db: Database session
        
    Returns:
        Restored account data
        
    Raises:
        HTTPException: If account not found or not deleted
    """
    account = get_account_by_id(account_id, db, include_deleted=True)
    
    if not account.deleted_at:
        raise HTTPException(status_code=400, detail="Account is not deleted")
    
    # Restore account
    account.deleted_at = None
    account.status = 'active'
    account.updated_at = datetime.now()
    
    db.commit()
    db.refresh(account)
    
    return AccountRead.from_orm(account)


def block_account(
    account_id: int,
    db: Session = Depends(get_db)
) -> AccountRead:
    """
    Block an account
    
    Args:
        account_id: Account ID
        db: Database session
        
    Returns:
        Updated account data
        
    Raises:
        HTTPException: If account not found
    """
    account = get_account_by_id(account_id, db)
    
    if account.status == 'blocked':
        raise HTTPException(status_code=400, detail="Account is already blocked")
    
    account.status = 'blocked'
    account.updated_at = datetime.now()
    
    db.commit()
    db.refresh(account)
    
    return AccountRead.from_orm(account)


def unblock_account(
    account_id: int,
    db: Session = Depends(get_db)
) -> AccountRead:
    """
    Unblock an account
    
    Args:
        account_id: Account ID
        db: Database session
        
    Returns:
        Updated account data
        
    Raises:
        HTTPException: If account not found
    """
    account = get_account_by_id(account_id, db)
    
    if account.status != 'blocked':
        raise HTTPException(status_code=400, detail="Account is not blocked")
    
    account.status = 'active'
    account.updated_at = datetime.now()
    
    db.commit()
    db.refresh(account)
    
    return AccountRead.from_orm(account)

