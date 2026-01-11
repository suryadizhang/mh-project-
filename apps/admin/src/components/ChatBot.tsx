/**
 * AI Chatbot Component for Admin Panel
 * Provides AI chat functionality with admin-specific features
 */

'use client';

import {
  Activity,
  AlertCircle,
  Bot,
  CheckCircle,
  Clock,
  Loader2,
  MessageCircle,
  Minimize2,
  Send,
  Settings,
  User,
  Wifi,
  WifiOff,
} from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';

import { useWebSocket } from '@/hooks/useWebSocket';

// Environment-aware WebSocket URL
const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/^http/, 'ws').replace(
        /^https/,
        'wss'
      )
    : typeof window !== 'undefined' && window.location.hostname !== 'localhost'
      ? 'wss://mhapi.mysticdatanode.net'
      : 'ws://localhost:8002');
import { logger } from '@/lib/logger';
import { type AdminChatResponse, aiApiService } from '@/services/ai-api';

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
  confidence?: number;
  processingTime?: number;
  debugInfo?: any;
}

interface ChatBotProps {
  className?: string;
  defaultMinimized?: boolean;
  showDebugInfo?: boolean;
  enableWebSocket?: boolean;
}

export default function ChatBot({
  className = '',
  defaultMinimized = false,
  showDebugInfo = true,
  enableWebSocket = true,
}: ChatBotProps) {
  const [isMinimized, setIsMinimized] = useState(defaultMinimized);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content:
        "Hello! I'm your AI management assistant. I can help you with:\n• User & Staff Management\n• Booking Operations\n• Analytics & Reports\n• System Configuration\n• Operations Support\n\nHow can I assist you with managing MyHibachi today?",
      isBot: true,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket connection for real-time chat
  const wsConfig = {
    url: `${WS_BASE_URL}/api/v1/ws/chat`,
    conversationId: conversationId || undefined,
    userId: 'admin',
    channel: 'admin',
    userRole: 'admin',
    autoReconnect: true,
  };

  const {
    isConnected: wsConnected,
    isConnecting: wsConnecting,
    lastMessage: wsLastMessage,
    connectionError: wsError,
    sendMessage: wsSendMessage,
    reconnect: wsReconnect,
  } = useWebSocket(
    enableWebSocket ? wsConfig : { url: '', autoReconnect: false }
  );

  // Handle WebSocket messages
  useEffect(() => {
    if (!wsLastMessage || !enableWebSocket) return;

    const message = wsLastMessage;

    // Handle different message types
    switch (message.type) {
      case 'ai_response':
        setIsLoading(false);
        const aiMessage: Message = {
          id: message.message_id || Date.now().toString(),
          content: message.content,
          isBot: true,
          timestamp: new Date(message.timestamp),
          confidence: message.metadata?.confidence,
          processingTime: message.metadata?.processing_time_ms,
          debugInfo: message.metadata,
        };
        setMessages(prev => [...prev, aiMessage]);
        break;

      case 'typing':
        // Handle typing indicator
        if (message.metadata?.is_typing) {
          setIsLoading(true);
        } else {
          setIsLoading(false);
        }
        break;

      case 'connection_status':
        logger.debug('WebSocket connection status', {
          status: message.content,
        });
        break;

      case 'system':
        if (message.content !== 'pong') {
          // Filter out ping/pong messages
          const systemMessage: Message = {
            id: Date.now().toString(),
            content: `System: ${message.content}`,
            isBot: true,
            timestamp: new Date(message.timestamp),
          };
          setMessages(prev => [...prev, systemMessage]);
        }
        break;

      case 'error':
        setIsLoading(false);
        const errorMessage: Message = {
          id: Date.now().toString(),
          content: message.content,
          isBot: true,
          timestamp: new Date(message.timestamp),
        };
        setMessages(prev => [...prev, errorMessage]);
        break;

      default:
        logger.debug('Unknown WebSocket message type', { type: message.type });
    }
  }, [wsLastMessage, enableWebSocket]);

  // Update connection status
  useEffect(() => {
    if (enableWebSocket) {
      setIsConnected(wsConnected);
    }
  }, [wsConnected, enableWebSocket]);

  // Check AI API connection on mount
  useEffect(() => {
    checkConnection();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const checkConnection = async () => {
    try {
      const available = await aiApiService.isAvailable();
      setIsConnected(available);
    } catch (error) {
      logger.error(error as Error, { context: 'check_ai_api_connection' });
      setIsConnected(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      isBot: false,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    if (enableWebSocket && wsConnected) {
      // Use WebSocket for real-time chat
      setIsLoading(true);
      wsSendMessage(inputValue, 'message');
    } else {
      // Fallback to REST API
      setIsLoading(true);

      try {
        let response: AdminChatResponse;

        if (showDebugInfo) {
          // Use admin test endpoint for debug info
          response = await aiApiService.testAdminChat({
            message: inputValue,
            test_mode: true,
            channel: 'admin',
            user_role: 'admin',
            context: {
              admin_user: true,
              conversation_id: conversationId,
            },
          });
        } else {
          // Use regular chat endpoint
          const chatResponse = await aiApiService.sendChatMessage({
            message: inputValue,
            conversation_id: conversationId || undefined,
            channel: 'admin',
            user_id: 'admin',
            user_role: 'admin',
            context: {
              admin_user: true,
            },
          });
          response = chatResponse as any; // Type conversion for compatibility
        }

        // Update conversation ID
        if (!conversationId) {
          setConversationId(response.conversation_id);
        }

        const botMessage: Message = {
          id: response.message_id,
          content: response.content,
          isBot: true,
          timestamp: new Date(response.timestamp),
          confidence: response.debug_info?.confidence_score,
          processingTime: response.processing_time_ms,
          debugInfo: response.debug_info,
        };

        setMessages(prev => [...prev, botMessage]);
      } catch (error) {
        logger.error(error as Error, {
          context: 'send_message',
          conversation_id: conversationId,
        });

        const errorMessage: Message = {
          id: Date.now().toString(),
          content: `Sorry, I'm having trouble connecting to the AI service. Please try again later. ${error instanceof Error ? error.message : ''}`,
          isBot: true,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearConversation = () => {
    setMessages([
      {
        id: '1',
        content:
          "Hello! I'm your AI management assistant. How can I help you manage MyHibachi today?",
        isBot: true,
        timestamp: new Date(),
      },
    ]);
    setConversationId(null);
  };

  if (isMinimized) {
    return (
      <div className={`fixed bottom-6 right-6 z-50 ${className}`}>
        <button
          onClick={() => setIsMinimized(false)}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-200 hover:scale-105"
        >
          <MessageCircle size={24} />
          {!isConnected && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full" />
          )}
        </button>
      </div>
    );
  }

  return (
    <div className={`fixed bottom-6 right-6 z-50 ${className}`}>
      <div className="bg-white rounded-lg shadow-2xl border border-gray-200 w-96 h-[500px] flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 text-white p-4 rounded-t-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot size={20} />
            <div>
              <h3 className="font-semibold">AI Assistant</h3>
              <div className="flex items-center gap-1 text-xs">
                {enableWebSocket ? (
                  wsConnected ? (
                    <>
                      <Wifi size={12} className="text-green-300" />
                      <span>Real-time</span>
                    </>
                  ) : wsConnecting ? (
                    <>
                      <Loader2
                        size={12}
                        className="text-yellow-300 animate-spin"
                      />
                      <span>Connecting...</span>
                    </>
                  ) : (
                    <>
                      <WifiOff size={12} className="text-red-300" />
                      <span>Offline</span>
                    </>
                  )
                ) : isConnected ? (
                  <>
                    <CheckCircle size={12} className="text-green-300" />
                    <span>Connected</span>
                  </>
                ) : (
                  <>
                    <AlertCircle size={12} className="text-red-300" />
                    <span>Disconnected</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (enableWebSocket) {
                  wsReconnect();
                } else {
                  checkConnection();
                }
              }}
              className="hover:bg-blue-700 p-1 rounded"
              title="Refresh connection"
            >
              <Activity size={16} />
            </button>
            <button
              onClick={clearConversation}
              className="hover:bg-blue-700 p-1 rounded"
              title="New conversation"
            >
              <Settings size={16} />
            </button>
            <button
              onClick={() => setIsMinimized(true)}
              className="hover:bg-blue-700 p-1 rounded"
              title="Minimize"
            >
              <Minimize2 size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(message => (
            <div
              key={message.id}
              className={`flex items-start gap-2 ${
                message.isBot ? 'flex-row' : 'flex-row-reverse'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${
                  message.isBot ? 'bg-blue-500' : 'bg-gray-500'
                }`}
              >
                {message.isBot ? <Bot size={16} /> : <User size={16} />}
              </div>
              <div
                className={`flex-1 ${message.isBot ? 'text-left' : 'text-right'}`}
              >
                <div
                  className={`inline-block p-3 rounded-lg max-w-xs ${
                    message.isBot
                      ? 'bg-gray-100 text-gray-800'
                      : 'bg-blue-600 text-white'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>

                  {/* Debug info for admin */}
                  {showDebugInfo && message.isBot && message.debugInfo && (
                    <div className="mt-2 pt-2 border-t border-gray-300 text-xs">
                      <div className="grid grid-cols-2 gap-1">
                        {message.confidence && (
                          <div>
                            <span className="font-semibold">Confidence:</span>{' '}
                            {(message.confidence * 100).toFixed(1)}%
                          </div>
                        )}
                        {message.processingTime && (
                          <div>
                            <span className="font-semibold">Time:</span>{' '}
                            {message.processingTime.toFixed(0)}ms
                          </div>
                        )}
                        {message.debugInfo.knowledge_base_hits && (
                          <div>
                            <span className="font-semibold">KB Hits:</span>{' '}
                            {message.debugInfo.knowledge_base_hits}
                          </div>
                        )}
                        {message.debugInfo.fallback_used && (
                          <div className="col-span-2 text-orange-600">
                            <span className="font-semibold">
                              ⚠️ Fallback Used
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                  <Clock size={12} />
                  <span>{message.timestamp.toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
                <Bot size={16} />
              </div>
              <div className="bg-gray-100 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-gray-600">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2">
            <textarea
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                enableWebSocket
                  ? wsConnected
                    ? 'Ask me anything...'
                    : 'Connecting to real-time chat...'
                  : isConnected
                    ? 'Ask me anything...'
                    : 'AI service disconnected'
              }
              disabled={
                enableWebSocket
                  ? !wsConnected || isLoading
                  : !isConnected || isLoading
              }
              className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              rows={2}
            />
            <button
              onClick={handleSendMessage}
              disabled={
                !inputValue.trim() ||
                (enableWebSocket
                  ? !wsConnected || isLoading
                  : !isConnected || isLoading)
              }
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg px-4 py-2 transition-colors disabled:cursor-not-allowed"
            >
              <Send size={16} />
            </button>
          </div>

          {enableWebSocket
            ? !wsConnected && (
                <div className="mt-2 text-xs text-red-600 flex items-center gap-1">
                  <AlertCircle size={12} />
                  <span>
                    {wsConnecting
                      ? 'Connecting to real-time chat...'
                      : wsError ||
                        'Real-time chat is not available. Messages will use REST API.'}
                  </span>
                </div>
              )
            : !isConnected && (
                <div className="mt-2 text-xs text-red-600 flex items-center gap-1">
                  <AlertCircle size={12} />
                  <span>
                    AI service is not available. Check the connection.
                  </span>
                </div>
              )}
        </div>
      </div>
    </div>
  );
}
