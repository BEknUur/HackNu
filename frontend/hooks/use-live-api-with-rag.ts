/**
 * useLiveAPIWithRAG Hook
 * 
 * Extends the useLiveAPI hook with RAG (Retrieval-Augmented Generation) capabilities.
 * This hook integrates with the backend RAG system to provide:
 * - Vector search (company knowledge base)
 * - Web search (real-time information)
 * - Multi-agent coordination
 */

import { useCallback, useEffect, useState, useRef } from "react";
import { useLiveAPI, UseLiveAPIResults } from "./use-live-api";
import { LiveClientOptions } from "../lib/types";
import { LiveConnectConfig } from "@google/genai";
import { config } from "../lib/config";

export interface UseLiveAPIWithRAGResults extends UseLiveAPIResults {
  ragToolsEnabled: boolean;
  ragToolsHealthy: boolean;
  setRAGToolsEnabled: (enabled: boolean) => void;
}

/**
 * Enhanced useLiveAPI hook with RAG tools integration
 */
export function useLiveAPIWithRAG(options: LiveClientOptions): UseLiveAPIWithRAGResults {
  const liveAPI = useLiveAPI(options);
  const [ragToolsEnabled, setRAGToolsEnabled] = useState(true);
  const [ragToolsHealthy, setRAGToolsHealthy] = useState(false);
  const lastConfigRef = useRef<string | null>(null);

  // Check RAG tools health on mount and periodically
  useEffect(() => {
    let healthCheckInterval: ReturnType<typeof setInterval> | null = null;

    const checkRAGHealth = async () => {
      try {
        const response = await fetch(
          `${config.backendURL}${config.endpoints.rag.live.supervisorStatus}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          const isHealthy = data.status === 'operational' && 
                          data.supervisor_agent?.initialized === true;
          setRAGToolsHealthy(isHealthy);
          console.log('[RAG] Health check:', isHealthy ? '✅ Healthy' : '⚠️ Unhealthy', data);
        } else {
          setRAGToolsHealthy(false);
          console.warn('[RAG] Health check failed:', response.status);
        }
      } catch (error) {
        setRAGToolsHealthy(false);
        console.error('[RAG] Health check error:', error);
      }
    };

    // Initial health check
    checkRAGHealth();

    // Check health every 30 seconds
    healthCheckInterval = setInterval(checkRAGHealth, 30000);

    return () => {
      if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
      }
    };
  }, []);

  // Enhanced setConfig - ONE tool that sends to Supervisor Agent
  const setConfigWithRAG = useCallback((newConfig: LiveConnectConfig) => {
    // Create a stable config string to prevent infinite loops
    const configString = JSON.stringify(newConfig);
    
    if (lastConfigRef.current === configString) {
      console.log('[RAG] Config unchanged, skipping update');
      return;
    }
    
    lastConfigRef.current = configString;

    if (ragToolsEnabled && ragToolsHealthy) {
      // Declare ONE tool that sends queries to the Supervisor Agent
      // The Supervisor will then decide which specific tools (vector_search, web_search, etc.) to use
      const ragConfig: LiveConnectConfig = {
        ...newConfig,
        tools: [
          {
            functionDeclarations: [
              {
                name: "query_knowledge_system",
                description: "Search and retrieve information from Zaman Bank's knowledge base, company documents, policies, and the web. Use this for ANY question about company information, banking services, policies, procedures, or general knowledge. The backend AI supervisor will automatically determine the best sources to use.",
                parameters: {
                  type: "object" as any,
                  properties: {
                    query: {
                      type: "string" as any,
                      description: "The user's question or query"
                    }
                  },
                  required: ["query"]
                }
              }
            ]
          }
        ]
      };
      liveAPI.setConfig(ragConfig);
      console.log('[RAG] Config updated - Supervisor Agent enabled via query_knowledge_system tool');
    } else {
      liveAPI.setConfig(newConfig);
      console.log('[RAG] Config updated without RAG tools');
    }
  }, [liveAPI, ragToolsEnabled, ragToolsHealthy]);

  // Handle tool calls from Gemini
  useEffect(() => {
    const onToolCall = async (toolCall: any) => {
      if (!ragToolsEnabled || !ragToolsHealthy) {
        console.warn('[RAG] Tool call received but RAG tools are not enabled/healthy');
        return;
      }

      console.log('[RAG] Tool call received:', toolCall);

      try {
        const functionCalls = toolCall.functionCalls || [];
        const functionResponses = [];

        for (const fc of functionCalls) {
          const { name, args, id } = fc;
          console.log(`[RAG] Gemini called tool: ${name}`, args);
          console.log(`[RAG] Sending query to Supervisor Agent`);

          // Call the backend RAG API - Supervisor Agent will decide which tools to use
          const response = await fetch(
            `${config.backendURL}${config.endpoints.rag.live.query}`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                query: args.query,
                context: {
                  session_id: Date.now().toString(),
                  // NO tool_name - let Supervisor decide!
                }
              }),
            }
          );

          if (response.ok) {
            const data = await response.json();
            console.log(`[RAG] Supervisor response:`, data);
            console.log(`[RAG] Tools used by Supervisor:`, data.agents_used);

            functionResponses.push({
              id,
              name,
              response: {
                result: data.response,
                sources: data.sources,
                confidence: data.confidence,
                agents_used: data.agents_used,
              }
            });
          } else {
            console.error(`[RAG] Supervisor query failed:`, response.status);
            functionResponses.push({
              id,
              name,
              response: {
                error: `Failed to execute query: ${response.statusText}`
              }
            });
          }
        }

        // Send tool responses back to Gemini
        if (functionResponses.length > 0) {
          liveAPI.client.sendToolResponse({ functionResponses });
          console.log('[RAG] Tool responses sent:', functionResponses.length);
        }
      } catch (error) {
        console.error('[RAG] Tool execution error:', error);
      }
    };

    // Listen for tool calls
    liveAPI.client.on('toolcall', onToolCall);

    return () => {
      liveAPI.client.off('toolcall', onToolCall);
    };
  }, [liveAPI.client, ragToolsEnabled, ragToolsHealthy]);

  return {
    ...liveAPI,
    setConfig: setConfigWithRAG,
    ragToolsEnabled,
    ragToolsHealthy,
    setRAGToolsEnabled,
  };
}
