/**
 * Enhanced Live API Hook with RAG Tools Integration
 * 
 * This hook extends the original useLiveAPI with RAG tool support
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GenAILiveClient } from "../lib/genai-live-client";
import { LiveClientOptions } from "../lib/types";
import { AudioStreamer } from "../lib/audio-streamer";
import { audioContext } from "../lib/utils";
import VolMeterWorket from "../lib/worklets/vol-meter";
import { LiveConnectConfig } from "@google/genai";
import { useRAGTools } from "./use-rag-tools";
import { ragToolsClient } from "../lib/rag-tools-client";

export type UseLiveAPIWithRAGResults = {
  client: GenAILiveClient;
  setConfig: (config: LiveConnectConfig) => void;
  config: LiveConnectConfig;
  model: string;
  setModel: (model: string) => void;
  connected: boolean;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  volume: number;
  ragToolsEnabled: boolean;
  ragToolsHealthy: boolean;
  setRAGToolsEnabled: (enabled: boolean) => void;
};

export function useLiveAPIWithRAG(options: LiveClientOptions): UseLiveAPIWithRAGResults {
  const client = useMemo(() => new GenAILiveClient(options), [options]);
  const audioStreamerRef = useRef<AudioStreamer | null>(null);

  const [model, setModel] = useState<string>("models/gemini-2.0-flash-exp");
  const [config, setConfig] = useState<LiveConnectConfig>({});
  const [connected, setConnected] = useState(false);
  const [volume, setVolume] = useState(0);
  const [ragToolsEnabled, setRAGToolsEnabled] = useState(true);

  // Initialize RAG tools
  const { tools, toolsLoaded, toolsHealthy } = useRAGTools({
    client,
    enabled: ragToolsEnabled,
  });

  // Register audio for streaming server -> speakers
  useEffect(() => {
    if (!audioStreamerRef.current) {
      audioContext({ id: "audio-out" }).then((audioCtx: AudioContext) => {
        audioStreamerRef.current = new AudioStreamer(audioCtx);
        audioStreamerRef.current
          .addWorklet<any>("vumeter-out", VolMeterWorket, (ev: any) => {
            setVolume(ev.data.volume);
          })
          .then(() => {
            // Successfully added worklet
          });
      });
    }
  }, [audioStreamerRef]);

  useEffect(() => {
    const onOpen = () => {
      setConnected(true);
    };

    const onClose = () => {
      setConnected(false);
    };

    const onError = (error: ErrorEvent) => {
      console.error("error", error);
    };

    const stopAudioStreamer = () => audioStreamerRef.current?.stop();

    const onAudio = (data: ArrayBuffer) =>
      audioStreamerRef.current?.addPCM16(new Uint8Array(data));

    client
      .on("error", onError)
      .on("open", onOpen)
      .on("close", onClose)
      .on("interrupted", stopAudioStreamer)
      .on("audio", onAudio);

    return () => {
      client
        .off("error", onError)
        .off("open", onOpen)
        .off("close", onClose)
        .off("interrupted", stopAudioStreamer)
        .off("audio", onAudio)
        .disconnect();
    };
  }, [client]);

  const connect = useCallback(async () => {
    if (!config) {
      throw new Error("config has not been set");
    }

    // Prepare config with RAG tools if enabled
    let finalConfig = { ...config };

    if (ragToolsEnabled && toolsLoaded && tools.length > 0) {
      console.log('[RAG] Connecting with RAG tools:', tools.map(t => t.name));
      
      // Add tools to config - convert to proper Gemini format
      finalConfig.tools = tools.map(tool => ({
        functionDeclarations: [
          {
            name: tool.name,
            description: tool.description,
            parameters: {
              type: tool.parameters.type as any,
              properties: tool.parameters.properties,
              required: tool.parameters.required,
            } as any,
          }
        ]
      })) as any;

      console.log('[RAG] Tools registered with Gemini:', finalConfig.tools);
    } else {
      console.log('[RAG] Connecting without RAG tools');
    }

    client.disconnect();
    await client.connect(model, finalConfig);
  }, [client, config, model, ragToolsEnabled, toolsLoaded, tools]);

  const disconnect = useCallback(async () => {
    client.disconnect();
    setConnected(false);
  }, [setConnected, client]);

  return {
    client,
    config,
    setConfig,
    model,
    setModel,
    connected,
    connect,
    disconnect,
    volume,
    ragToolsEnabled,
    ragToolsHealthy: toolsHealthy,
    setRAGToolsEnabled,
  };
}

