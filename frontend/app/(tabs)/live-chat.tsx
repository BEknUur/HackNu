import { StyleSheet, View, Text, TouchableOpacity, ScrollView, Platform, Dimensions } from 'react-native';
import { useState, useEffect, useRef } from 'react';
import { useLiveAPIWithRAG } from '@/hooks/use-live-api-with-rag';
import Constants from 'expo-constants';
import { AudioRecorder } from '@/lib/audio-recorder';
import { useWebcam } from '@/hooks/use-webcam';
import { useScreenCapture } from '@/hooks/use-screen-capture';
import { ZamanColors } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

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
  const { connected, connect, disconnect, client, volume, setConfig, ragToolsEnabled, ragToolsHealthy } = useLiveAPIWithRAG(apiOptions);
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'ai'}>>([]);
  const [isMicOn, setIsMicOn] = useState(false);
  const [language, setLanguage] = useState<Language>('en');
  const [screenWidth, setScreenWidth] = useState(Dimensions.get('window').width);
  const audioRecorderRef = useRef<AudioRecorder | null>(null);
  const webcam = useWebcam();
  const screenCapture = useScreenCapture();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const previewVideoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoIntervalRef = useRef<number | null>(null);

  // Listen for screen size changes
  useEffect(() => {
    const subscription = Dimensions.addEventListener('change', ({ window }) => {
      setScreenWidth(window.width);
    });
    return () => subscription?.remove();
  }, []);

  const isMobile = screenWidth < 768;

  // Language instructions
  const languageInstructions = {
    ru: `You are a ZAMAN BANK AI assistant with access to banking tools and information. IMPORTANT: You MUST respond ONLY in RUSSIAN language. Always speak Russian, never use English in your responses. Use natural Russian speech patterns.

AVAILABLE TOOLS:
- vector_search: Search company internal documents and policies
- web_search: Search the web for current information
- transfer_money: Transfer money between accounts
- deposit_money: Add money to an account
- withdraw_money: Remove money from an account
- get_my_accounts: Show all user accounts with balances
- get_account_balance: Check balance of specific account

BANKING OPERATIONS:
1. When user asks to transfer/send money → Use transfer_money
2. When user asks to deposit money → Use deposit_money
3. When user asks to withdraw money → Use withdraw_money
4. When user asks about accounts/balance → Use get_my_accounts or get_account_balance
5. For company questions → Use vector_search
6. For general information → Use web_search

Always execute banking operations immediately when requested!`,
    en: `You are a ZAMAN BANK AI assistant with multimodal capabilities and access to banking tools. You can see through camera, view screen shares, listen to audio, and execute financial transactions.

AVAILABLE TOOLS:
- vector_search: Search company internal documents, policies, and knowledge base
- web_search: Search the web for current information, news, and public data
- transfer_money: Transfer money between accounts
- deposit_money: Add money to an account
- withdraw_money: Remove money from an account
- get_my_accounts: Show all user accounts with balances
- get_account_balance: Check balance of specific account

BANKING OPERATIONS:
1. When user asks to transfer/send money → Use transfer_money
2. When user asks to deposit money → Use deposit_money
3. When user asks to withdraw money → Use withdraw_money
4. When user asks about accounts/balance → Use get_my_accounts or get_account_balance
5. For company questions → Use vector_search
6. For general information → Use web_search

EXAMPLES:
- "Send 50000 tenge to account 2" → Use transfer_money
- "Deposit 100000 KZT to my account" → Use deposit_money
- "Show my accounts" → Use get_my_accounts
- "What's my balance?" → Use get_my_accounts

Always execute banking operations immediately when requested! Be helpful and efficient.`,
  };

  // UI translations
  const translations = {
    ru: {
      title: 'Gemini Live Chat',
      subtitle: 'Multimodal AI Assistant',
      connect: 'Подключить',
      live: 'LIVE',
      greetingMessage: 'Привет! Я Gemini AI с мультимодальными возможностями. Включи микрофон, камеру или покажи свой экран чтобы начать!',
      connected: 'Подключено к Gemini Live API',
      disconnected: 'Отключено от Gemini',
      connectFirst: 'Сначала подключитесь к Gemini',
      emptyStateText: 'Нажми "Подключить" чтобы начать',
      emptyStateSubtext: 'После подключения используй кнопки ниже',
      emptyStateButtons: 'Голос • Камера • Экран',
      apiKeyMissing: 'API ключ не найден',
      micOn: 'Микрофон включен - Говори!',
      micOff: 'Микрофон выключен',
      cameraOn: 'Камера включена - AI видит тебя!',
      cameraOff: 'Камера выключена',
      screenOn: 'Показ экрана включен - AI видит твой экран!',
      screenOff: 'Показ экрана остановлен',
      microphone: 'Microphone',
      camera: 'Camera',
      screen: 'Screen',
      cameraPreview: 'Camera Preview',
      screenPreview: 'Screen Preview',
      volume: 'Volume',
    },
    en: {
      title: 'Gemini Live Chat',
      subtitle: 'Multimodal AI Assistant',
      connect: 'Connect',
      live: 'LIVE',
      greetingMessage: 'Hello! I\'m Gemini AI with multimodal capabilities. Turn on your microphone, camera, or share your screen to start!',
      connected: 'Connected to Gemini Live API',
      disconnected: 'Disconnected from Gemini',
      connectFirst: 'Please connect to Gemini first',
      emptyStateText: 'Press "Connect" to start',
      emptyStateSubtext: 'After connecting, use the buttons below',
      emptyStateButtons: 'Voice • Camera • Screen Share',
      apiKeyMissing: 'API key not found',
      micOn: 'Microphone is ON - Speak now!',
      micOff: 'Microphone turned off',
      cameraOn: 'Camera is ON - AI can see you!',
      cameraOff: 'Camera turned off',
      screenOn: 'Screen sharing is ON - AI can see your screen!',
      screenOff: 'Screen sharing stopped',
      microphone: 'Microphone',
      camera: 'Camera',
      screen: 'Screen',
      cameraPreview: 'Camera Preview',
      screenPreview: 'Screen Preview',
      volume: 'Volume',
    },
  };

  const t = translations[language];

  // Setup config for Gemini with language and RAG tools
  useEffect(() => {
    const systemInstruction = languageInstructions[language];
    console.log('Setting language to:', language, 'Instruction:', systemInstruction);
    console.log('RAG Tools Status:', { ragToolsEnabled, ragToolsHealthy });
    
    // Create config that includes both system instruction AND preserves RAG tools
    const config = {
      systemInstruction: {
        parts: [{ text: systemInstruction }]
      }
    };
    
    // Let the RAG hook handle tool registration - don't override it
    setConfig(config);
  }, [language, ragToolsEnabled, ragToolsHealthy]); // Include RAG status in dependencies

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
        
        <View style={[styles.headerRight, isMobile && styles.headerRightMobile]}>
          {/* RAG Tools Indicator */}
          {ragToolsEnabled && !isMobile && (
            <View style={[styles.ragIndicator, ragToolsHealthy ? styles.ragIndicatorHealthy : styles.ragIndicatorError]}>
              <Ionicons 
                name={ragToolsHealthy ? "checkmark-circle" : "alert-circle"} 
                size={16} 
                color={ZamanColors.white} 
                style={{ marginRight: 6 }}
              />
              <Text style={[styles.ragIndicatorText, (ragToolsHealthy || !ragToolsHealthy) && styles.ragIndicatorTextActive]}>
                RAG
              </Text>
            </View>
          )}
          
          {/* Language Switcher */}
          <View style={[styles.languageSwitcher, isMobile && styles.languageSwitcherMobile]}>
            <TouchableOpacity 
              style={[styles.languageButton, language === 'en' && styles.languageButtonActive, isMobile && styles.languageButtonMobile]}
              onPress={() => setLanguage('en')}
            >
              <Text style={[styles.languageButtonText, language === 'en' && styles.languageButtonTextActive]}>
                EN
              </Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.languageButton, language === 'ru' && styles.languageButtonActive, isMobile && styles.languageButtonMobile]}
              onPress={() => setLanguage('ru')}
            >
              <Text style={[styles.languageButtonText, language === 'ru' && styles.languageButtonTextActive]}>
                RU
              </Text>
            </TouchableOpacity>
          </View>
          
          <TouchableOpacity 
            style={[styles.connectButton, connected && styles.connectButtonActive, isMobile && styles.connectButtonMobile]}
            onPress={handleConnect}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <View style={[styles.statusDot, connected && styles.statusDotActive]} />
              <Text style={styles.connectButtonText}>
                {connected ? t.live : t.connect}
              </Text>
            </View>
          </TouchableOpacity>
        </View>
      </View>
      
      {/* Mobile RAG Indicator Row */}
      {isMobile && ragToolsEnabled && (
        <View style={styles.mobileRagRow}>
          <View style={[styles.ragIndicator, styles.ragIndicatorMobile, ragToolsHealthy ? styles.ragIndicatorHealthy : styles.ragIndicatorError]}>
            <Ionicons 
              name={ragToolsHealthy ? "checkmark-circle" : "alert-circle"} 
              size={14} 
              color={ZamanColors.white} 
              style={{ marginRight: 4 }}
            />
            <Text style={[styles.ragIndicatorText, styles.ragIndicatorTextActive, { fontSize: 11 }]}>
              RAG Tools {ragToolsHealthy ? 'Active' : 'Error'}
            </Text>
          </View>
        </View>
      )}
      
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
            <View style={styles.emptyIconContainer}>
              <Ionicons name="chatbubbles-outline" size={64} color={ZamanColors.persianGreen} />
            </View>
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
              <View style={styles.errorContainer}>
                <Ionicons name="alert-circle-outline" size={18} color="#f44336" />
                <Text style={styles.errorText}>{t.apiKeyMissing}</Text>
              </View>
            )}
          </View>
        ) : (
          messages.map((msg) => (
            <View 
              key={msg.id} 
              style={[styles.messageBubble, msg.sender === 'user' ? styles.userBubble : styles.aiBubble]}
            >
              <Text style={[styles.messageText, msg.sender === 'user' && styles.userMessageText]}>
                {msg.text}
              </Text>
            </View>
          ))
        )}
      </ScrollView>

      {/* Active indicator */}
      {connected && (isMicOn || webcam.isStreaming || screenCapture.isStreaming) && (
        <View style={styles.activeIndicator}>
          {isMicOn && (
            <View style={styles.activeItem}>
              <Ionicons name="mic" size={16} color={ZamanColors.persianGreen} />
              <Text style={styles.activeText}>{t.microphone}</Text>
            </View>
          )}
          {webcam.isStreaming && (
            <View style={styles.activeItem}>
              <Ionicons name="videocam" size={16} color={ZamanColors.persianGreen} />
              <Text style={styles.activeText}>{t.camera}</Text>
            </View>
          )}
          {screenCapture.isStreaming && (
            <View style={styles.activeItem}>
              <Ionicons name="desktop" size={16} color={ZamanColors.persianGreen} />
              <Text style={styles.activeText}>{t.screen}</Text>
            </View>
          )}
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
          <Ionicons 
            name={isMicOn ? 'mic' : 'mic-off'} 
            size={28} 
            color={isMicOn ? ZamanColors.white : ZamanColors.black} 
            style={{ marginBottom: 8 }}
          />
          <Text style={[styles.controlButtonText, isMicOn && styles.controlButtonTextActive]}>
            {t.microphone}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.controlButton, webcam.isStreaming && styles.controlButtonActive]}
          disabled={!connected || Platform.OS !== 'web'}
          onPress={toggleCamera}
        >
          <Ionicons 
            name={webcam.isStreaming ? 'videocam' : 'videocam-off'} 
            size={28} 
            color={webcam.isStreaming ? ZamanColors.white : ZamanColors.black} 
            style={{ marginBottom: 8 }}
          />
          <Text style={[styles.controlButtonText, webcam.isStreaming && styles.controlButtonTextActive]}>
            {t.camera}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.controlButton, screenCapture.isStreaming && styles.controlButtonActive]}
          disabled={!connected || Platform.OS !== 'web'}
          onPress={toggleScreenShare}
        >
          <Ionicons 
            name={screenCapture.isStreaming ? 'desktop' : 'desktop-outline'} 
            size={28} 
            color={screenCapture.isStreaming ? ZamanColors.white : ZamanColors.black} 
            style={{ marginBottom: 8 }}
          />
          <Text style={[styles.controlButtonText, screenCapture.isStreaming && styles.controlButtonTextActive]}>
            {t.screen}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

export default function LiveChatScreen() {
  return <LiveChatContent />;
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: ZamanColors.white 
  },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingHorizontal: 24,
    paddingBottom: 20,
    backgroundColor: ZamanColors.white, 
    borderBottomWidth: 1, 
    borderBottomColor: ZamanColors.gray[200],
  },
  headerLeft: {
    flexDirection: 'column',
    flex: 1,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flexShrink: 0,
  },
  headerRightMobile: {
    gap: 8,
  },
  headerTitle: { 
    fontSize: 24, 
    fontWeight: '600', 
    color: ZamanColors.black,
    letterSpacing: 0.5,
  },
  headerSubtitle: { 
    fontSize: 13, 
    color: ZamanColors.gray[500], 
    marginTop: 4,
    fontWeight: '400',
  },
  languageSwitcher: {
    flexDirection: 'row',
    backgroundColor: ZamanColors.cloud,
    borderRadius: 12,
    padding: 3,
    gap: 4,
  },
  languageSwitcherMobile: {
    padding: 2,
    gap: 2,
    borderRadius: 10,
  },
  languageButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
  },
  languageButtonMobile: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  languageButtonActive: {
    backgroundColor: ZamanColors.persianGreen,
  },
  languageButtonText: {
    color: ZamanColors.gray[500],
    fontSize: 13,
    fontWeight: '500',
  },
  languageButtonTextActive: {
    color: ZamanColors.white,
  },
  ragIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: ZamanColors.cloud,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
  },
  ragIndicatorMobile: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 10,
  },
  ragIndicatorHealthy: {
    backgroundColor: ZamanColors.persianGreen,
    borderColor: ZamanColors.persianGreen,
  },
  ragIndicatorError: {
    backgroundColor: '#f44336',
    borderColor: '#f44336',
  },
  ragIndicatorText: {
    color: ZamanColors.black,
    fontSize: 12,
    fontWeight: '600',
  },
  ragIndicatorTextActive: {
    color: ZamanColors.white,
  },
  mobileRagRow: {
    paddingHorizontal: 24,
    paddingVertical: 8,
    backgroundColor: ZamanColors.white,
    borderBottomWidth: 1,
    borderBottomColor: ZamanColors.gray[200],
    alignItems: 'flex-start',
  },
  connectButton: { 
    paddingHorizontal: 24, 
    paddingVertical: 10, 
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
    borderRadius: 12,
  },
  connectButtonMobile: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 10,
  },
  connectButtonActive: { 
    backgroundColor: ZamanColors.solar,
    borderColor: ZamanColors.solar,
  },
  connectButtonText: { 
    color: ZamanColors.black, 
    fontWeight: '600', 
    fontSize: 14,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: ZamanColors.gray[400],
  },
  statusDotActive: {
    backgroundColor: ZamanColors.black,
  },
  messagesContainer: { 
    flex: 1, 
    padding: 24,
    backgroundColor: ZamanColors.cloud,
  },
  videoPreviewContainer: {
    alignItems: 'center',
    marginBottom: 24,
    padding: 20,
    backgroundColor: ZamanColors.white,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: ZamanColors.persianGreen,
  },
  videoLabel: {
    marginTop: 16,
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: ZamanColors.persianGreen,
    borderRadius: 12,
  },
  videoLabelText: {
    color: ZamanColors.white,
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  emptyState: { 
    flex: 1, 
    justifyContent: 'center', 
    alignItems: 'center', 
    paddingTop: 80,
  },
  emptyIconContainer: { 
    marginBottom: 24,
    padding: 20,
    backgroundColor: ZamanColors.cloud,
    borderRadius: 50,
  },
  emptyStateText: { 
    fontSize: 20, 
    color: ZamanColors.black, 
    textAlign: 'center', 
    marginBottom: 12, 
    fontWeight: '600',
  },
  emptyStateSubtext: { 
    fontSize: 15, 
    color: ZamanColors.gray[500], 
    textAlign: 'center', 
    marginTop: 8,
    lineHeight: 22,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 20,
    padding: 12,
    backgroundColor: ZamanColors.cloud,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#f44336',
  },
  errorText: { 
    fontSize: 14, 
    color: '#f44336', 
    fontWeight: '600',
  },
  messageBubble: { 
    maxWidth: '80%', 
    padding: 16, 
    borderRadius: 16, 
    marginBottom: 16,
  },
  userBubble: { 
    alignSelf: 'flex-end', 
    backgroundColor: ZamanColors.persianGreen,
  },
  aiBubble: { 
    alignSelf: 'flex-start', 
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
  },
  messageText: { 
    color: ZamanColors.black, 
    fontSize: 16, 
    lineHeight: 24,
  },
  userMessageText: {
    color: ZamanColors.white,
  },
  activeIndicator: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
    backgroundColor: ZamanColors.white,
    borderTopWidth: 1,
    borderTopColor: ZamanColors.gray[200],
    gap: 20,
  },
  activeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  activeText: { 
    color: ZamanColors.persianGreen, 
    fontSize: 14, 
    fontWeight: '600',
  },
  volumeText: { 
    color: ZamanColors.gray[500], 
    fontSize: 13,
    fontWeight: '500',
  },
  controlsContainer: { 
    flexDirection: 'row', 
    justifyContent: 'space-around', 
    padding: 24, 
    backgroundColor: ZamanColors.white, 
    borderTopWidth: 1, 
    borderTopColor: ZamanColors.gray[200],
  },
  controlButton: { 
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 16,
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
    opacity: 0.5,
    minWidth: 110,
  },
  controlButtonActive: { 
    opacity: 1, 
    backgroundColor: ZamanColors.persianGreen,
    borderColor: ZamanColors.persianGreen,
  },
  controlButtonText: { 
    color: ZamanColors.black, 
    fontSize: 13, 
    fontWeight: '600',
  },
  controlButtonTextActive: {
    color: ZamanColors.white,
  },
});
