import { StyleSheet, View, Text, TouchableOpacity, ScrollView, Platform } from 'react-native';
import { useState, useEffect, useRef } from 'react';
import { useLiveAPIWithRAG } from '../../hooks/use-live-api-with-rag';
import Constants from 'expo-constants';
import { AudioRecorder } from '../../lib/audio-recorder';
import { useWebcam } from '../../hooks/use-webcam';
import { useScreenCapture } from '../../hooks/use-screen-capture';

// @ts-ignore - для web video элемента
declare global {
  namespace JSX {
    interface IntrinsicElements {
      video: any;
    }
  }
}

const API_KEY = Constants.expoConfig?.extra?.GEMINI_API_KEY || process.env.EXPO_PUBLIC_GEMINI_API_KEY;

type Language = 'ru' | 'en';

function LiveChatContent() {
  const apiOptions = { apiKey: API_KEY || '' };
  const { connected, connect, disconnect, client, volume, setConfig, ragToolsEnabled, ragToolsHealthy, setRAGToolsEnabled } = useLiveAPIWithRAG(apiOptions);
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'ai'}>>([]);
  const [isMicOn, setIsMicOn] = useState(false);
  const [language, setLanguage] = useState<Language>('en');
  const audioRecorderRef = useRef<AudioRecorder | null>(null);
  const webcam = useWebcam();
  const screenCapture = useScreenCapture();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const previewVideoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoIntervalRef = useRef<number | null>(null);

  // Language instructions
  const languageInstructions = {
    ru: `You are a helpful AI assistant with access to company knowledge and web search. IMPORTANT: You MUST respond ONLY in RUSSIAN language. Always speak Russian, never use English in your responses. Use natural Russian speech patterns.

AVAILABLE TOOLS:
- vector_search: Search company internal documents and policies
- web_search: Search the web for current information

When answering questions:
1. Use vector_search for company-related questions
2. Use web_search for current events or general information
3. Combine results when needed
4. Always cite your sources`,
    en: `You are a helpful AI assistant with multimodal capabilities and access to specialized tools. You can see through camera, view screen shares, and listen to audio.

AVAILABLE TOOLS:
- vector_search: Search company internal documents, policies, and knowledge base
- web_search: Search the web for current information, news, and public data

INSTRUCTIONS:
1. When user asks about company information, policies, or internal documents → Use vector_search
2. When user asks about current events, news, or general knowledge → Use web_search
3. When you need both internal and external information → Use both tools
4. Always cite your sources and be specific about where information came from
5. Respond naturally and helpfully in English`,
  };

  // UI translations
  const translations = {
    ru: {
      title: 'Gemini Live Чат',
      subtitle: 'Мультимодальный AI Ассистент',
      connect: 'Подключить',
      live: 'В ЭФИРЕ',
      greetingMessage: 'Привет! Я Gemini AI с мультимодальными возможностями. Включи микрофон, камеру или покажи свой экран чтобы начать! 🎤📹🖥️',
      connected: 'Подключено к Gemini Live API! 🚀',
      disconnected: 'Отключено от Gemini',
      connectFirst: 'Сначала подключитесь к Gemini',
      emptyStateText: 'Нажми "Подключить" чтобы начать',
      emptyStateSubtext: 'После подключения используй кнопки ниже:',
      emptyStateButtons: '🎤 Голос • 📹 Камера • 🖥️ Экран',
      apiKeyMissing: '⚠️ API ключ не найден!',
      micOn: '🎤 Микрофон включен - Говори!',
      micOff: '🔇 Микрофон выключен',
      cameraOn: '📹 Камера включена - AI видит тебя!',
      cameraOff: '📷 Камера выключена',
      screenOn: '🖥️ Показ экрана включен - AI видит твой экран!',
      screenOff: '🖥️ Показ экрана остановлен',
      microphone: 'Микрофон',
      camera: 'Камера',
      screen: 'Экран',
      cameraPreview: '📹 Превью Камеры',
      screenPreview: '🖥️ Превью Экрана',
      volume: 'Громкость',
    },
    en: {
      title: 'Gemini Live Chat',
      subtitle: 'Multimodal AI Assistant',
      connect: 'Connect',
      live: 'LIVE',
      greetingMessage: 'Hello! I\'m Gemini AI with multimodal capabilities. Turn on your microphone, camera, or share your screen to start! 🎤📹🖥️',
      connected: 'Connected to Gemini Live API! 🚀',
      disconnected: 'Disconnected from Gemini',
      connectFirst: 'Please connect to Gemini first',
      emptyStateText: 'Press "Connect" to start',
      emptyStateSubtext: 'After connecting, use the buttons below:',
      emptyStateButtons: '🎤 Voice • 📹 Camera • 🖥️ Screen Share',
      apiKeyMissing: '⚠️ API key not found!',
      micOn: '🎤 Microphone is ON - Speak now!',
      micOff: '🔇 Microphone turned off',
      cameraOn: '📹 Camera is ON - AI can see you!',
      cameraOff: '📷 Camera turned off',
      screenOn: '🖥️ Screen sharing is ON - AI can see your screen!',
      screenOff: '🖥️ Screen sharing stopped',
      microphone: 'Microphone',
      camera: 'Camera',
      screen: 'Screen',
      cameraPreview: '📹 Camera Preview',
      screenPreview: '🖥️ Screen Preview',
      volume: 'Volume',
    },
  };

  const t = translations[language];

  // Setup config for Gemini with language
  useEffect(() => {
    const systemInstruction = languageInstructions[language];
    console.log('Setting language to:', language, 'Instruction:', systemInstruction);
    setConfig({
      systemInstruction: {
        parts: [{ text: systemInstruction }]
      }
    });
  }, [setConfig, language]);

  // Update preview video when stream changes
  useEffect(() => {
    if (Platform.OS === 'web') {
      const currentStream = webcam.stream || screenCapture.stream;
      console.log('Stream changed:', currentStream ? 'Stream available' : 'No stream', 'Preview ref:', !!previewVideoRef.current);
      
      if (currentStream && previewVideoRef.current) {
        console.log('Setting stream to preview video');
        previewVideoRef.current.srcObject = currentStream;
        previewVideoRef.current.play()
          .then(() => console.log('Video playing!'))
          .catch(err => console.log('Video play error:', err));
      } else if (!currentStream && previewVideoRef.current) {
        previewVideoRef.current.srcObject = null;
      }
    }
  }, [webcam.stream, screenCapture.stream]);

  // Listen for AI responses
  useEffect(() => {
    const onContent = (content: any) => {
      console.log('AI Response:', content);
      if (content.modelTurn?.parts) {
        content.modelTurn.parts.forEach((part: any) => {
          if (part.text) {
            setMessages(prev => [...prev, {
              id: Date.now().toString() + Math.random(),
              text: part.text,
              sender: 'ai'
            }]);
          }
        });
      }
    };

    const onSetupComplete = () => {
      console.log('Setup complete!');
    };

    client.on('content', onContent);
    client.on('setupcomplete', onSetupComplete);
    
    return () => {
      client.off('content', onContent);
      client.off('setupcomplete', onSetupComplete);
    };
  }, [client]);

  // Handle connection
  const handleConnect = async () => {
    try {
      if (connected) {
        await disconnect();
        stopAllStreams();
        setMessages([]);
        alert(t.disconnected);
      } else {
        await connect();
        setMessages([{
          id: '1',
          text: t.greetingMessage,
          sender: 'ai'
        }]);
        alert(t.connected);
      }
    } catch (error) {
      console.error('Connection error:', error);
      alert('Error: Check your API key');
    }
  };

  // Stop all active streams
  const stopAllStreams = () => {
    if (isMicOn) {
      audioRecorderRef.current?.stop();
      audioRecorderRef.current = null;
      setIsMicOn(false);
    }
    if (webcam.isStreaming) {
      stopVideoStream();
      webcam.stop();
    }
    if (screenCapture.isStreaming) {
      stopVideoStream();
      screenCapture.stop();
    }
  };

  // Toggle microphone
  const toggleMic = async () => {
    if (!connected) {
      alert(t.connectFirst);
      return;
    }

    if (isMicOn) {
      // Stop recording
      audioRecorderRef.current?.stop();
      audioRecorderRef.current = null;
      setIsMicOn(false);
      alert(t.micOff);
    } else {
      // Start recording
      try {
        const recorder = new AudioRecorder(16000);
        audioRecorderRef.current = recorder;

        recorder.on('data', (base64Data: string) => {
          if (connected) {
            client.sendRealtimeInput([{
              mimeType: 'audio/pcm',
              data: base64Data
            }]);
          }
        });

        await recorder.start();
        setIsMicOn(true);
        alert(t.micOn);
      } catch (error) {
        console.error('Microphone error:', error);
        alert('Error: Could not access microphone');
      }
    }
  };

  // Start sending video frames
  const startVideoStream = (stream: MediaStream) => {
    if (Platform.OS !== 'web') return;

    const video = document.createElement('video');
    video.srcObject = stream;
    video.play();
    videoRef.current = video;

    const canvas = document.createElement('canvas');
    canvasRef.current = canvas;
    const ctx = canvas.getContext('2d');

    // Send frames every 1 second
    videoIntervalRef.current = window.setInterval(() => {
      if (!video.videoWidth || !video.videoHeight) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx?.drawImage(video, 0, 0);

      canvas.toBlob((blob) => {
        if (blob) {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64data = (reader.result as string).split(',')[1];
            if (connected && base64data) {
              client.sendRealtimeInput([{
                mimeType: 'image/jpeg',
                data: base64data
              }]);
            }
          };
          reader.readAsDataURL(blob);
        }
      }, 'image/jpeg', 0.7);
    }, 1000);
  };

  // Stop video stream
  const stopVideoStream = () => {
    if (videoIntervalRef.current) {
      clearInterval(videoIntervalRef.current);
      videoIntervalRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
      videoRef.current = null;
    }
    if (previewVideoRef.current) {
      previewVideoRef.current.srcObject = null;
    }
  };

  // Toggle webcam
  const toggleCamera = async () => {
    if (!connected) {
      alert(t.connectFirst);
      return;
    }

    if (Platform.OS !== 'web') {
      alert('Webcam is only available on web platform');
      return;
    }

    if (webcam.isStreaming) {
      stopVideoStream();
      webcam.stop();
      alert(t.cameraOff);
    } else {
      try {
        // Stop screen share if active
        if (screenCapture.isStreaming) {
          stopVideoStream();
          screenCapture.stop();
        }

        const stream = await webcam.start();
        startVideoStream(stream);
        alert(t.cameraOn);
      } catch (error) {
        console.error('Camera error:', error);
        alert('Error: Could not access camera');
      }
    }
  };

  // Toggle screen share
  const toggleScreenShare = async () => {
    if (!connected) {
      alert(t.connectFirst);
      return;
    }

    if (Platform.OS !== 'web') {
      alert('Screen sharing is only available on web platform');
      return;
    }

    if (screenCapture.isStreaming) {
      stopVideoStream();
      screenCapture.stop();
      alert(t.screenOff);
    } else {
      try {
        // Stop webcam if active
        if (webcam.isStreaming) {
          stopVideoStream();
          webcam.stop();
        }

        const stream = await screenCapture.start();
        startVideoStream(stream);
        alert(t.screenOn);
      } catch (error) {
        console.error('Screen share error:', error);
        alert('Error: Could not capture screen');
      }
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>{t.title}</Text>
          <Text style={styles.headerSubtitle}>{t.subtitle}</Text>
        </View>
        
        <View style={styles.headerRight}>
          {/* RAG Tools Indicator */}
          {ragToolsEnabled && (
            <View style={[styles.ragIndicator, ragToolsHealthy ? styles.ragIndicatorHealthy : styles.ragIndicatorError]}>
              <Text style={styles.ragIndicatorText}>
                {ragToolsHealthy ? '🧠 RAG' : '⚠️ RAG'}
              </Text>
            </View>
          )}
          
          {/* Language Switcher */}
          <View style={styles.languageSwitcher}>
            <TouchableOpacity 
              style={[styles.languageButton, language === 'en' && styles.languageButtonActive]}
              onPress={() => setLanguage('en')}
            >
              <Text style={[styles.languageButtonText, language === 'en' && styles.languageButtonTextActive]}>
                EN 🇺🇸
              </Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.languageButton, language === 'ru' && styles.languageButtonActive]}
              onPress={() => setLanguage('ru')}
            >
              <Text style={[styles.languageButtonText, language === 'ru' && styles.languageButtonTextActive]}>
                RU 🇷🇺
              </Text>
            </TouchableOpacity>
          </View>
          
          <TouchableOpacity 
            style={[styles.connectButton, connected && styles.connectButtonActive]}
            onPress={handleConnect}
          >
            <Text style={styles.connectButtonText}>
              {connected ? `● ${t.live}` : `○ ${t.connect}`}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
      
      <ScrollView style={styles.messagesContainer}>
        {/* Video Preview */}
        {Platform.OS === 'web' && (webcam.isStreaming || screenCapture.isStreaming) && (
          <View style={styles.videoPreviewContainer}>
            <video
              ref={(ref) => { 
                previewVideoRef.current = ref;
                console.log('Video ref set:', !!ref);
              }}
              autoPlay
              playsInline
              muted
              onLoadedMetadata={(e) => {
                console.log('Video metadata loaded', e.currentTarget.videoWidth, 'x', e.currentTarget.videoHeight);
              }}
              onPlay={() => console.log('Video started playing')}
              onError={(e) => console.error('Video error:', e)}
              style={{
                width: '100%',
                maxWidth: 800,
                minHeight: 400,
                borderRadius: 16,
                backgroundColor: '#000',
                transform: webcam.isStreaming ? 'scaleX(-1)' : 'scaleX(1)', // Зеркалим камеру
              }}
            />
            <View style={styles.videoLabel}>
              <Text style={styles.videoLabelText}>
                {webcam.isStreaming ? t.cameraPreview : t.screenPreview}
              </Text>
            </View>
          </View>
        )}

        {messages.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>🤖</Text>
            <Text style={styles.emptyStateText}>
              {t.emptyStateText}
            </Text>
            <Text style={styles.emptyStateSubtext}>
              {t.emptyStateSubtext}
            </Text>
            <Text style={styles.emptyStateSubtext}>
              {t.emptyStateButtons}
            </Text>
            {!API_KEY && (
              <Text style={styles.errorText}>{t.apiKeyMissing}</Text>
            )}
          </View>
        ) : (
          messages.map((msg) => (
            <View 
              key={msg.id} 
              style={[styles.messageBubble, msg.sender === 'user' ? styles.userBubble : styles.aiBubble]}
            >
              <Text style={styles.messageText}>{msg.text}</Text>
            </View>
          ))
        )}
      </ScrollView>

      {/* Active indicator */}
      {connected && (isMicOn || webcam.isStreaming || screenCapture.isStreaming) && (
        <View style={styles.activeIndicator}>
          {isMicOn && <Text style={styles.activeText}>🎤 {t.microphone}</Text>}
          {webcam.isStreaming && <Text style={styles.activeText}>📹 {t.camera}</Text>}
          {screenCapture.isStreaming && <Text style={styles.activeText}>🖥️ {t.screen}</Text>}
          {isMicOn && <Text style={styles.volumeText}>{t.volume}: {Math.round(volume * 100)}%</Text>}
        </View>
      )}

      {/* Controls */}
      <View style={styles.controlsContainer}>
        <TouchableOpacity 
          style={[styles.controlButton, isMicOn && styles.controlButtonActive]}
          disabled={!connected}
          onPress={toggleMic}
        >
          <Text style={styles.controlButtonIcon}>{isMicOn ? '🎤' : '🔇'}</Text>
          <Text style={styles.controlButtonText}>{t.microphone}</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.controlButton, webcam.isStreaming && styles.controlButtonActive]}
          disabled={!connected || Platform.OS !== 'web'}
          onPress={toggleCamera}
        >
          <Text style={styles.controlButtonIcon}>{webcam.isStreaming ? '📹' : '📷'}</Text>
          <Text style={styles.controlButtonText}>{t.camera}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.controlButton, screenCapture.isStreaming && styles.controlButtonActive]}
          disabled={!connected || Platform.OS !== 'web'}
          onPress={toggleScreenShare}
        >
          <Text style={styles.controlButtonIcon}>🖥️</Text>
          <Text style={styles.controlButtonText}>{t.screen}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

export default function LiveChatScreen() {
  return <LiveChatContent />;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a' },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    padding: 16, 
    backgroundColor: '#1a1a1a', 
    borderBottomWidth: 1, 
    borderBottomColor: '#333' 
  },
  headerLeft: {
    flexDirection: 'column',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  headerSubtitle: { fontSize: 12, color: '#888', marginTop: 2 },
  languageSwitcher: {
    flexDirection: 'row',
    backgroundColor: '#333',
    borderRadius: 20,
    padding: 4,
    gap: 4,
  },
  languageButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  languageButtonActive: {
    backgroundColor: '#4CAF50',
  },
  languageButtonText: {
    color: '#888',
    fontSize: 12,
    fontWeight: '600',
  },
  languageButtonTextActive: {
    color: '#fff',
  },
  ragIndicator: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#333',
  },
  ragIndicatorHealthy: {
    backgroundColor: '#4CAF50',
  },
  ragIndicatorError: {
    backgroundColor: '#f44336',
  },
  ragIndicatorText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  connectButton: { paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#333', borderRadius: 20 },
  connectButtonActive: { backgroundColor: '#f44336' },
  connectButtonText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  messagesContainer: { flex: 1, padding: 16 },
  videoPreviewContainer: {
    alignItems: 'center',
    marginBottom: 20,
    padding: 16,
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  videoLabel: {
    marginTop: 12,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#4CAF50',
    borderRadius: 20,
  },
  videoLabelText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 80 },
  emptyIcon: { fontSize: 64, marginBottom: 16 },
  emptyStateText: { fontSize: 18, color: '#fff', textAlign: 'center', marginBottom: 8, fontWeight: '600' },
  emptyStateSubtext: { fontSize: 14, color: '#888', textAlign: 'center', marginTop: 4 },
  errorText: { fontSize: 14, color: '#f44336', textAlign: 'center', marginTop: 16, fontWeight: 'bold' },
  messageBubble: { maxWidth: '80%', padding: 12, borderRadius: 16, marginBottom: 12 },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#2196F3' },
  aiBubble: { alignSelf: 'flex-start', backgroundColor: '#333' },
  messageText: { color: '#fff', fontSize: 16, lineHeight: 22 },
  activeIndicator: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#1a1a1a',
    borderTopWidth: 1,
    borderTopColor: '#333',
    gap: 16,
  },
  activeText: { color: '#4CAF50', fontSize: 14, fontWeight: '600' },
  volumeText: { color: '#888', fontSize: 12 },
  controlsContainer: { 
    flexDirection: 'row', 
    justifyContent: 'space-around', 
    padding: 16, 
    backgroundColor: '#1a1a1a', 
    borderTopWidth: 1, 
    borderTopColor: '#333' 
  },
  controlButton: { 
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 16,
    backgroundColor: '#333',
    opacity: 0.5,
    minWidth: 100,
  },
  controlButtonActive: { 
    opacity: 1, 
    backgroundColor: '#4CAF50',
  },
  controlButtonIcon: { fontSize: 28, marginBottom: 4 },
  controlButtonText: { color: '#fff', fontSize: 12, fontWeight: '600' },
});
