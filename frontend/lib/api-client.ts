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

// Financial Analysis Types
export interface FinancialAnalysisResponse {
  user_id: number;
  analysis_period_months: number;
  financial_data: {
    user_info: {
      user_id: number;
      name: string;
      email: string;
      member_since: string;
    };
    accounts_summary: {
      total_accounts: number;
      accounts: Array<{
        id: number;
        type: string;
        balance: number;
        currency: string;
        status: string;
      }>;
      total_balance_by_currency: Record<string, number>;
      account_types: string[];
    };
    transactions_analysis: {
      total_transactions: number;
      period_months: number;
      by_type: Record<string, { count: number; total_amount: number; currency: string }>;
      recent_transactions: Array<{
        id: number;
        amount: number;
        currency: string;
        type: string;
        description: string;
        date: string;
      }>;
      average_transactions_per_month: number;
    };
    spending_breakdown: {
      total_spending: number;
      average_monthly_spending: number;
      by_category: Record<string, number>;
      monthly_breakdown: Record<string, number>;
      spending_volatility: number;
      highest_spending_month: string;
      highest_spending_amount: number;
    };
    income_analysis: {
      total_income: number;
      average_monthly_income: number;
      monthly_breakdown: Record<string, number>;
      income_transactions_count: number;
    };
    financial_goals: {
      total_goals: number;
      active_goals: Array<any>;
      achieved_goals: Array<any>;
      total_target_amount: number;
      total_current_savings: number;
      overall_progress_percentage: number;
    };
    financial_health: {
      health_score: number;
      savings_rate_percentage: number;
      expense_ratio_percentage: number;
      average_monthly_savings: number;
      spending_stability: string;
      financial_status: string;
    };
    recommendations_data: {
      needs_budget_adjustment: boolean;
      needs_savings_increase: boolean;
      spending_is_volatile: boolean;
      has_negative_cash_flow: boolean;
      top_spending_categories: Array<[string, number]>;
    };
    generated_at: string;
  };
  ai_insights: string;
  specific_query: string | null;
  status: string;
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

/**
 * Get comprehensive financial analysis for a user
 */
export async function getFinancialAnalysis(
  userId: number,
  monthsBack: number = 6,
  specificQuery?: string
): Promise<FinancialAnalysisResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    months_back: String(monthsBack),
  });

  if (specificQuery) {
    params.append('specific_query', specificQuery);
  }

  const url = `${config.backendURL}/api/predict/analyze?${params.toString()}`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to fetch financial analysis');
  }

  return response.json();
}

