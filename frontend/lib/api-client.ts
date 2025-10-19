/**
 * API Client for Transaction and Account Operations
 */

import { config } from './config';

// TypeScript Interfaces
export interface Account {
  id: number;
  user_id: number;
  account_type: string;
  balance: string;
  currency: string;
  status: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Transaction {
  id: number;
  user_id: number;
  account_id: number;
  amount: string;
  currency: string;
  transaction_type: string;
  description?: string | null;
  to_user_id?: number | null;
  to_account_id?: number | null;
  product_id?: number | null;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface TransactionDepositRequest {
  account_id: number;
  amount: number;
  currency: string;
  description?: string;
}

export interface TransactionWithdrawalRequest {
  account_id: number;
  amount: number;
  currency: string;
  description?: string;
}

export interface TransactionTransferRequest {
  from_account_id: number;
  to_account_id: number;
  amount: number;
  currency: string;
  description?: string;
}

export interface ApiError {
  detail: string;
}

export interface AccountCreate {
  user_id: number;
  account_type: string;
  balance?: number;
  currency: string;
}

/**
 * Get user's accounts
 */
export async function getUserAccounts(userId: number): Promise<Account[]> {
  const url = `${config.backendURL}/api/accounts/user/${userId}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to fetch accounts');
  }

  return response.json();
}

/**
 * Create a new account for user
 */
export async function createAccount(data: AccountCreate): Promise<Account> {
  const url = `${config.backendURL}/api/accounts`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to create account');
  }

  return response.json();
}

/**
 * Get user's transactions with optional filters
 */
export async function getUserTransactions(
  userId: number,
  filters?: {
    account_id?: number;
    transaction_type?: string;
    skip?: number;
    limit?: number;
  }
): Promise<Transaction[]> {
  const params = new URLSearchParams({
    skip: String(filters?.skip ?? 0),
    limit: String(filters?.limit ?? 100),
  });

  if (filters?.account_id) {
    params.append('account_id', String(filters.account_id));
  }

  if (filters?.transaction_type) {
    params.append('transaction_type', filters.transaction_type);
  }

  const url = `${config.backendURL}/api/transactions/user/${userId}?${params.toString()}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to fetch transactions');
  }

  return response.json();
}

/**
 * Create a deposit transaction
 */
export async function createDeposit(
  userId: number,
  data: TransactionDepositRequest
): Promise<Transaction> {
  const url = `${config.backendURL}/api/transactions/deposit?user_id=${userId}`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to create deposit');
  }

  return response.json();
}

/**
 * Create a withdrawal transaction
 */
export async function createWithdrawal(
  userId: number,
  data: TransactionWithdrawalRequest
): Promise<Transaction> {
  const url = `${config.backendURL}/api/transactions/withdrawal?user_id=${userId}`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to create withdrawal');
  }

  return response.json();
}

/**
 * Create a transfer transaction
 */
export async function createTransfer(
  userId: number,
  data: TransactionTransferRequest
): Promise<Transaction> {
  const url = `${config.backendURL}/api/transactions/transfer?user_id=${userId}`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to create transfer');
  }

  return response.json();
}

