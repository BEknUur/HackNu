/**
 * RAG Tools Health Check Hook
 * 
 * Monitors the backend RAG system status and provides real-time health information
 * for the Gemini Live Chat RAG integration.
 */

import { useState, useEffect, useCallback } from 'react';
import { config } from '@/lib/config';

interface RAGStatus {
  status: 'operational' | 'not_initialized' | 'error';
  supervisor_agent: {
    initialized: boolean;
    type: string | null;
  };
  specialist_agents: {
    available: string[];
    count: number;
  };
  configuration: {
    environment: string;
    max_iterations: number;
    parallel_agents: boolean;
  };
  tools: {
    available: string[];
    enabled: boolean;
  };
}

interface UseRAGToolsResult {
  /** Whether RAG tools are enabled and available */
  ragToolsEnabled: boolean;
  /** Whether RAG system is healthy and operational */
  ragToolsHealthy: boolean;
  /** Detailed RAG status information */
  ragStatus: RAGStatus | null;
  /** Error message if health check failed */
  error: string | null;
  /** Whether currently checking health */
  isChecking: boolean;
  /** Manually trigger a health check */
  checkHealth: () => Promise<void>;
}

/**
 * Hook to monitor RAG system health and availability
 * 
 * Checks the backend /api/rag/live/supervisor/status endpoint
 * to determine if RAG tools are available for Gemini Live.
 * 
 * @param autoCheck - Whether to automatically check on mount (default: true)
 * @param checkInterval - Interval in ms to re-check health (default: 30000 = 30s, 0 = no auto-refresh)
 * @returns RAG tools status and health information
 * 
 * @example
 * ```tsx
 * const { ragToolsEnabled, ragToolsHealthy } = useRAGTools();
 * 
 * return (
 *   <View>
 *     {ragToolsEnabled && (
 *       <Text>RAG Status: {ragToolsHealthy ? 'Healthy' : 'Error'}</Text>
 *     )}
 *   </View>
 * );
 * ```
 */
export function useRAGTools(
  autoCheck: boolean = true,
  checkInterval: number = 30000
): UseRAGToolsResult {
  const [ragStatus, setRagStatus] = useState<RAGStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const checkHealth = useCallback(async () => {
    setIsChecking(true);
    setError(null);

    try {
      const response = await fetch(
        `${config.backendURL}/api/rag/live/supervisor/status`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
      }

      const data: RAGStatus = await response.json();
      setRagStatus(data);
      
      console.log('[RAG Health Check] Status:', data.status);
      console.log('[RAG Health Check] Supervisor initialized:', data.supervisor_agent.initialized);
      console.log('[RAG Health Check] Specialist agents:', data.specialist_agents.available);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('[RAG Health Check] Error:', errorMessage);
      setError(errorMessage);
      setRagStatus(null);
    } finally {
      setIsChecking(false);
    }
  }, []);

  // Auto-check on mount
  useEffect(() => {
    if (autoCheck) {
      checkHealth();
    }
  }, [autoCheck, checkHealth]);

  // Auto-refresh at interval
  useEffect(() => {
    if (checkInterval > 0 && autoCheck) {
      const intervalId = setInterval(checkHealth, checkInterval);
      return () => clearInterval(intervalId);
    }
  }, [checkInterval, autoCheck, checkHealth]);

  // Compute derived values
  const ragToolsEnabled = ragStatus !== null && ragStatus.status !== 'error';
  const ragToolsHealthy = 
    ragStatus !== null && 
    ragStatus.status === 'operational' && 
    ragStatus.supervisor_agent.initialized &&
    ragStatus.specialist_agents.count > 0;

  return {
    ragToolsEnabled,
    ragToolsHealthy,
    ragStatus,
    error,
    isChecking,
    checkHealth,
  };
}

export default useRAGTools;
