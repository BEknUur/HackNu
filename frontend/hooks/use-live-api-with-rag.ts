/**
 * useLiveAPIWithRAG Hook
 * 
 * Extends the useLiveAPI hook with RAG (Retrieval-Augmented Generation) capabilities.
 * This hook integrates with the backend RAG system to provide:
 * - Vector search (company knowledge base)
 * - Web search (real-time information)
 * - Multi-agent coordination
 */

import { useCallback, useEffect, useState } from "react";
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

  // Enhanced setConfig that adds RAG tool declarations
  const setConfigWithRAG = useCallback((newConfig: LiveConnectConfig) => {
    if (ragToolsEnabled && ragToolsHealthy) {
      // Add RAG function declarations to the config
      const ragConfig: LiveConnectConfig = {
        ...newConfig,
        tools: [
          {
            functionDeclarations: [
              {
                name: "vector_search",
                description: "Search company internal documents, policies, and knowledge base. Use this for questions about company information, internal procedures, policies, or any company-specific knowledge.",
                parameters: {
                  type: "object" as any,
                  properties: {
                    query: {
                      type: "string" as any,
                      description: "The search query to find relevant information from company documents"
                    }
                  },
                  required: ["query"]
                }
              },
              {
                name: "web_search",
                description: "Search the web for current information, news, and general knowledge. Use this for questions about current events, real-time information, or general topics not in company documents.",
                parameters: {
                  type: "object" as any,
                  properties: {
                    query: {
                      type: "string" as any,
                      description: "The search query to find information on the web"
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
      console.log('[RAG] Config updated with RAG tools');
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
          console.log(`[RAG] Executing tool: ${name}`, args);

          // Call the backend RAG API
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
                  tool_name: name,
                  session_id: Date.now().toString(),
                }
              }),
            }
          );

          if (response.ok) {
            const data = await response.json();
            console.log(`[RAG] Tool ${name} response:`, data);

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
            console.error(`[RAG] Tool ${name} failed:`, response.status);
            functionResponses.push({
              id,
              name,
              response: {
                error: `Failed to execute ${name}: ${response.statusText}`
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
