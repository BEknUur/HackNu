#!/usr/bin/env python3
"""
Add Default Accounts to Existing Users

This script finds users without accounts and creates a default checking account for them.
Run this to fix existing users who were created before the auto-account-creation feature.
"""

from database import SessionLocal
from models.user import User
from models.account import Account
from decimal import Decimal
from datetime import datetime


def add_accounts_to_users():
    """Add default accounts to users who don't have any."""
    print("\n" + "="*80)
    print("Adding Default Accounts to Existing Users")
    print("="*80 + "\n")
    
    db = SessionLocal()
    
    try:
        # Get all active users
        users = db.query(User).filter(User.deleted_at == None).all()
        print(f"📊 Found {len(users)} active users")
        
        users_without_accounts = []
        users_with_accounts = []
        accounts_created = 0
        
        for user in users:
            # Check if user has any accounts
            account_count = db.query(Account).filter(
                Account.user_id == user.id,
                Account.status == 'active'
            ).count()
            
            if account_count == 0:
                users_without_accounts.append(user)
                
                # Create default checking account
                try:
                    default_account = Account(
                        user_id=user.id,
                        account_type="checking",
                        balance=Decimal("0.00"),
                        currency="KZT",
                        status="active",
                        created_at=datetime.now()
                    )
                    db.add(default_account)
                    db.commit()
                    db.refresh(default_account)
                    
                    accounts_created += 1
                    print(f"✅ Created account #{default_account.id} for user #{user.id} ({user.name} {user.surname}, {user.email})")
                    
                except Exception as e:
                    print(f"❌ Error creating account for user #{user.id}: {e}")
                    db.rollback()
            else:
                users_with_accounts.append(user)
                print(f"✓  User #{user.id} ({user.name} {user.surname}) already has {account_count} account(s)")
        
        print("\n" + "="*80)
        print("Summary")
        print("="*80)
        print(f"Total users: {len(users)}")
        print(f"Users with accounts: {len(users_with_accounts)}")
        print(f"Users without accounts: {len(users_without_accounts)}")
        print(f"Accounts created: {accounts_created}")
        print("="*80 + "\n")
        
        if accounts_created > 0:
            print(f"✅ Successfully created {accounts_created} default account(s)!")
        else:
            print("✓  All users already have accounts!")
        
        return accounts_created
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    add_accounts_to_users()

