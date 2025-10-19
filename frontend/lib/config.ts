/**
 * Configuration Module
 * 
 * Centralized configuration for the frontend application
 */

import Constants from 'expo-constants';

/**
 * Available backend servers
 */
export const BACKEND_SERVERS = {
  LOCAL: 'http://localhost:8000',
  PRODUCTION: 'http://46.101.175.118:8000',
} as const;

/**
 * Get backend API URL
 */
export function getBackendURL(): string {
  // Priority order:
  // 1. Environment variable (from .env file)
  // 2. Expo config extra (from app.json)
  // 3. Default server URL (localhost for development)
  const url = 
    process.env.EXPO_PUBLIC_BACKEND_URL ||
    Constants.expoConfig?.extra?.BACKEND_URL ||
    BACKEND_SERVERS.LOCAL;
  
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
  
  // Available backend servers for easy switching
  servers: BACKEND_SERVERS,
  
  // API endpoints
  endpoints: {
    rag: {
      query: '/api/rag/query',
      status: '/api/rag/status',
      toolsStatus: '/api/rag/tools/status',
      live: {
        functionDeclarations: '/api/rag/live/function-declarations',
        toolCall: '/api/rag/live/tool-call',
        health: '/api/rag/live/health',
      }
    },
    products: '/api/products',
    cart: '/api/cart',
    auth: '/api/auth',
    faceid: '/api/faceid',
  },
  
  // Feature flags
  features: {
    ragTools: true,
    faceVerification: true,
    liveChat: true,
  },
};

/**
 * Check if using production backend
 */
export function isProduction(): boolean {
  return config.backendURL === BACKEND_SERVERS.PRODUCTION;
}

/**
 * Check if using local backend
 */
export function isLocal(): boolean {
  return config.backendURL === BACKEND_SERVERS.LOCAL;
}

// Log configuration on load (only in development)
if (__DEV__) {
  console.log('[Config] Application configuration:', {
    backendURL: config.backendURL,
    environment: isProduction() ? 'PRODUCTION' : 'LOCAL',
    hasGeminiKey: !!config.geminiAPIKey,
    features: config.features,
  });
  console.log('[Config] To switch backend: Set EXPO_PUBLIC_BACKEND_URL in .env');
  console.log('[Config] Available servers:', BACKEND_SERVERS);
}
