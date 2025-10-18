from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session
from database import get_db
from services.transaction import service
from services.transaction.schemas import (
    TransactionDeposit,
    TransactionWithdrawal,
    TransactionTransfer,
    TransactionPurchase,
    TransactionUpdate,
    TransactionRead,
    TransactionHistoryFilter,
    TransactionStats
)
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/deposit", response_model=TransactionRead, status_code=201)
def create_deposit(
    deposit_data: TransactionDeposit,
    user_id: int = Query(..., gt=0, description="User ID performing the deposit"),
    db: Session = Depends(get_db)
):
    """
    Create a deposit transaction.
    
    Adds funds to the specified account.
    
    **Required fields:**
    - account_id: Account to deposit to
    - amount: Amount to deposit (must be positive)
    - currency: Currency code
    
    **Optional fields:**
    - description: Transaction description
    """
    return service.create_deposit(deposit_data, user_id, db)


@router.post("/withdrawal", response_model=TransactionRead, status_code=201)
def create_withdrawal(
    withdrawal_data: TransactionWithdrawal,
    user_id: int = Query(..., gt=0, description="User ID performing the withdrawal"),
    db: Session = Depends(get_db)
):
    """
    Create a withdrawal transaction.
    
    Removes funds from the specified account.
    
    **Required fields:**
    - account_id: Account to withdraw from
    - amount: Amount to withdraw (must be positive)
    - currency: Currency code
    
    **Optional fields:**
    - description: Transaction description
    
    **Note:** Account must have sufficient funds.
    """
    return service.create_withdrawal(withdrawal_data, user_id, db)


@router.post("/transfer", response_model=TransactionRead, status_code=201)
def create_transfer(
    transfer_data: TransactionTransfer,
    user_id: int = Query(..., gt=0, description="User ID performing the transfer"),
    db: Session = Depends(get_db)
):
    """
    Create a transfer between two accounts.
    
    Transfers funds from source account to destination account.
    
    **Required fields:**
    - from_account_id: Source account ID
    - to_account_id: Destination account ID
    - amount: Amount to transfer (must be positive)
    - currency: Currency code
    
    **Optional fields:**
    - description: Transaction description
    
    **Note:** Both accounts must use the same currency and source account must have sufficient funds.
    """
    return service.create_transfer(transfer_data, user_id, db)


@router.post("/purchase", response_model=TransactionRead, status_code=201)
def create_purchase(
    purchase_data: TransactionPurchase,
    user_id: int = Query(..., gt=0, description="User ID making the purchase"),
    db: Session = Depends(get_db)
):
    """
    Create a purchase transaction.
    
    Purchases a product using the specified account.
    
    **Required fields:**
    - account_id: Account to charge from
    - product_id: Product to purchase
    - amount: Amount (will be calculated from product price * quantity)
    - currency: Currency code
    
    **Optional fields:**
    - quantity: Quantity of product (default: 1)
    - description: Transaction description
    
    **Note:** Account must have sufficient funds and currency must match product currency.
    """
    return service.create_purchase(purchase_data, user_id, db)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int = Path(..., gt=0, description="Transaction ID"),
    db: Session = Depends(get_db)
):
    """
    Get transaction details by ID.
    """
    return service.get_transaction(transaction_id, db)


@router.get("/user/{user_id}", response_model=List[TransactionRead])
def get_user_transactions(
    user_id: int = Path(..., gt=0, description="User ID"),
    account_id: Optional[int] = Query(None, gt=0, description="Filter by account ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum amount"),
    date_from: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO format)"),
    include_deleted: bool = Query(False, description="Include deleted transactions"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all transactions for a specific user with optional filters.
    
    **Query parameters:**
    - account_id: Filter by specific account
    - transaction_type: Filter by type ('deposit', 'withdrawal', 'transfer', 'purchase')
    - min_amount: Minimum transaction amount
    - max_amount: Maximum transaction amount
    - date_from: Start date for filtering
    - date_to: End date for filtering
    - include_deleted: Include soft-deleted transactions
    - skip: Pagination offset
    - limit: Maximum results to return
    
    Returns transactions where user is either sender or receiver (for transfers).
    """
    from decimal import Decimal
    
    # Build filters
    filters = TransactionHistoryFilter(
        account_id=account_id,
        transaction_type=transaction_type,
        min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
        max_amount=Decimal(str(max_amount)) if max_amount is not None else None,
        date_from=date_from,
        date_to=date_to
    )
    
    return service.get_user_transactions(user_id, db, filters, include_deleted, skip, limit)


@router.get("/account/{account_id}/history", response_model=List[TransactionRead])
def get_account_transactions(
    account_id: int = Path(..., gt=0, description="Account ID"),
    user_id: int = Query(..., gt=0, description="User ID (for permission check)"),
    include_deleted: bool = Query(False, description="Include deleted transactions"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for a specific account.
    
    **Query parameters:**
    - user_id: User ID for permission verification
    - include_deleted: Include soft-deleted transactions
    - skip: Pagination offset
    - limit: Maximum results to return
    
    Returns transactions where the account is either source or destination.
    """
    return service.get_account_transactions(account_id, user_id, db, include_deleted, skip, limit)


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int = Path(..., gt=0, description="Transaction ID"),
    user_id: int = Query(..., gt=0, description="User ID (for permission check)"),
    transaction_data: TransactionUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update transaction description.
    
    Only the description field can be updated. Transaction amounts and types are immutable
    for audit and accounting purposes.
    
    **Query parameters:**
    - user_id: User ID for permission verification (must own the transaction)
    """
    return service.update_transaction(transaction_id, user_id, transaction_data, db)


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int = Path(..., gt=0, description="Transaction ID"),
    user_id: int = Query(..., gt=0, description="User ID (for permission check)"),
    db: Session = Depends(get_db)
):
    """
    Soft delete a transaction.
    
    Transactions are always soft-deleted (not permanently removed) for audit purposes.
    The transaction will be marked as deleted but retained in the database.
    
    **Query parameters:**
    - user_id: User ID for permission verification (must own the transaction)
    """
    return service.delete_transaction(transaction_id, user_id, db)


@router.get("/user/{user_id}/stats", response_model=TransactionStats)
def get_user_transaction_stats(
    user_id: int = Path(..., gt=0, description="User ID"),
    currency: str = Query(..., description="Currency code for statistics"),
    date_from: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get transaction statistics for a user.
    
    Returns aggregated statistics including:
    - Total number of transactions
    - Total deposits
    - Total withdrawals
    - Total transfers sent
    - Total transfers received
    - Total purchases
    
    **Query parameters:**
    - currency: Currency to calculate stats for (required)
    - date_from: Start date for statistics period
    - date_to: End date for statistics period
    """
    return service.get_user_transaction_stats(user_id, currency, db, date_from, date_to)

