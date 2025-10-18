from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database import get_db
from models.transaction import Transaction
from models.account import Account
from models.user import User
from models.product import Product
from services.transaction.schemas import (
    TransactionRead,
    TransactionDeposit,
    TransactionWithdrawal,
    TransactionTransfer,
    TransactionPurchase,
    TransactionUpdate,
    TransactionHistoryFilter,
    TransactionStats
)
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


def get_transaction_by_id(
    transaction_id: int, 
    db: Session, 
    include_deleted: bool = False
) -> Transaction:
    """
    Get transaction by ID with optional deleted filter
    
    Args:
        transaction_id: Transaction ID
        db: Database session
        include_deleted: Whether to include deleted transactions
        
    Returns:
        Transaction object
        
    Raises:
        HTTPException: If transaction not found
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if not include_deleted and transaction.deleted_at:
        raise HTTPException(status_code=404, detail="Transaction is deleted")
    
    return transaction


def verify_account_exists_and_active(account_id: int, db: Session) -> Account:
    """
    Verify that account exists, is not deleted, and is active
    
    Args:
        account_id: Account ID
        db: Database session
        
    Returns:
        Account object
        
    Raises:
        HTTPException: If account not found, deleted, or not active
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    if account.deleted_at:
        raise HTTPException(status_code=404, detail=f"Account {account_id} is deleted")
    
    if account.status != 'active':
        raise HTTPException(
            status_code=400,
            detail=f"Account {account_id} is {account.status}. Only active accounts can perform transactions"
        )
    
    return account


def verify_product_exists_and_active(product_id: int, db: Session) -> Product:
    """
    Verify that product exists and is active
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Product object
        
    Raises:
        HTTPException: If product not found or not active
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    if product.deleted_at:
        raise HTTPException(status_code=404, detail=f"Product {product_id} is deleted")
    
    if product.is_active != 'active':
        raise HTTPException(status_code=400, detail=f"Product {product_id} is not active")
    
    return product


def create_deposit(
    deposit_data: TransactionDeposit,
    user_id: int,
    db: Session = Depends(get_db)
) -> TransactionRead:
    """
    Create a deposit transaction
    
    Args:
        deposit_data: Deposit transaction data
        user_id: User ID performing the deposit
        db: Database session
        
    Returns:
        Created transaction data
        
    Raises:
        HTTPException: If validation fails
    """
    # Verify account
    account = verify_account_exists_and_active(deposit_data.account_id, db)
    
    # Verify user owns the account
    if account.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this account")
    
    # Verify currency matches
    if account.currency != deposit_data.currency:
        raise HTTPException(
            status_code=400,
            detail=f"Currency mismatch. Account uses {account.currency}, transaction uses {deposit_data.currency}"
        )
    
    # Update account balance
    account.balance += deposit_data.amount
    account.updated_at = datetime.now()
    
    # Create transaction
    new_transaction = Transaction(
        user_id=user_id,
        account_id=deposit_data.account_id,
        amount=deposit_data.amount,
        currency=deposit_data.currency,
        transaction_type='deposit',
        description=deposit_data.description or f"Deposit to account {deposit_data.account_id}"
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return TransactionRead.from_orm(new_transaction)


def create_withdrawal(
    withdrawal_data: TransactionWithdrawal,
    user_id: int,
    db: Session = Depends(get_db)
) -> TransactionRead:
    """
    Create a withdrawal transaction
    
    Args:
        withdrawal_data: Withdrawal transaction data
        user_id: User ID performing the withdrawal
        db: Database session
        
    Returns:
        Created transaction data
        
    Raises:
        HTTPException: If validation fails or insufficient funds
    """
    # Verify account
    account = verify_account_exists_and_active(withdrawal_data.account_id, db)
    
    # Verify user owns the account
    if account.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this account")
    
    # Verify currency matches
    if account.currency != withdrawal_data.currency:
        raise HTTPException(
            status_code=400,
            detail=f"Currency mismatch. Account uses {account.currency}, transaction uses {withdrawal_data.currency}"
        )
    
    # Check sufficient funds
    if account.balance < withdrawal_data.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Current balance: {account.balance} {account.currency}"
        )
    
    # Update account balance
    account.balance -= withdrawal_data.amount
    account.updated_at = datetime.now()
    
    # Create transaction
    new_transaction = Transaction(
        user_id=user_id,
        account_id=withdrawal_data.account_id,
        amount=withdrawal_data.amount,
        currency=withdrawal_data.currency,
        transaction_type='withdrawal',
        description=withdrawal_data.description or f"Withdrawal from account {withdrawal_data.account_id}"
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return TransactionRead.from_orm(new_transaction)


def create_transfer(
    transfer_data: TransactionTransfer,
    user_id: int,
    db: Session = Depends(get_db)
) -> TransactionRead:
    """
    Create a transfer between accounts
    
    Args:
        transfer_data: Transfer transaction data
        user_id: User ID performing the transfer
        db: Database session
        
    Returns:
        Created transaction data
        
    Raises:
        HTTPException: If validation fails or insufficient funds
    """
    # Verify both accounts
    from_account = verify_account_exists_and_active(transfer_data.from_account_id, db)
    to_account = verify_account_exists_and_active(transfer_data.to_account_id, db)
    
    # Verify user owns the source account
    if from_account.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own the source account")
    
    # Verify currency matches
    if from_account.currency != transfer_data.currency:
        raise HTTPException(
            status_code=400,
            detail=f"Currency mismatch. Source account uses {from_account.currency}"
        )
    
    if to_account.currency != transfer_data.currency:
        raise HTTPException(
            status_code=400,
            detail=f"Currency mismatch. Destination account uses {to_account.currency}"
        )
    
    # Check sufficient funds
    if from_account.balance < transfer_data.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Current balance: {from_account.balance} {from_account.currency}"
        )
    
    # Update account balances
    from_account.balance -= transfer_data.amount
    from_account.updated_at = datetime.now()
    
    to_account.balance += transfer_data.amount
    to_account.updated_at = datetime.now()
    
    # Create transaction
    new_transaction = Transaction(
        user_id=user_id,
        account_id=transfer_data.from_account_id,
        amount=transfer_data.amount,
        currency=transfer_data.currency,
        transaction_type='transfer',
        description=transfer_data.description or f"Transfer to account {transfer_data.to_account_id}",
        to_user_id=to_account.user_id,
        to_account_id=transfer_data.to_account_id
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return TransactionRead.from_orm(new_transaction)


def create_purchase(
    purchase_data: TransactionPurchase,
    user_id: int,
    db: Session = Depends(get_db)
) -> TransactionRead:
    """
    Create a purchase transaction
    
    Args:
        purchase_data: Purchase transaction data
        user_id: User ID performing the purchase
        db: Database session
        
    Returns:
        Created transaction data
        
    Raises:
        HTTPException: If validation fails or insufficient funds
    """
    # Verify account
    account = verify_account_exists_and_active(purchase_data.account_id, db)
    
    # Verify user owns the account
    if account.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this account")
    
    # Verify product
    product = verify_product_exists_and_active(purchase_data.product_id, db)
    
    # Calculate total amount
    total_amount = product.price * purchase_data.quantity
    
    # Verify currency matches
    if account.currency != product.currency:
        raise HTTPException(
            status_code=400,
            detail=f"Currency mismatch. Account uses {account.currency}, product uses {product.currency}"
        )
    
    # Override amount with calculated total
    actual_amount = total_amount
    
    # Check sufficient funds
    if account.balance < actual_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Required: {actual_amount} {account.currency}, Current balance: {account.balance} {account.currency}"
        )
    
    # Update account balance
    account.balance -= actual_amount
    account.updated_at = datetime.now()
    
    # Create transaction
    new_transaction = Transaction(
        user_id=user_id,
        account_id=purchase_data.account_id,
        amount=actual_amount,
        currency=account.currency,
        transaction_type='purchase',
        description=purchase_data.description or f"Purchase of {product.title} (x{purchase_data.quantity})",
        product_id=purchase_data.product_id
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return TransactionRead.from_orm(new_transaction)


def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
) -> TransactionRead:
    """
    Get transaction by ID
    
    Args:
        transaction_id: Transaction ID
        db: Database session
        
    Returns:
        Transaction data
        
    Raises:
        HTTPException: If transaction not found
    """
    transaction = get_transaction_by_id(transaction_id, db)
    return TransactionRead.from_orm(transaction)


def get_user_transactions(
    user_id: int,
    db: Session = Depends(get_db),
    filters: Optional[TransactionHistoryFilter] = None,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[TransactionRead]:
    """
    Get all transactions for a specific user with filters
    
    Args:
        user_id: User ID
        db: Database session
        filters: Optional filters for transactions
        include_deleted: Whether to include deleted transactions
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of user's transactions
    """
    # Build base query - include transactions where user is sender or receiver
    query = db.query(Transaction).filter(
        or_(
            Transaction.user_id == user_id,
            Transaction.to_user_id == user_id
        )
    )
    
    if not include_deleted:
        query = query.filter(Transaction.deleted_at.is_(None))
    
    # Apply filters if provided
    if filters:
        if filters.account_id:
            query = query.filter(
                or_(
                    Transaction.account_id == filters.account_id,
                    Transaction.to_account_id == filters.account_id
                )
            )
        
        if filters.transaction_type:
            query = query.filter(Transaction.transaction_type == filters.transaction_type)
        
        if filters.min_amount:
            query = query.filter(Transaction.amount >= filters.min_amount)
        
        if filters.max_amount:
            query = query.filter(Transaction.amount <= filters.max_amount)
        
        if filters.date_from:
            query = query.filter(Transaction.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Transaction.created_at <= filters.date_to)
    
    # Order by most recent first
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return [TransactionRead.from_orm(transaction) for transaction in transactions]


def get_account_transactions(
    account_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[TransactionRead]:
    """
    Get all transactions for a specific account
    
    Args:
        account_id: Account ID
        user_id: User ID (for permission check)
        db: Database session
        include_deleted: Whether to include deleted transactions
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of account's transactions
        
    Raises:
        HTTPException: If account not found or user doesn't own it
    """
    # Verify account and ownership
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this account")
    
    # Build query - include transactions where account is source or destination
    query = db.query(Transaction).filter(
        or_(
            Transaction.account_id == account_id,
            Transaction.to_account_id == account_id
        )
    )
    
    if not include_deleted:
        query = query.filter(Transaction.deleted_at.is_(None))
    
    # Order by most recent first
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return [TransactionRead.from_orm(transaction) for transaction in transactions]


def update_transaction(
    transaction_id: int,
    user_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db)
) -> TransactionRead:
    """
    Update transaction (only description can be updated)
    
    Args:
        transaction_id: Transaction ID
        user_id: User ID (for permission check)
        transaction_data: Updated transaction data
        db: Database session
        
    Returns:
        Updated transaction data
        
    Raises:
        HTTPException: If transaction not found or user doesn't own it
    """
    transaction = get_transaction_by_id(transaction_id, db)
    
    # Verify user owns the transaction
    if transaction.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this transaction")
    
    # Update only description
    if transaction_data.description is not None:
        transaction.description = transaction_data.description
    
    transaction.updated_at = datetime.now()
    
    db.commit()
    db.refresh(transaction)
    
    return TransactionRead.from_orm(transaction)


def delete_transaction(
    transaction_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    soft_delete: bool = True
) -> dict:
    """
    Delete transaction (soft delete only for audit purposes)
    
    Args:
        transaction_id: Transaction ID
        user_id: User ID (for permission check)
        db: Database session
        soft_delete: Always True for transactions (audit requirement)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If transaction not found or user doesn't own it
    """
    transaction = get_transaction_by_id(transaction_id, db)
    
    # Verify user owns the transaction
    if transaction.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this transaction")
    
    # Always soft delete for audit purposes
    transaction.deleted_at = datetime.now()
    db.commit()
    
    return {"message": "Transaction marked as deleted (soft delete for audit purposes)"}


def get_user_transaction_stats(
    user_id: int,
    currency: str,
    db: Session = Depends(get_db),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> TransactionStats:
    """
    Get transaction statistics for a user
    
    Args:
        user_id: User ID
        currency: Currency to calculate stats for
        db: Database session
        date_from: Start date for stats
        date_to: End date for stats
        
    Returns:
        Transaction statistics
    """
    # Build base query
    query = db.query(Transaction).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.currency == currency,
            Transaction.deleted_at.is_(None)
        )
    )
    
    # Apply date filters
    if date_from:
        query = query.filter(Transaction.created_at >= date_from)
    
    if date_to:
        query = query.filter(Transaction.created_at <= date_to)
    
    transactions = query.all()
    
    # Calculate stats
    total_transactions = len(transactions)
    total_deposits = sum(t.amount for t in transactions if t.transaction_type == 'deposit')
    total_withdrawals = sum(t.amount for t in transactions if t.transaction_type == 'withdrawal')
    total_transfers_sent = sum(t.amount for t in transactions if t.transaction_type == 'transfer')
    total_purchases = sum(t.amount for t in transactions if t.transaction_type == 'purchase')
    
    # Calculate received transfers
    received_query = db.query(Transaction).filter(
        and_(
            Transaction.to_user_id == user_id,
            Transaction.transaction_type == 'transfer',
            Transaction.currency == currency,
            Transaction.deleted_at.is_(None)
        )
    )
    
    if date_from:
        received_query = received_query.filter(Transaction.created_at >= date_from)
    
    if date_to:
        received_query = received_query.filter(Transaction.created_at <= date_to)
    
    total_transfers_received = sum(t.amount for t in received_query.all())
    
    return TransactionStats(
        total_transactions=total_transactions,
        total_deposits=Decimal(str(total_deposits)),
        total_withdrawals=Decimal(str(total_withdrawals)),
        total_transfers_sent=Decimal(str(total_transfers_sent)),
        total_transfers_received=Decimal(str(total_transfers_received)),
        total_purchases=Decimal(str(total_purchases)),
        currency=currency
    )

