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
    // Create a stable config string to prevent infinite loops
    const configString = JSON.stringify(newConfig);
    
    if (lastConfigRef.current === configString) {
      console.log('[RAG] Config unchanged, skipping update');
      return;
    }
    
    lastConfigRef.current = configString;

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
              },
              {
                name: "transfer_money",
                description: "Transfer money from one account to another. Use this when user wants to send money to another account or person.",
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
                description: "Deposit money into a user's account. Use this when user wants to add money to their account.",
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
                description: "Withdraw money from a user's account. Use this when user wants to take money out of their account.",
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
                description: "Get all accounts belonging to the user with their balances. Use this when user asks about their accounts or wants to see their financial status.",
                parameters: {
                  type: "object" as any,
                  properties: {},
                  required: []
                }
              },
              {
                name: "get_account_balance",
                description: "Get the current balance of a specific account. Use this when user asks about balance of a specific account.",
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
