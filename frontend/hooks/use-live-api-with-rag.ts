/**
 * useLiveAPIWithRAG Hook
 * 
 * Simple extension of useLiveAPI with RAG backend integration.
 * Single endpoint: api/rag/live/query
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
  
  // Get user context from localStorage
  const getUserContext = useCallback(() => {
    try {
      const userJson = typeof localStorage !== 'undefined' ? localStorage.getItem('user') : null;
      if (userJson) {
        const user = JSON.parse(userJson);
        return {
          userId: user.id || 1,
          token: typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null
        };
      }
    } catch (e) {
      console.error('Failed to parse user data:', e);
    }
    return { userId: 1, token: null };
  }, []);

  // Check RAG health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(
          `${config.backendURL}${config.endpoints.rag.live.supervisorStatus}`,
          { method: 'GET', headers: { 'Content-Type': 'application/json' } }
        );

        if (response.ok) {
          const data = await response.json();
          const isHealthy = data.status === 'operational' && data.supervisor_agent?.initialized === true;
          setRAGToolsHealthy(isHealthy);
          console.log('[RAG] Health:', isHealthy ? '✅' : '⚠️');
        } else {
          setRAGToolsHealthy(false);
        }
      } catch (error) {
        setRAGToolsHealthy(false);
        console.error('[RAG] Health check error:', error);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Enhanced setConfig that adds RAG tool declaration
  const setConfigWithRAG = useCallback((newConfig: LiveConnectConfig) => {
    const withTools = ragToolsEnabled && ragToolsHealthy;
    
    const ragConfig: LiveConnectConfig = withTools
      ? {
          ...newConfig,
          tools: [
            {
              functionDeclarations: [
                {
                  name: "rag_query",
                  description: "Process user query through the RAG backend. Use this for ANY user question or request.",
                  parameters: {
                    type: "object" as any,
                    properties: {
                      query: {
                        type: "string" as any,
                        description: "The full user query/request text"
                      }
                    },
                    required: ["query"]
                  }
                }
              ]
            }
          ]
        }
      : newConfig;

    liveAPI.setConfig(ragConfig);
    console.log('[RAG] Config updated', withTools ? 'WITH tools' : 'WITHOUT tools');
  }, [liveAPI, ragToolsEnabled, ragToolsHealthy]);

  // Handle tool calls from Gemini
  useEffect(() => {
    const onToolCall = async (toolCall: any) => {
      console.log('[RAG] Tool call received:', toolCall);
      
      if (!ragToolsEnabled || !ragToolsHealthy) {
        console.warn('[RAG] Tools not enabled/healthy');
      }

      try {
        const functionCalls = toolCall.functionCalls || [];
        const functionResponses = [];

        for (const fc of functionCalls) {
          const { name, args, id } = fc;
          console.log(`[RAG] Executing: ${name}`, args);

          try {
            // Get user context
            const userContext = getUserContext();
            
            // Prepare request body - SIMPLE
            const requestBody = {
              query: args.query || "",
              user_id: userContext.userId
            };

            console.log(`[RAG] Request:`, requestBody);

            // Call the RAG API
            const response = await fetch(
              `${config.backendURL}${config.endpoints.rag.live.query}`,
              {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  ...(userContext.token ? { 'Authorization': `Bearer ${userContext.token}` } : {})
                },
                body: JSON.stringify(requestBody),
              }
            );

            console.log(`[RAG] Response status: ${response.status}`);

            if (response.ok) {
              const data = await response.json();
              console.log(`[RAG] Response:`, data);

              functionResponses.push({
                id,
                name,
                response: {
                  result: data.response || "No response from backend",
                  sources: data.sources || [],
                  confidence: data.confidence || 0,
                  agents_used: data.agents_used || []
                }
              });
            } else {
              const errorText = await response.text();
              console.error(`[RAG] Failed:`, response.status, errorText);
              functionResponses.push({
                id,
                name,
                response: {
                  error: `Failed to execute: ${response.status} ${response.statusText}`
                }
              });
            }
          } catch (toolError) {
            console.error(`[RAG] Error:`, toolError);
            functionResponses.push({
              id,
              name,
              response: {
                error: `Error: ${toolError instanceof Error ? toolError.message : String(toolError)}`
              }
            });
          }
        }

        // Send responses back to Gemini
        if (functionResponses.length > 0) {
          console.log('[RAG] Sending responses:', functionResponses);
          await liveAPI.client.sendToolResponse({ functionResponses });
          console.log('[RAG] ✅ Responses sent');
        }
      } catch (error) {
        console.error('[RAG] ❌ Tool execution error:', error);
      }
    };

    // Listen for tool calls
    liveAPI.client.on('toolcall', onToolCall);

    return () => {
      liveAPI.client.off('toolcall', onToolCall);
    };
  }, [liveAPI.client, ragToolsEnabled, ragToolsHealthy, getUserContext]);

  return {
    ...liveAPI,
    setConfig: setConfigWithRAG,
    ragToolsEnabled,
    ragToolsHealthy,
    setRAGToolsEnabled,
  };
}

