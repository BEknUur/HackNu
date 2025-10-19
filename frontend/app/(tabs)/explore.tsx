import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { ZamanColors } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';
import Markdown from 'react-native-markdown-display';
import ZamanLogo from '@/components/zaman-logo';
import { config } from '@/lib/config';

// AI Character Configuration
const AI_CHARACTER_NAME = "Zaman";
const WELCOME_MESSAGE = "I'm Zaman. Your future self asked me to help you get there.";

interface ChatMessage {
  id: number;
  role: "user" | "ai";
  content: string;
  timestamp: string;
  sources?: any[];
  agents_used?: string[];
  confidence?: number;
}

interface ChatState {
  messages: ChatMessage[];
  input: string;
  loading: boolean;
  error: string | null;
}

const { width } = Dimensions.get('window');
const isSmallScreen = width < 768;

// Utility to filter refusal patterns
function filterRefusalText(content: string): string {
  let cleaned = content.replace(/\(Refusal: ?true\)/gi, '');
  cleaned = cleaned.replace(/([\n\r]+[ \t]*([*]{2,}|_{2,})[ \t]*)+$/g, '');
  cleaned = cleaned.replace(/[\n\r]+$/g, '').trim();
  return cleaned;
}

export default function ExploreScreen() {
  const scrollViewRef = useRef<ScrollView>(null);
  const inputRef = useRef<TextInput>(null);

  const [chatState, setChatState] = useState<ChatState>({
    messages: [{
      id: 0,
      role: 'ai',
      content: WELCOME_MESSAGE,
      timestamp: new Date().toISOString()
    }],
    input: '',
    loading: false,
    error: null
  });

  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  // Send message to RAG API
  const sendMessage = useCallback(async () => {
    if (!chatState.input.trim() || chatState.loading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: chatState.input.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message immediately
    setChatState(prev => ({ 
      ...prev, 
      messages: [...prev.messages, userMessage],
      loading: true,
      input: '',
      error: null
    }));

    try {
      // Get token from localStorage
      const token = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;
      
      // Call RAG API
      const response = await fetch(`${config.backendURL}${config.endpoints.rag.live.query}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          query: userMessage.content,
          session_id: sessionId,
          user_id: 'user',
          context: {}
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Add AI response
      const aiMessage: ChatMessage = {
        id: Date.now() + 1,
        role: 'ai',
        content: data.response,
        timestamp: new Date().toISOString(),
        sources: data.sources || [],
        agents_used: data.agents_used || [],
        confidence: data.confidence || 0.8
      };

      setChatState(prev => ({ 
        ...prev, 
        messages: [...prev.messages, aiMessage],
        loading: false 
      }));

    } catch (error: any) {
      console.error('Error sending message:', error);
      
      let errorMessage = 'Failed to send message';
      if (error.message === 'Failed to fetch') {
        errorMessage = '🔌 Backend not running. Please start: cd backend && uvicorn main:app --reload';
      } else {
        errorMessage = error.message || 'Unknown error occurred';
      }
      
      setChatState(prev => ({ 
        ...prev, 
        error: errorMessage,
        loading: false 
      }));
    }
  }, [chatState.input, chatState.loading, sessionId]);

  const handleSuggestedPrompt = useCallback((prompt: string) => {
    setChatState(prev => ({ ...prev, input: prompt }));
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [chatState.messages]);

  const fixedPrompts = [
    "What Islamic banking products does Zaman offer?",
    "How does Zaman ensure Sharia compliance in its services?",
    "How can I open a halal savings account with Zaman?",
    "What investment opportunities are available in Islamic banking?",
   
  ];

  const startNewChat = useCallback(() => {
    setChatState({
      messages: [{
        id: 0,
        role: 'ai',
        content: WELCOME_MESSAGE,
        timestamp: new Date().toISOString()
      }],
      input: '',
      loading: false,
      error: null
    });
  }, []);

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <View style={styles.mainContainer}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Text style={styles.headerTitle}>
              Chat with {AI_CHARACTER_NAME}
            </Text>
            <Text style={styles.headerSubtitle}>
              Your AI Wellness Coach
            </Text>
          </View>
          {chatState.messages.length > 1 && (
            <TouchableOpacity
              style={styles.newChatButton}
              onPress={startNewChat}
            >
              <Ionicons name="add-circle-outline" size={20} color={ZamanColors.persianGreen} />
              <Text style={styles.newChatButtonText}>New Chat</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Avatar Section */}
        <View style={styles.avatarSection}>
          <View style={styles.avatarContainer}>
            <View style={styles.avatarCircle}>
              <ZamanLogo size={isSmallScreen ? 60 : 80} withAccent />
            </View>
          </View>
          <View style={styles.statusBadge}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>
              Ready
            </Text>
          </View>
        </View>

        {/* Error Display */}
        {chatState.error && (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle" size={20} color="#f44336" />
            <Text style={styles.errorText}>
              {chatState.error}
            </Text>
            <TouchableOpacity onPress={() => setChatState(prev => ({ ...prev, error: null }))}>
              <Ionicons name="close-circle" size={20} color="#f44336" />
            </TouchableOpacity>
          </View>
        )}

        {/* Messages */}
        <ScrollView 
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {chatState.messages.map((msg) => (
            <View
              key={`${msg.id}-${msg.timestamp}`}
              style={[
                styles.messageWrapper,
                msg.role === 'user' ? styles.userMessageWrapper : styles.aiMessageWrapper
              ]}
            >
              <View
                style={[
                  styles.messageBubble,
                  msg.role === 'user' ? styles.userBubble : styles.aiBubble
                ]}
              >
                <Markdown
                  style={msg.role === 'user' ? markdownUserStyles : markdownAiStyles}
                >
                  {filterRefusalText(msg.content)}
                </Markdown>
                
                {/* RAG Metadata - only for AI messages */}
                {msg.role === 'ai' && msg.agents_used && msg.agents_used.length > 0 && (
                  <View style={styles.ragMetadata}>
                    {/* Agents Used */}
                    <View style={styles.agentsContainer}>
                      <View style={styles.metadataLabelRow}>
                        <Ionicons name="git-network-outline" size={14} color={ZamanColors.gray[600]} />
                        <Text style={styles.metadataLabel}>
                          Agents:
                        </Text>
                      </View>
                      <View style={styles.agentsList}>
                        {msg.agents_used.map((agent, idx) => (
                          <View key={idx} style={styles.agentBadge}>
                            <Text style={styles.agentText}>
                              {agent.replace('_agent', '').replace('_', ' ')}
                            </Text>
                          </View>
                        ))}
                      </View>
                    </View>
                    
                    {/* Sources Count */}
                    {msg.sources && msg.sources.length > 0 && (
                      <View style={styles.metadataRow}>
                        <Ionicons name="library-outline" size={12} color={ZamanColors.gray[600]} />
                        <Text style={styles.sourcesCount}>
                          {msg.sources.length} source{msg.sources.length > 1 ? 's' : ''}
                        </Text>
                      </View>
                    )}
                    
                    {/* Confidence */}
                  
                  </View>
                )}
              </View>
              <Text style={styles.timestamp}>
                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Text>
            </View>
          ))}

          {/* Loading Indicator */}
          {chatState.loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color={ZamanColors.persianGreen} />
              <Text style={styles.loadingText}>
                {AI_CHARACTER_NAME} is thinking...
              </Text>
            </View>
          )}

          {/* Quick Starters */}
          {chatState.messages.length === 1 && !chatState.loading && (
            <View style={styles.promptsContainer}>
              <Text style={styles.promptsTitle}>
                Quick starters:
              </Text>
              {fixedPrompts.map((prompt, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.promptButton}
                  onPress={() => handleSuggestedPrompt(prompt)}
                >
                  <Ionicons name="bulb-outline" size={16} color={ZamanColors.persianGreen} />
                  <Text style={styles.promptText}>
                    {prompt}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </ScrollView>

        {/* Input Area */}
        <View style={styles.inputContainer}>
          <TextInput
            ref={inputRef}
            style={styles.input}
            value={chatState.input}
            onChangeText={(text) => setChatState(prev => ({ ...prev, input: text }))}
            placeholder={`Message ${AI_CHARACTER_NAME}...`}
            placeholderTextColor={ZamanColors.gray[400]}
            multiline
            editable={!chatState.loading}
            onKeyPress={(e: any) => {
              if (Platform.OS === 'web' && e.nativeEvent.key === 'Enter' && !e.nativeEvent.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
          />
          <TouchableOpacity
            style={[
              styles.sendButton,
              (!chatState.input.trim() || chatState.loading) && styles.sendButtonDisabled
            ]}
            onPress={sendMessage}
            disabled={!chatState.input.trim() || chatState.loading}
          >
            <Ionicons 
              name="send" 
              size={20} 
              color={ZamanColors.white} 
            />
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  mainContainer: {
    flex: 1,
    backgroundColor: ZamanColors.white,
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingHorizontal: 24,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: ZamanColors.gray[200],
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: ZamanColors.white,
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: ZamanColors.black,
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  headerSubtitle: {
    fontSize: 13,
    color: ZamanColors.gray[500],
    fontWeight: '400',
  },
  newChatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
  },
  newChatButtonText: {
    color: ZamanColors.persianGreen,
    fontSize: 14,
    fontWeight: '600',
  },
  avatarSection: {
    alignItems: 'center',
    paddingVertical: 30,
    backgroundColor: ZamanColors.cloud,
  },
  avatarContainer: {
    width: isSmallScreen ? 100 : 120,
    height: isSmallScreen ? 100 : 120,
    marginBottom: 16,
  },
  avatarCircle: {
    width: '100%',
    height: '100%',
    borderRadius: 100,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: ZamanColors.white,
    borderWidth: 3,
    borderColor: ZamanColors.persianGreen,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: ZamanColors.white,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: ZamanColors.gray[200],
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#22c55e',
  },
  statusText: {
    fontSize: 13,
    fontWeight: '500',
    color: ZamanColors.gray[600],
  },
  errorContainer: {
    marginHorizontal: 24,
    marginVertical: 12,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: ZamanColors.cloud,
    borderWidth: 1,
    borderColor: '#f44336',
  },
  errorText: {
    fontSize: 14,
    flex: 1,
    color: '#f44336',
    fontWeight: '500',
  },
  messagesContainer: {
    flex: 1,
    backgroundColor: ZamanColors.cloud,
  },
  messagesContent: {
    padding: 24,
    paddingBottom: 20,
  },
  messageWrapper: {
    marginBottom: 20,
    maxWidth: '80%',
  },
  userMessageWrapper: {
    alignSelf: 'flex-end',
    alignItems: 'flex-end',
  },
  aiMessageWrapper: {
    alignSelf: 'flex-start',
    alignItems: 'flex-start',
  },
  messageBubble: {
    borderRadius: 16,
    padding: 16,
  },
  userBubble: {
    borderBottomRightRadius: 4,
    backgroundColor: ZamanColors.persianGreen,
  },
  aiBubble: {
    borderBottomLeftRadius: 4,
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
  },
  timestamp: {
    fontSize: 11,
    marginTop: 6,
    color: ZamanColors.gray[500],
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 16,
  },
  loadingText: {
    fontSize: 14,
    color: ZamanColors.gray[600],
    fontWeight: '500',
  },
  promptsContainer: {
    marginTop: 20,
    gap: 12,
  },
  promptsTitle: {
    fontSize: 13,
    marginBottom: 12,
    color: ZamanColors.gray[600],
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  promptButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
  },
  promptText: {
    flex: 1,
    fontSize: 14,
    color: ZamanColors.black,
    lineHeight: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
    paddingBottom: Platform.OS === 'ios' ? 34 : 16,
    borderTopWidth: 1,
    borderTopColor: ZamanColors.gray[200],
    gap: 12,
    backgroundColor: ZamanColors.white,
  },
  input: {
    flex: 1,
    fontSize: 15,
    maxHeight: 100,
    paddingVertical: 8,
    color: ZamanColors.black,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: ZamanColors.persianGreen,
  },
  sendButtonDisabled: {
    backgroundColor: ZamanColors.gray[400],
    opacity: 0.5,
  },
  ragMetadata: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: ZamanColors.gray[200],
    gap: 8,
  },
  agentsContainer: {
    marginBottom: 6,
  },
  metadataLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  metadataLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: ZamanColors.gray[600],
  },
  metadataRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  agentsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  agentBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: ZamanColors.persianGreen,
  },
  agentText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'capitalize',
    color: ZamanColors.white,
  },
  sourcesCount: {
    fontSize: 11,
    color: ZamanColors.gray[600],
    fontWeight: '500',
  },
  confidence: {
    fontSize: 11,
    color: ZamanColors.gray[600],
    fontWeight: '500',
  },
});

// Markdown styles for AI messages (black text on white)
const markdownAiStyles = StyleSheet.create({
  body: {
    color: ZamanColors.black,
    fontSize: 15,
    lineHeight: 22,
  },
  paragraph: {
    marginTop: 0,
    marginBottom: 10,
    color: ZamanColors.black,
  },
  strong: {
    fontWeight: '700',
    color: ZamanColors.black,
  },
  em: {
    fontStyle: 'italic',
    color: ZamanColors.black,
  },
  bullet_list: {
    marginTop: 6,
    marginBottom: 6,
  },
  ordered_list: {
    marginTop: 6,
    marginBottom: 6,
  },
  list_item: {
    flexDirection: 'row',
    marginBottom: 6,
    color: ZamanColors.black,
  },
  bullet_list_icon: {
    marginLeft: 0,
    marginRight: 8,
    color: ZamanColors.persianGreen,
    fontSize: 15,
  },
  code_inline: {
    backgroundColor: ZamanColors.cloud,
    color: ZamanColors.persianGreen,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontSize: 14,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  code_block: {
    backgroundColor: ZamanColors.cloud,
    padding: 12,
    borderRadius: 8,
    marginTop: 6,
    marginBottom: 6,
  },
  fence: {
    backgroundColor: ZamanColors.cloud,
    padding: 12,
    borderRadius: 8,
    marginTop: 6,
    marginBottom: 6,
  },
  heading1: {
    fontSize: 20,
    fontWeight: '700',
    color: ZamanColors.black,
    marginTop: 10,
    marginBottom: 10,
  },
  heading2: {
    fontSize: 18,
    fontWeight: '600',
    color: ZamanColors.black,
    marginTop: 8,
    marginBottom: 8,
  },
  heading3: {
    fontSize: 16,
    fontWeight: '600',
    color: ZamanColors.black,
    marginTop: 6,
    marginBottom: 6,
  },
  link: {
    color: ZamanColors.persianGreen,
    textDecorationLine: 'underline',
  },
  blockquote: {
    backgroundColor: ZamanColors.cloud,
    borderLeftWidth: 3,
    borderLeftColor: ZamanColors.persianGreen,
    paddingLeft: 12,
    paddingVertical: 8,
    marginTop: 6,
    marginBottom: 6,
  },
});

// Markdown styles for User messages (white text on green)
const markdownUserStyles = StyleSheet.create({
  body: {
    color: ZamanColors.white,
    fontSize: 15,
    lineHeight: 22,
  },
  paragraph: {
    marginTop: 0,
    marginBottom: 10,
    color: ZamanColors.white,
  },
  strong: {
    fontWeight: '700',
    color: ZamanColors.white,
  },
  em: {
    fontStyle: 'italic',
    color: ZamanColors.white,
  },
  bullet_list: {
    marginTop: 6,
    marginBottom: 6,
  },
  ordered_list: {
    marginTop: 6,
    marginBottom: 6,
  },
  list_item: {
    flexDirection: 'row',
    marginBottom: 6,
    color: ZamanColors.white,
  },
  bullet_list_icon: {
    marginLeft: 0,
    marginRight: 8,
    color: ZamanColors.white,
    fontSize: 15,
  },
  code_inline: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    color: ZamanColors.white,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontSize: 14,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  code_block: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    padding: 12,
    borderRadius: 8,
    marginTop: 6,
    marginBottom: 6,
  },
  fence: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    padding: 12,
    borderRadius: 8,
    marginTop: 6,
    marginBottom: 6,
  },
  heading1: {
    fontSize: 20,
    fontWeight: '700',
    color: ZamanColors.white,
    marginTop: 10,
    marginBottom: 10,
  },
  heading2: {
    fontSize: 18,
    fontWeight: '600',
    color: ZamanColors.white,
    marginTop: 8,
    marginBottom: 8,
  },
  heading3: {
    fontSize: 16,
    fontWeight: '600',
    color: ZamanColors.white,
    marginTop: 6,
    marginBottom: 6,
  },
  link: {
    color: ZamanColors.white,
    textDecorationLine: 'underline',
  },
  blockquote: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderLeftWidth: 3,
    borderLeftColor: ZamanColors.white,
    paddingLeft: 12,
    paddingVertical: 8,
    marginTop: 6,
    marginBottom: 6,
  },
});
