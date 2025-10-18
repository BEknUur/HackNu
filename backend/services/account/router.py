from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from database import get_db
from services.account import service
from services.account.schemas import (
    AccountCreate,
    AccountUpdate,
    AccountRead,
    AccountBalanceUpdate
)
from typing import List

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountRead, status_code=201)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new account for a user.
    
    **Required fields:**
    - user_id: ID of the user who owns the account
    - account_type: Type of account ('checking', 'savings', 'credit')
    
    **Optional fields:**
    - balance: Initial balance (default: 0.00)
    - currency: Currency code (default: 'USD')
    """
    return service.create_account(account_data, db)


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: int = Path(..., gt=0, description="Account ID"),
    db: Session = Depends(get_db)
):
    """
    Get account details by ID.
    """
    return service.get_account(account_id, db)


@router.get("/user/{user_id}", response_model=List[AccountRead])
def get_user_accounts(
    user_id: int = Path(..., gt=0, description="User ID"),
    include_deleted: bool = Query(False, description="Include deleted accounts"),
    db: Session = Depends(get_db)
):
    """
    Get all accounts for a specific user.
    
    **Query parameters:**
    - include_deleted: Whether to include soft-deleted accounts (default: False)
    """
    return service.get_user_accounts(user_id, db, include_deleted)


@router.get("/", response_model=List[AccountRead])
def get_all_accounts(
    include_deleted: bool = Query(False, description="Include deleted accounts"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all accounts with pagination.
    
    **Query parameters:**
    - include_deleted: Whether to include soft-deleted accounts (default: False)
    - skip: Number of records to skip for pagination (default: 0)
    - limit: Maximum number of records to return (default: 100, max: 1000)
    """
    return service.get_all_accounts(db, include_deleted, skip, limit)


@router.put("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int = Path(..., gt=0, description="Account ID"),
    account_data: AccountUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Update account information.
    
    **Updatable fields:**
    - account_type: Type of account
    - balance: Account balance (use balance operations for deposits/withdrawals)
    - currency: Currency code
    - status: Account status ('active', 'blocked', 'closed')
    
    All fields are optional - only provided fields will be updated.
    """
    return service.update_account(account_id, account_data, db)




@router.delete("/{account_id}")
def delete_account(
    account_id: int = Path(..., gt=0, description="Account ID"),
    soft_delete: bool = Query(True, description="Soft delete (True) or hard delete (False)"),
    db: Session = Depends(get_db)
):
    """
    Delete an account.
    
    **Query parameters:**
    - soft_delete: If True, marks account as deleted; if False, permanently removes it (default: True)
    
    **Note:** Account balance must be zero before deletion.
    """
    return service.delete_account(account_id, db, soft_delete)


@router.post("/{account_id}/restore", response_model=AccountRead)
def restore_account(
    account_id: int = Path(..., gt=0, description="Account ID"),
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted account.
    
    Sets the account status back to 'active' and clears the deleted_at timestamp.
    """
    return service.restore_account(account_id, db)


@router.post("/{account_id}/block", response_model=AccountRead)
def block_account(
    account_id: int = Path(..., gt=0, description="Account ID"),
    db: Session = Depends(get_db)
):
    """
    Block an account.
    
    Blocked accounts cannot perform transactions.
    """
    return service.block_account(account_id, db)


@router.post("/{account_id}/unblock", response_model=AccountRead)
def unblock_account(
    account_id: int = Path(..., gt=0, description="Account ID"),
    db: Session = Depends(get_db)
):
    """
    Unblock an account.
    
    Sets the account status back to 'active'.
    """
    return service.unblock_account(account_id, db)

