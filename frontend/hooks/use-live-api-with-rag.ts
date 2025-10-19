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
  
  // Get user context from localStorage (same as explore.tsx)
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
    return { userId: 1, token: null }; // Fallback to user 1 if no auth
  }, []);

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
    // Build the effective config (with or without tools based on health)
    const withTools = ragToolsEnabled && ragToolsHealthy;
    const ragConfig: LiveConnectConfig = withTools
      ? {
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
              },
              {
                name: "transfer_money",
                description: "IMMEDIATELY transfer money between accounts. Call this function when user says 'send money', 'transfer', or similar.",
                parameters: {
                  type: "object" as any,
                  properties: {
                    from_account_id: {
                      type: "number" as any,
                      description: "The ID of the source account to transfer money from"
                    },
                    to_account_id: {
                      type: "number" as any,
                      description: "The ID of the destination account to transfer money to"
                    },
                    amount: {
                      type: "number" as any,
                      description: "The amount of money to transfer (must be positive)"
                    },
                    currency: {
                      type: "string" as any,
                      description: "The currency code (KZT, USD, EUR). Default is KZT"
                    },
                    description: {
                      type: "string" as any,
                      description: "Optional description for the transfer"
                    }
                  },
                  required: ["from_account_id", "to_account_id", "amount"]
                }
              },
              {
                name: "deposit_money",
                description: "IMMEDIATELY deposit money to account. Call this function when user says 'deposit', 'add money', or similar.",
                parameters: {
                  type: "object" as any,
                  properties: {
                    account_id: {
                      type: "number" as any,
                      description: "The ID of the account to deposit money into"
                    },
                    amount: {
                      type: "number" as any,
                      description: "The amount of money to deposit (must be positive)"
                    },
                    currency: {
                      type: "string" as any,
                      description: "The currency code (KZT, USD, EUR). Default is KZT"
                    },
                    description: {
                      type: "string" as any,
                      description: "Optional description for the deposit"
                    }
                  },
                  required: ["account_id", "amount"]
                }
              },
              {
                name: "withdraw_money",
                description: "IMMEDIATELY withdraw money from account. Call this function when user says 'withdraw', 'take out money', or similar.",
                parameters: {
                  type: "object" as any,
                  properties: {
                    account_id: {
                      type: "number" as any,
                      description: "The ID of the account to withdraw money from"
                    },
                    amount: {
                      type: "number" as any,
                      description: "The amount of money to withdraw (must be positive)"
                    },
                    currency: {
                      type: "string" as any,
                      description: "The currency code (KZT, USD, EUR). Default is KZT"
                    },
                    description: {
                      type: "string" as any,
                      description: "Optional description for the withdrawal"
                    }
                  },
                  required: ["account_id", "amount"]
                }
              },
              {
                name: "get_my_accounts",
                description: "IMMEDIATELY show all user accounts and balances. Call this function when user says 'show accounts', 'my accounts', 'balance', or similar.",
                parameters: {
                  type: "object" as any,
                  properties: {},
                  required: []
                }
              },
              {
                name: "get_account_balance",
                description: "IMMEDIATELY get balance of specific account. Call this function when user asks about balance of a particular account.",
                parameters: {
                  type: "object" as any,
                  properties: {
                    account_id: {
                      type: "number" as any,
                      description: "The ID of the account to check balance for"
                    }
                  },
                  required: ["account_id"]
                }
              }
            ]
          }
        ]
        }
      : newConfig;

    // Create a stable string of the EFFECTIVE config including tools/health
    const effectiveConfigString = JSON.stringify({ ragConfig });
    if (lastConfigRef.current === effectiveConfigString) {
      console.log('[RAG] Effective config unchanged, skipping update');
      return;
    }
    lastConfigRef.current = effectiveConfigString;

    // Apply config
    liveAPI.setConfig(ragConfig);
    console.log(withTools ? '[RAG] Config updated WITH RAG tools' : '[RAG] Config updated WITHOUT RAG tools');
  }, [liveAPI, ragToolsEnabled, ragToolsHealthy]);

  // Edge-triggered reconnect only when health flips from false -> true
  const prevHealthyRef = useRef<boolean>(false);
  const reconnectingRef = useRef<boolean>(false);
  const cooldownRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const becameHealthy = ragToolsEnabled && ragToolsHealthy && !prevHealthyRef.current;

    if (!ragToolsHealthy) {
      // If health goes unhealthy, allow future reconnect when it becomes healthy again
      prevHealthyRef.current = false;
      if (cooldownRef.current) {
        clearTimeout(cooldownRef.current);
        cooldownRef.current = null;
      }
      return;
    }

    if (becameHealthy && !reconnectingRef.current) {
      // Guard against rapid repeats
      reconnectingRef.current = true;
      console.log('[RAG] Reconnecting to apply RAG tools in active session...');

      // Best-effort reconnect; ignore errors
      liveAPI
        .connect()
        .then(() => console.log('[RAG] Reconnected with tools'))
        .catch((err) => console.warn('[RAG] Reconnect warning:', err?.message || err))
        .finally(() => {
          prevHealthyRef.current = true;
          reconnectingRef.current = false;
          // Cooldown to avoid re-trigger from transient state churn
          if (cooldownRef.current) clearTimeout(cooldownRef.current);
          cooldownRef.current = setTimeout(() => {
            // Keep prevHealthy true; effect only fires again if health becomes false then true
            cooldownRef.current = null;
          }, 3000);
        });
    }
  }, [ragToolsEnabled, ragToolsHealthy, liveAPI]);

  // Handle tool calls from Gemini
  useEffect(() => {
    const onToolCall = async (toolCall: any) => {
      console.log('[RAG] Tool call received:', toolCall);
      console.log('[RAG] Tools status:', { ragToolsEnabled, ragToolsHealthy });
      
      if (!ragToolsEnabled || !ragToolsHealthy) {
        console.warn('[RAG] Tool call received but RAG tools are not enabled/healthy');
        // Still try to process the tool call even if health check failed
        // return;
      }

      try {
        const functionCalls = toolCall.functionCalls || [];
        const functionResponses = [];

        console.log(`[RAG] Processing ${functionCalls.length} function call(s)`);

        for (const fc of functionCalls) {
          const { name, args, id } = fc;
          console.log(`[RAG] Executing tool: ${name}`, { id, args });

          try {
            // Prepare natural language query for the RAG system
            let naturalQuery = "";
            
            // Convert function calls to natural language
            if (name === "transfer_money") {
              naturalQuery = `Transfer ${args.amount} ${args.currency || 'KZT'} from account ${args.from_account_id} to account ${args.to_account_id}`;
              if (args.description) naturalQuery += ` for ${args.description}`;
            } else if (name === "deposit_money") {
              naturalQuery = `Deposit ${args.amount} ${args.currency || 'KZT'} to account ${args.account_id}`;
              if (args.description) naturalQuery += ` for ${args.description}`;
            } else if (name === "withdraw_money") {
              naturalQuery = `Withdraw ${args.amount} ${args.currency || 'KZT'} from account ${args.account_id}`;
              if (args.description) naturalQuery += ` for ${args.description}`;
            } else if (name === "get_my_accounts") {
              naturalQuery = "Show me all my accounts with balances";
            } else if (name === "get_account_balance") {
              naturalQuery = `What is the balance of account ${args.account_id}?`;
            } else if (name === "get_account_details") {
              naturalQuery = `Show me details of account ${args.account_id}`;
            } else if (name === "vector_search") {
              naturalQuery = args.query;
            } else if (name === "web_search") {
              naturalQuery = args.query;
            } else {
              naturalQuery = args.query || `Execute ${name} with parameters`;
            }

            console.log(`[RAG] Natural query: ${naturalQuery}`);

            // Get current user context
            const userContext = getUserContext();
            
            let requestBody: any = {
              query: naturalQuery,
              context: {
                session_id: Date.now().toString(),
                original_function: name,
                ...args  // Include all function arguments in context for reference
              }
            };

            // For transaction tools, add authenticated user_id
            if (['transfer_money', 'deposit_money', 'withdraw_money', 'get_my_accounts', 'get_account_balance', 'get_account_details'].includes(name)) {
              requestBody.user_id = userContext.userId;
              console.log(`[RAG] Using authenticated user ID: ${userContext.userId}`);
            }

            console.log(`[RAG] Sending request:`, requestBody);

            // Call the backend RAG API
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
              const errorText = await response.text();
              console.error(`[RAG] Tool ${name} failed:`, response.status, errorText);
              functionResponses.push({
                id,
                name,
                response: {
                  error: `Failed to execute ${name}: ${response.status} ${response.statusText}`
                }
              });
            }
          } catch (toolError) {
            console.error(`[RAG] Error executing tool ${name}:`, toolError);
            functionResponses.push({
              id,
              name,
              response: {
                error: `Error executing ${name}: ${toolError instanceof Error ? toolError.message : String(toolError)}`
              }
            });
          }
        }

        // Send tool responses back to Gemini
        if (functionResponses.length > 0) {
          console.log('[RAG] Sending tool responses to Gemini:', functionResponses);
          try {
            await liveAPI.client.sendToolResponse({ functionResponses });
            console.log('[RAG] ✅ Tool responses sent successfully:', functionResponses.length);
          } catch (sendError) {
            console.error('[RAG] ❌ Failed to send tool responses:', sendError);
          }
        } else {
          console.warn('[RAG] No function responses to send');
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
  }, [liveAPI.client, ragToolsEnabled, ragToolsHealthy]);

  return {
    ...liveAPI,
    setConfig: setConfigWithRAG,
    ragToolsEnabled,
    ragToolsHealthy,
    setRAGToolsEnabled,
  };
}
