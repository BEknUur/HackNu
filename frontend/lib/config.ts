/**
 * Configuration Module
 * 
 * Centralized configuration for the frontend application
 */

import Constants from 'expo-constants';

/**
 * Backend server URL (fallback for mobile/development)
 */
export const BACKEND_SERVER = 'https://46.101.175.118:8000' as const;

/**
 * Get backend API URL
 */
export function getBackendURL(): string {
  // For web in production with HTTPS, use relative paths (empty string)
  // This allows nginx reverse proxy to handle API requests
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    console.log('[Config] Backend URL: (relative path via nginx proxy)');
    return ''; // Empty string for relative paths
  }
  
  // Priority order for other environments:
  // 1. Environment variable (from .env file)
  // 2. Expo config extra (from app.json)
  // 3. Default server URL
  const url = 
    process.env.EXPO_PUBLIC_BACKEND_URL ||
    Constants.expoConfig?.extra?.BACKEND_URL ||
    BACKEND_SERVER;
  
  console.log('[Config] Backend URL:', url);
  return url;
}

/**
 * Get Gemini API Key
 */
export function getGeminiAPIKey(): string {
  // Priority order:
  // 1. Environment variable (from .env file) - PREFERRED
  // 2. Expo config extra (from app.json) - DEPRECATED for security
  const key = 
    process.env.EXPO_PUBLIC_GEMINI_API_KEY ||
    Constants.expoConfig?.extra?.GEMINI_API_KEY ||
    '';
  
  if (!key) {
    console.warn('[Config] Gemini API Key not configured!');
    console.warn('[Config] Please set EXPO_PUBLIC_GEMINI_API_KEY in .env file');
  }
  
  return key;
}

/**
 * Configuration object
 */
export const config = {
  backendURL: getBackendURL(),
  geminiAPIKey: getGeminiAPIKey(),
  
  // Backend server URL
  server: BACKEND_SERVER,
  
  // API endpoints
  endpoints: {
    rag: {
      query: '/api/rag/query',
      status: '/api/rag/status',
      toolsStatus: '/api/rag/tools/status',
      live: {
        query: '/api/rag/live/query',
        supervisorStatus: '/api/rag/live/supervisor/status',
        initialize: '/api/rag/live/supervisor/initialize',
      }
    },
    products: '/api/products',
    cart: '/api/cart',
    auth: '/api/auth',
    faceid: '/api/faceid',
    accounts: '/api/accounts',
    transactions: '/api/transactions',
  },
  
  // Feature flags
  features: {
    ragTools: true,
    faceVerification: true,
    liveChat: true,
  },
};

/**
 * Check if using the configured backend
 */
export function isConfiguredBackend(): boolean {
  return config.backendURL === BACKEND_SERVER;
}

// Log configuration on load (only in development)
if (__DEV__) {
  console.log('[Config] Application configuration:', {
    backendURL: config.backendURL,
    hasGeminiKey: !!config.geminiAPIKey,
    features: config.features,
  });
  console.log('[Config] To switch backend: Set EXPO_PUBLIC_BACKEND_URL in .env');
  console.log('[Config] Default server:', BACKEND_SERVER);
}
