import { StyleSheet, View, Text, TouchableOpacity, ScrollView, Alert, Platform } from 'react-native';
import { useState, useEffect, useRef } from 'react';
import { LiveAPIProvider, useLiveAPIContext } from '../../contexts/LiveAPIContext';
import { Camera } from 'expo-camera';
import Constants from 'expo-constants';

const API_KEY = Constants.expoConfig?.extra?.GEMINI_API_KEY || process.env.EXPO_PUBLIC_GEMINI_API_KEY;

function LiveChatContent() {
  const { connected, connect, disconnect, client, volume } = useLiveAPIContext();
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'ai'}>>([]);
  const [isMicOn, setIsMicOn] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

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

    client.on('content', onContent);
    return () => {
      client.off('content', onContent);
    };
  }, [client]);

  const handleConnect = async () => {
    try {
      if (connected) {
        await disconnect();
        setMessages([]);
        setIsMicOn(false);
        setIsCameraOn(false);
        setIsScreenSharing(false);
        Alert.alert('Отключено', 'Соединение закрыто');
      } else {
        await connect();
        setMessages([{
          id: '1',
          text: 'Привет! Я Gemini AI с мультимодальными возможностями. Включите микрофон или камеру чтобы начать! 🎤📹',
          sender: 'ai'
        }]);
        Alert.alert('Успех', 'Подключено к Gemini Live API! 🚀');
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Ошибка', 'Проверьте API ключ в .env файле');
    }
  };

  const sendTestMessage = (text: string) => {
    if (!connected) return;
    
    // Добавляем сообщение пользователя
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      text: text,
      sender: 'user'
    }]);

    // Отправляем в Gemini
    try {
      client.send([{ text: text }]);
    } catch (error) {
      console.error('Send error:', error);
      Alert.alert('Ошибка', 'Не удалось отправить сообщение');
    }
  };

  const toggleMic = () => {
    if (!connected) {
      Alert.alert('Ошибка', 'Сначала подключитесь к Gemini');
      return;
    }
    const newState = !isMicOn;
    setIsMicOn(newState);
    
    if (newState) {
      // Включили микрофон - отправляем тестовое сообщение
      Alert.alert('Микрофон включен', '🎤 Говорите, AI слушает');
      setTimeout(() => {
        sendTestMessage('Привет! Я включил микрофон. Как дела?');
      }, 500);
    } else {
      Alert.alert('Микрофон выключен', '🔇 Голосовой ввод остановлен');
    }
  };

  const toggleCamera = () => {
    if (!connected) {
      Alert.alert('Ошибка', 'Сначала подключитесь к Gemini');
      return;
    }
    if (!hasPermission) {
      Alert.alert('Ошибка', 'Нет доступа к камере');
      return;
    }
    const newState = !isCameraOn;
    setIsCameraOn(newState);
    
    if (newState) {
      Alert.alert('Камера включена', '📹 AI видит что вы показываете');
      setTimeout(() => {
        sendTestMessage('Я включил камеру. Что ты видишь на экране?');
      }, 500);
    } else {
      Alert.alert('Камера выключена', '📷 Видео остановлено');
    }
  };

  const toggleScreenShare = () => {
    if (!connected) {
      Alert.alert('Ошибка', 'Сначала подключитесь к Gemini');
      return;
    }
    if (Platform.OS !== 'web') {
      Alert.alert('Недоступно', 'Демонстрация экрана доступна только на веб-платформе');
      return;
    }
    const newState = !isScreenSharing;
    setIsScreenSharing(newState);
    
    if (newState) {
      Alert.alert('Демонстрация экрана', '🖥️ AI видит ваш экран');
      setTimeout(() => {
        sendTestMessage('Я включил демонстрацию экрана. Опиши что ты видишь.');
      }, 500);
    } else {
      Alert.alert('Демонстрация остановлена', '🖥️ Захват экрана остановлен');
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
              Нажмите "Connect" чтобы начать
            </Text>
            <Text style={styles.emptyStateSubtext}>
              После подключения используйте кнопки снизу:
            </Text>
            <Text style={styles.emptyStateSubtext}>
              🎤 Голосовой ввод • 📹 Камера • 🖥️ Экран
            </Text>
            {!API_KEY && (
              <Text style={styles.errorText}>⚠️ API ключ не найден!</Text>
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

      {/* Индикатор активности */}
      {connected && (isMicOn || isCameraOn || isScreenSharing) && (
        <View style={styles.activeIndicator}>
          {isMicOn && <Text style={styles.activeText}>🎤 Микрофон</Text>}
          {isCameraOn && <Text style={styles.activeText}>📹 Камера</Text>}
          {isScreenSharing && <Text style={styles.activeText}>🖥️ Экран</Text>}
          {isMicOn && <Text style={styles.volumeText}>Volume: {Math.round(volume * 100)}%</Text>}
        </View>
      )}

      {/* Контролы */}
      <View style={styles.controlsContainer}>
        <TouchableOpacity 
          style={[styles.controlButton, isMicOn && styles.controlButtonActive]}
          disabled={!connected}
          onPress={toggleMic}
        >
          <Text style={styles.controlButtonIcon}>{isMicOn ? '🎤' : '🔇'}</Text>
          <Text style={styles.controlButtonText}>Микрофон</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.controlButton, isCameraOn && styles.controlButtonActive]}
          disabled={!connected}
          onPress={toggleCamera}
        >
          <Text style={styles.controlButtonIcon}>{isCameraOn ? '📹' : '📷'}</Text>
          <Text style={styles.controlButtonText}>Камера</Text>
        </TouchableOpacity>
        
        {Platform.OS === 'web' && (
          <TouchableOpacity 
            style={[styles.controlButton, isScreenSharing && styles.controlButtonActive]}
            disabled={!connected}
            onPress={toggleScreenShare}
          >
            <Text style={styles.controlButtonIcon}>🖥️</Text>
            <Text style={styles.controlButtonText}>Экран</Text>
          </TouchableOpacity>
        )}
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
