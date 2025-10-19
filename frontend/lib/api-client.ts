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
  detail: string | any[];
  message?: string;
  errors?: any[];
}

export interface UserData {
  id: number;
  name: string;
  surname: string;
  email: string;
  phone: string;
  avatar?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  surname: string;
  email: string;
  phone: string;
  password: string;
  avatar?: File | Blob;
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
    const errorMsg = typeof error.detail === 'string' ? error.detail : 'Failed to fetch accounts';
    throw new Error(errorMsg);
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
    const errorMsg = typeof error.detail === 'string' ? error.detail : 'Failed to create account';
    throw new Error(errorMsg);
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
    const errorMsg = typeof error.detail === 'string' ? error.detail : 'Failed to fetch transactions';
    throw new Error(errorMsg);
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
    const errorMsg = typeof error.detail === 'string' ? error.detail : 'Failed to create deposit';
    throw new Error(errorMsg);
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
    const errorMsg = typeof error.detail === 'string' ? error.detail : 'Failed to create withdrawal';
    throw new Error(errorMsg);
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
    const errorMsg = typeof error.detail === 'string' ? error.detail : 'Failed to create transfer';
    throw new Error(errorMsg);
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
    const errorMsg = typeof error.detail === 'string' ? error.detail : 'Failed to fetch financial analysis';
    throw new Error(errorMsg);
  }

  return response.json();
}

/**
 * Parse API error response into user-friendly message
 */
function parseErrorMessage(error: ApiError, statusCode: number): string {
  if (typeof error.detail === 'string') {
    return error.detail;
  }
  
  if (Array.isArray(error.detail)) {
    return error.detail
      .map((e: any) => e.msg || e.message || JSON.stringify(e))
      .join('\n');
  }
  
  if (error.message) {
    return error.message;
  }
  
  // Default messages by status code
  switch (statusCode) {
    case 400:
      return 'Invalid request. Please check your input.';
    case 401:
      return 'Invalid email or password.';
    case 403:
      return 'Access denied.';
    case 404:
      return 'Resource not found.';
    case 422:
      return 'Validation error. Please check your input.';
    case 500:
      return 'Server error. Please try again later.';
    default:
      return 'An unexpected error occurred.';
  }
}

/**
 * Login with email and password
 */
export async function loginUser(credentials: LoginRequest): Promise<UserData> {
  try {
    const url = `${config.backendURL}/api/auth/login`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        email: credentials.email.trim().toLowerCase(),
        password: credentials.password,
      }),
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({ 
        detail: 'Failed to connect to server' 
      }));
      
      throw new Error(parseErrorMessage(error, response.status));
    }

    const userData: UserData = await response.json();
    return userData;
    
  } catch (error: any) {
    // Re-throw with better context
    if (error.message) {
      throw error;
    }
    
    if (error.name === 'TypeError' && error.message?.includes('fetch')) {
      throw new Error('Network error: Cannot connect to server. Please check your internet connection.');
    }
    
    throw new Error('Login failed. Please try again.');
  }
}

/**
 * Register a new user with avatar
 */
export async function registerUser(data: RegisterRequest): Promise<UserData> {
  try {
    const url = `${config.backendURL}/api/auth/register`;
    
    const formData = new FormData();
    formData.append('name', data.name.trim());
    formData.append('surname', data.surname.trim());
    formData.append('email', data.email.trim().toLowerCase());
    formData.append('phone', data.phone.trim());
    formData.append('password', data.password);
    
    if (data.avatar) {
      // @ts-ignore - FormData accepts blob with filename
      formData.append('avatar', data.avatar, 'avatar.jpg');
    }

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({ 
        detail: 'Failed to connect to server' 
      }));
      
      let errorMessage = parseErrorMessage(error, response.status);
      
      // Specific handling for registration errors
      if (response.status === 400) {
        if (typeof error.detail === 'string') {
          if (error.detail.toLowerCase().includes('email')) {
            errorMessage = 'This email is already registered. Please use a different email or try logging in.';
          } else if (error.detail.toLowerCase().includes('phone')) {
            errorMessage = 'This phone number is already registered. Please use a different number.';
          }
        }
      }
      
      throw new Error(errorMessage);
    }

    const userData: UserData = await response.json();
    return userData;
    
  } catch (error: any) {
    // Re-throw with better context
    if (error.message) {
      throw error;
    }
    
    if (error.name === 'TypeError' && error.message?.includes('fetch')) {
      throw new Error('Network error: Cannot connect to server. Please check your internet connection.');
    }
    
    throw new Error('Registration failed. Please try again.');
  }
}

/**
 * Verify face ID
 */
export async function verifyFaceID(photoBlob: Blob): Promise<{
  success: boolean;
  verified: boolean;
  message: string;
  user?: UserData;
  confidence?: number;
  distance?: number;
  error?: string;
}> {
  try {
    const url = `${config.backendURL}/api/faceid/verify`;
    
    const formData = new FormData();
    // @ts-ignore - FormData accepts blob with filename
    formData.append('file', photoBlob, 'photo.jpg');

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({ 
        detail: 'Face verification failed' 
      }));
      
      throw new Error(parseErrorMessage(error, response.status));
    }

    return response.json();
    
  } catch (error: any) {
    // Re-throw with better context
    if (error.message) {
      throw error;
    }
    
    if (error.name === 'TypeError' && error.message?.includes('fetch')) {
      throw new Error('Network error: Cannot connect to server. Please check your internet connection.');
    }
    
    throw new Error('Face verification failed. Please try again.');
  }
}

