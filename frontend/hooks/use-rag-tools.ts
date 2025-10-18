/**
 * Hook for integrating RAG tools with Gemini Live
 * 
 * This hook handles tool calls from Gemini and routes them to the backend
 */

import { useEffect, useCallback, useState } from 'react';
import { GenAILiveClient } from '../lib/genai-live-client';
import { ragToolsClient, FunctionDeclaration } from '../lib/rag-tools-client';
import { LiveServerToolCall } from '@google/genai';

export interface UseRAGToolsOptions {
  client: GenAILiveClient;
  enabled?: boolean;
}

export interface UseRAGToolsResults {
  tools: FunctionDeclaration[];
  toolsLoaded: boolean;
  toolsHealthy: boolean;
  handleToolCall: (toolCall: LiveServerToolCall) => Promise<void>;
}

/**
 * Hook to integrate RAG tools with Gemini Live
 */
export function useRAGTools({ client, enabled = true }: UseRAGToolsOptions): UseRAGToolsResults {
  const [tools, setTools] = useState<FunctionDeclaration[]>([]);
  const [toolsLoaded, setToolsLoaded] = useState(false);
  const [toolsHealthy, setToolsHealthy] = useState(false);

  // Load tools from backend
  useEffect(() => {
    if (!enabled) return;

    const loadTools = async () => {
      try {
        console.log('[RAG Tools] Loading function declarations from backend...');
        
        // Get function declarations
        const declarations = await ragToolsClient.getFunctionDeclarations();
        console.log('[RAG Tools] Loaded tools:', declarations.map(d => d.name));
        setTools(declarations);
        setToolsLoaded(true);

        // Check health
        const health = await ragToolsClient.checkHealth();
        console.log('[RAG Tools] Health status:', health);
        setToolsHealthy(health.status === 'healthy');
      } catch (error) {
        console.error('[RAG Tools] Error loading tools:', error);
        setToolsLoaded(false);
        setToolsHealthy(false);
      }
    };

    loadTools();
  }, [enabled]);

  // Handle tool calls from Gemini
  const handleToolCall = useCallback(async (toolCall: LiveServerToolCall) => {
    if (!toolCall.functionCalls || toolCall.functionCalls.length === 0) {
      console.warn('[RAG Tools] No function calls in tool call');
      return;
    }

    console.log('[RAG Tools] Received tool call:', toolCall);

    // Process each function call
    const responses = await Promise.all(
      toolCall.functionCalls.map(async (fc) => {
        const functionName = fc.name;
        const args = fc.args || {};

        console.log(`[RAG Tools] Calling ${functionName} with args:`, args);

        try {
          // Execute tool on backend
          const result = await ragToolsClient.executeToolCall(functionName, args);

          if (!result.success) {
            console.error(`[RAG Tools] Tool ${functionName} failed:`, result.error);
            return {
              name: functionName,
              id: fc.id,
              response: {
                error: result.error || 'Tool execution failed',
              },
            };
          }

          console.log(`[RAG Tools] Tool ${functionName} succeeded`);
          return {
            name: functionName,
            id: fc.id,
            response: {
              output: result.result,
            },
          };
        } catch (error) {
          console.error(`[RAG Tools] Error calling ${functionName}:`, error);
          return {
            name: functionName,
            id: fc.id,
            response: {
              error: error instanceof Error ? error.message : 'Unknown error',
            },
          };
        }
      })
    );

    // Send responses back to Gemini
    console.log('[RAG Tools] Sending tool responses back to Gemini:', responses);
    client.sendToolResponse({
      functionResponses: responses,
    });
  }, [client]);

  // Register tool call handler
  useEffect(() => {
    if (!enabled || !toolsLoaded) return;

    console.log('[RAG Tools] Registering tool call handler');
    client.on('toolcall', handleToolCall);

    return () => {
      console.log('[RAG Tools] Unregistering tool call handler');
      client.off('toolcall', handleToolCall);
    };
  }, [client, enabled, toolsLoaded, handleToolCall]);

  return {
    tools,
    toolsLoaded,
    toolsHealthy,
    handleToolCall,
  };
}

