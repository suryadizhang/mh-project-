/**
 * WebSocket Service for Real-time AI Chat
 * Handles WebSocket connections to AI API for live chat functionality
 */

'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { logger } from '@/lib/logger';

export interface WebSocketMessage {
  type: 'message' | 'typing' | 'system' | 'error' | 'connection_status' | 'ai_response';
  conversation_id: string;
  content: string;
  timestamp: string;
  user_id?: string;
  message_id?: string;
  metadata?: any;
}

export interface WebSocketConfig {
  url: string;
  conversationId?: string;
  userId?: string;
  channel?: string;
  userRole?: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface WebSocketHookResult {
  isConnected: boolean;
  isConnecting: boolean;
  lastMessage: WebSocketMessage | null;
  connectionError: string | null;
  sendMessage: (content: string, type?: string) => void;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
}

export function useWebSocket(config: WebSocketConfig): WebSocketHookResult {
  const {
    url,
    conversationId,
    userId = 'admin',
    channel = 'admin',
    userRole = 'admin',
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = config;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const messageQueue = useRef<string[]>([]);

  // Build WebSocket URL with query parameters
  const buildWebSocketUrl = useCallback(() => {
    const wsUrl = new URL(url);
    if (conversationId) wsUrl.searchParams.append('conversation_id', conversationId);
    if (userId) wsUrl.searchParams.append('user_id', userId);
    if (channel) wsUrl.searchParams.append('channel', channel);
    if (userRole) wsUrl.searchParams.append('user_role', userRole);
    return wsUrl.toString();
  }, [url, conversationId, userId, channel, userRole]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);
    setConnectionError(null);

    try {
      const wsUrl = buildWebSocketUrl();
      logger.websocket('connect', { url: wsUrl });
      
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        logger.websocket('connect', { status: 'connected' });
        setIsConnected(true);
        setIsConnecting(false);
        setConnectionError(null);
        reconnectAttempts.current = 0;

        // Send queued messages
        while (messageQueue.current.length > 0) {
          const queuedMessage = messageQueue.current.shift();
          if (queuedMessage) {
            ws.current?.send(queuedMessage);
          }
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          logger.websocket('message', { type: message.type, conversation_id: message.conversation_id });
          setLastMessage(message);
        } catch (error) {
          logger.error(error as Error, { context: 'websocket_parse' });
        }
      };

      ws.current.onclose = (event) => {
        logger.websocket('disconnect', { code: event.code, reason: event.reason });
        setIsConnected(false);
        setIsConnecting(false);

        // Attempt reconnection if enabled
        if (autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          logger.websocket('reconnect', { 
            attempt: reconnectAttempts.current, 
            maxAttempts: maxReconnectAttempts 
          });
          
          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setConnectionError('Maximum reconnection attempts reached');
        }
      };

      ws.current.onerror = (error) => {
        logger.websocket('error', { error: String(error) });
        setConnectionError('WebSocket connection error');
        setIsConnecting(false);
      };

    } catch (error) {
      logger.error(error as Error, { context: 'websocket_creation' });
      setConnectionError('Failed to create WebSocket connection');
      setIsConnecting(false);
    }
  }, [buildWebSocketUrl, autoReconnect, reconnectInterval, maxReconnectAttempts]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    reconnectAttempts.current = 0;
  }, []);

  // Reconnect to WebSocket
  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      connect();
    }, 100);
  }, [connect, disconnect]);

  // Send message via WebSocket
  const sendMessage = useCallback((content: string, type: string = 'message') => {
    const message = JSON.stringify({
      type,
      content,
      timestamp: new Date().toISOString()
    });

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(message);
    } else {
      // Queue message for when connection is established
      messageQueue.current.push(message);
      
      // Try to connect if not already connecting
      if (!isConnecting && !isConnected) {
        connect();
      }
    }
  }, [isConnecting, isConnected, connect]);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // CRITICAL: Only run on mount, not when connect/disconnect change
    // Otherwise causes infinite reconnection loop
  }, []);

  // Send periodic ping to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      sendMessage('ping', 'ping');
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // CRITICAL: Only depend on isConnected, not sendMessage
    // sendMessage is stable enough and won't cause issues
  }, [isConnected]);

  return {
    isConnected,
    isConnecting,
    lastMessage,
    connectionError,
    sendMessage,
    connect,
    disconnect,
    reconnect
  };
}

// WebSocket service class for advanced usage
export class WebSocketService {
  private ws: WebSocket | null = null;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();
  private config: WebSocketConfig;

  constructor(config: WebSocketConfig) {
    this.config = config;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.buildWebSocketUrl();
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          logger.websocket('connect', { service: 'WebSocketService', status: 'connected' });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            
            // Call registered handlers
            this.messageHandlers.forEach((handler) => {
              handler(message);
            });
          } catch (error) {
            logger.error(error as Error, { context: 'websocket_service_parse' });
          }
        };

        this.ws.onerror = (error) => {
          logger.websocket('error', { service: 'WebSocketService', error: String(error) });
          reject(error);
        };

        this.ws.onclose = () => {
          logger.websocket('disconnect', { service: 'WebSocketService' });
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendMessage(content: string, type: string = 'message'): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({
        type,
        content,
        timestamp: new Date().toISOString()
      });
      this.ws.send(message);
    }
  }

  onMessage(id: string, handler: (message: WebSocketMessage) => void): void {
    this.messageHandlers.set(id, handler);
  }

  offMessage(id: string): void {
    this.messageHandlers.delete(id);
  }

  private buildWebSocketUrl(): string {
    const { url, conversationId, userId = 'admin', channel = 'admin' } = this.config;
    const wsUrl = new URL(url);
    if (conversationId) wsUrl.searchParams.append('conversation_id', conversationId);
    if (userId) wsUrl.searchParams.append('user_id', userId);
    if (channel) wsUrl.searchParams.append('channel', channel);
    return wsUrl.toString();
  }
}