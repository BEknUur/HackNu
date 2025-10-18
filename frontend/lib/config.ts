/**
 * Configuration Module
 * 
 * Centralized configuration for the frontend application
 */

import Constants from 'expo-constants';

/**
 * Get backend API URL
 */
export function getBackendURL(): string {
  // Priority order:
  // 1. Environment variable (from .env file)
  // 2. Expo config extra (from app.json)
  // 3. Default server URL
  const url = 
    process.env.EXPO_PUBLIC_BACKEND_URL ||
    Constants.expoConfig?.extra?.BACKEND_URL ||
    'http://46.101.175.118:8000';
  
  console.log('[Config] Backend URL:', url);
  return url;
}

/**
 * Get Gemini API Key
 */
export function getGeminiAPIKey(): string {
  const key = 
    Constants.expoConfig?.extra?.GEMINI_API_KEY ||
    process.env.EXPO_PUBLIC_GEMINI_API_KEY ||
    '';
  
  if (!key) {
    console.warn('[Config] Gemini API Key not configured!');
  }
  
  return key;
}

/**
 * Configuration object
 */
export const config = {
  backendURL: getBackendURL(),
  geminiAPIKey: getGeminiAPIKey(),
  
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

// Log configuration on load (only in development)
if (__DEV__) {
  console.log('[Config] Application configuration:', {
    backendURL: config.backendURL,
    hasGeminiKey: !!config.geminiAPIKey,
    features: config.features,
  });
}

