import { StyleSheet, View, Text, TouchableOpacity, ScrollView, Platform } from 'react-native';
import { useState, useEffect, useRef } from 'react';
import { LiveAPIProvider, useLiveAPIContext } from '../../contexts/LiveAPIContext';
import Constants from 'expo-constants';
import { AudioRecorder } from '../../lib/audio-recorder';
import { useWebcam } from '../../hooks/use-webcam';
import { useScreenCapture } from '../../hooks/use-screen-capture';

const API_KEY = Constants.expoConfig?.extra?.GEMINI_API_KEY || process.env.EXPO_PUBLIC_GEMINI_API_KEY;

function LiveChatContent() {
  const { connected, connect, disconnect, client, volume, setConfig } = useLiveAPIContext();
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'ai'}>>([]);
  const [isMicOn, setIsMicOn] = useState(false);
  const audioRecorderRef = useRef<AudioRecorder | null>(null);
  const webcam = useWebcam();
  const screenCapture = useScreenCapture();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoIntervalRef = useRef<number | null>(null);

  // Setup config for Gemini
  useEffect(() => {
    setConfig({});
  }, [setConfig]);

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
        alert('Disconnected from Gemini');
      } else {
        await connect();
        setMessages([{
          id: '1',
          text: 'Hello! I\'m Gemini AI with multimodal capabilities. Turn on your microphone, camera, or share your screen to start! 🎤📹🖥️',
          sender: 'ai'
        }]);
        alert('Connected to Gemini Live API! 🚀');
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
      alert('Please connect to Gemini first');
      return;
    }

    if (isMicOn) {
      // Stop recording
      audioRecorderRef.current?.stop();
      audioRecorderRef.current = null;
      setIsMicOn(false);
      alert('🔇 Microphone turned off');
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
        alert('🎤 Microphone is ON - Speak now!');
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
  };

  // Toggle webcam
  const toggleCamera = async () => {
    if (!connected) {
      alert('Please connect to Gemini first');
      return;
    }

    if (Platform.OS !== 'web') {
      alert('Webcam is only available on web platform');
      return;
    }

    if (webcam.isStreaming) {
      stopVideoStream();
      webcam.stop();
      alert('📷 Camera turned off');
    } else {
      try {
        // Stop screen share if active
        if (screenCapture.isStreaming) {
          stopVideoStream();
          screenCapture.stop();
        }

        const stream = await webcam.start();
        startVideoStream(stream);
        alert('📹 Camera is ON - AI can see you!');
      } catch (error) {
        console.error('Camera error:', error);
        alert('Error: Could not access camera');
      }
    }
  };

  // Toggle screen share
  const toggleScreenShare = async () => {
    if (!connected) {
      alert('Please connect to Gemini first');
      return;
    }

    if (Platform.OS !== 'web') {
      alert('Screen sharing is only available on web platform');
      return;
    }

    if (screenCapture.isStreaming) {
      stopVideoStream();
      screenCapture.stop();
      alert('🖥️ Screen sharing stopped');
    } else {
      try {
        // Stop webcam if active
        if (webcam.isStreaming) {
          stopVideoStream();
          webcam.stop();
        }

        const stream = await screenCapture.start();
        startVideoStream(stream);
        alert('🖥️ Screen sharing is ON - AI can see your screen!');
      } catch (error) {
        console.error('Screen share error:', error);
        alert('Error: Could not capture screen');
      }
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Gemini Live Chat</Text>
          <Text style={styles.headerSubtitle}>Multimodal AI Assistant</Text>
        </View>
        <TouchableOpacity 
          style={[styles.connectButton, connected && styles.connectButtonActive]}
          onPress={handleConnect}
        >
          <Text style={styles.connectButtonText}>
            {connected ? '● LIVE' : '○ Connect'}
          </Text>
        </TouchableOpacity>
      </View>
      
      <ScrollView style={styles.messagesContainer}>
        {messages.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>🤖</Text>
            <Text style={styles.emptyStateText}>
              Press "Connect" to start
            </Text>
            <Text style={styles.emptyStateSubtext}>
              After connecting, use the buttons below:
            </Text>
            <Text style={styles.emptyStateSubtext}>
              🎤 Voice • 📹 Camera • 🖥️ Screen Share
            </Text>
            {!API_KEY && (
              <Text style={styles.errorText}>⚠️ API key not found!</Text>
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
          {isMicOn && <Text style={styles.activeText}>🎤 Microphone</Text>}
          {webcam.isStreaming && <Text style={styles.activeText}>📹 Camera</Text>}
          {screenCapture.isStreaming && <Text style={styles.activeText}>🖥️ Screen</Text>}
          {isMicOn && <Text style={styles.volumeText}>Volume: {Math.round(volume * 100)}%</Text>}
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
          <Text style={styles.controlButtonText}>Microphone</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.controlButton, webcam.isStreaming && styles.controlButtonActive]}
          disabled={!connected || Platform.OS !== 'web'}
          onPress={toggleCamera}
        >
          <Text style={styles.controlButtonIcon}>{webcam.isStreaming ? '📹' : '📷'}</Text>
          <Text style={styles.controlButtonText}>Camera</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.controlButton, screenCapture.isStreaming && styles.controlButtonActive]}
          disabled={!connected || Platform.OS !== 'web'}
          onPress={toggleScreenShare}
        >
          <Text style={styles.controlButtonIcon}>🖥️</Text>
          <Text style={styles.controlButtonText}>Screen</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

export default function LiveChatScreen() {
  const apiOptions = { apiKey: API_KEY || '' };
  return (
    <LiveAPIProvider options={apiOptions}>
      <LiveChatContent />
    </LiveAPIProvider>
  );
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
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  headerSubtitle: { fontSize: 12, color: '#888', marginTop: 2 },
  connectButton: { paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#333', borderRadius: 20 },
  connectButtonActive: { backgroundColor: '#f44336' },
  connectButtonText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  messagesContainer: { flex: 1, padding: 16 },
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
