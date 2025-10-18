/**
 * RAG Tools Client for Gemini Live Integration
 * 
 * This client handles communication with the backend RAG system,
 * allowing Gemini Live to call vector_search and web_search tools.
 */

import { Part } from "@google/genai";
import { getBackendURL } from "./config";

export interface ToolCallRequest {
  tool_name: string;
  parameters: Record<string, any>;
}

export interface ToolCallResponse {
  tool_name: string;
  result: string;
  success: boolean;
  error?: string;
}

export interface FunctionDeclaration {
  name: string;
  description: string;
  parameters: {
    type: string;
    properties: Record<string, any>;
    required: string[];
  };
}

/**
 * Client for interacting with the backend RAG tools
 */
export class RAGToolsClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getBackendURL();
    console.log('[RAG Tools Client] Initialized with URL:', this.baseUrl);
  }

  /**
   * Get function declarations from the backend
   */
  async getFunctionDeclarations(): Promise<FunctionDeclaration[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/rag/live/function-declarations`);
      if (!response.ok) {
        throw new Error(`Failed to get function declarations: ${response.statusText}`);
      }
      const data = await response.json();
      return data.functions || [];
    } catch (error) {
      console.error('Error fetching function declarations:', error);
      return [];
    }
  }

  /**
   * Execute a tool call on the backend
   */
  async executeToolCall(toolName: string, parameters: Record<string, any>): Promise<ToolCallResponse> {
    try {
      console.log(`[RAG Tools] Executing tool: ${toolName}`, parameters);
      
      const response = await fetch(`${this.baseUrl}/api/rag/live/tool-call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tool_name: toolName,
          parameters,
        }),
      });

      if (!response.ok) {
        throw new Error(`Tool call failed: ${response.statusText}`);
      }

      const result = await response.json();
      console.log(`[RAG Tools] Tool result:`, result);
      return result;
    } catch (error) {
      console.error(`[RAG Tools] Error executing tool ${toolName}:`, error);
      return {
        tool_name: toolName,
        result: '',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Check health status of RAG tools
   */
  async checkHealth(): Promise<{ status: string; tools: any }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/rag/live/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('[RAG Tools] Health check error:', error);
      return {
        status: 'error',
        tools: {},
      };
    }
  }
}

/**
 * Convert backend function declarations to Gemini-compatible tools
 */
export function convertToGeminiTools(declarations: FunctionDeclaration[]): any[] {
  return declarations.map(decl => ({
    functionDeclarations: [
      {
        name: decl.name,
        description: decl.description,
        parameters: decl.parameters,
      }
    ]
  }));
}

/**
 * Create a default RAG tools client
 */
export const ragToolsClient = new RAGToolsClient();

