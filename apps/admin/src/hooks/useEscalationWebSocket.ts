/**
 * WebSocket Hook for Real-time Escalation Updates
 * Connects admins to escalation events in real-time
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/lib/logger';

// Escalation WebSocket message types
export type EscalationEventType =
  | 'connection_established'
  | 'escalation_created'
  | 'escalation_updated'
  | 'escalation_resolved'
  | 'stats_updated'
  | 'pong'
  | 'error';

export interface EscalationData {
  id: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  status?:
    | 'pending'
    | 'assigned'
    | 'in_progress'
    | 'waiting_customer'
    | 'resolved';
  customer_phone?: string;
  reason?: string;
  method?: 'sms' | 'call' | 'email';
  created_at?: string;
  updated_at?: string;
  assigned_to_id?: string;
  assigned_at?: string;
  resolved_by_id?: string;
  resolved_at?: string;
  resolution_notes?: string;
  update_type?: 'assigned' | 'status_change' | 'resolved';
  old_status?: string;
}

export interface EscalationWebSocketMessage {
  type: EscalationEventType;
  data?: EscalationData;
  timestamp?: string;
  connection_id?: string;
  admin_id?: string;
  message?: string;
  escalation_id?: string;
}

export interface EscalationStats {
  pending: number;
  assigned: number;
  in_progress: number;
  total_active: number;
}

export interface UseEscalationWebSocketResult {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  connectionError: string | null;

  // Data
  lastEvent: EscalationWebSocketMessage | null;
  stats: EscalationStats;

  // Methods
  sendPing: () => void;
  subscribe: (escalationId: string) => void;
  unsubscribe: (escalationId: string) => void;
  reconnect: () => void;
}

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1';
const PING_INTERVAL = 30000; // 30 seconds
const RECONNECT_INTERVAL = 3000; // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 5;

export function useEscalationWebSocket(): UseEscalationWebSocketResult {
  const { token, isAuthenticated } = useAuth();

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastEvent, setLastEvent] =
    useState<EscalationWebSocketMessage | null>(null);
  const [stats, setStats] = useState<EscalationStats>({
    pending: 0,
    assigned: 0,
    in_progress: 0,
    total_active: 0,
  });

  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingInterval = useRef<NodeJS.Timeout | null>(null);

  // Build WebSocket URL with JWT token
  const buildWebSocketUrl = useCallback(() => {
    if (!token) {
      throw new Error('No authentication token available');
    }

    const wsUrl = `${WS_BASE_URL}/ws/escalations?token=${encodeURIComponent(token)}`;
    return wsUrl;
  }, [token]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!isAuthenticated || !token) {
      // Silent return - this is expected before authentication completes
      // Not an error, just waiting for auth
      logger.debug('WebSocket connection pending authentication');
      setConnectionError(null); // Clear any previous errors
      return;
    }

    if (ws.current?.readyState === WebSocket.OPEN) {
      logger.info('Already connected to escalation WebSocket');
      return;
    }

    setIsConnecting(true);
    setConnectionError(null);

    try {
      const wsUrl = buildWebSocketUrl();
      logger.info('Connecting to escalation WebSocket', { url: WS_BASE_URL });

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        logger.info('✅ Connected to escalation WebSocket');
        setIsConnected(true);
        setIsConnecting(false);
        setConnectionError(null);
        reconnectAttempts.current = 0;

        // Start ping interval
        if (pingInterval.current) {
          clearInterval(pingInterval.current);
        }
        pingInterval.current = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, PING_INTERVAL);
      };

      ws.current.onmessage = event => {
        try {
          const message: EscalationWebSocketMessage = JSON.parse(event.data);

          logger.info('📨 Escalation WebSocket message', {
            type: message.type,
            escalation_id: message.data?.id,
          });

          setLastEvent(message);

          // Update stats based on message type
          if (message.type === 'escalation_created') {
            setStats(prev => ({
              ...prev,
              pending: prev.pending + 1,
              total_active: prev.total_active + 1,
            }));
          } else if (
            message.type === 'escalation_updated' &&
            message.data?.update_type === 'assigned'
          ) {
            setStats(prev => ({
              ...prev,
              pending: Math.max(0, prev.pending - 1),
              assigned: prev.assigned + 1,
            }));
          } else if (
            message.type === 'escalation_updated' &&
            message.data?.status === 'in_progress'
          ) {
            setStats(prev => ({
              ...prev,
              assigned: Math.max(0, prev.assigned - 1),
              in_progress: prev.in_progress + 1,
            }));
          } else if (message.type === 'escalation_resolved') {
            setStats(prev => ({
              ...prev,
              in_progress: Math.max(0, prev.in_progress - 1),
              total_active: Math.max(0, prev.total_active - 1),
            }));
          } else if (message.type === 'stats_updated' && message.data) {
            // If backend sends full stats, use them
            setStats(message.data as unknown as EscalationStats);
          }
        } catch (error) {
          logger.error(error as Error, {
            context: 'escalation_websocket_parse',
          });
        }
      };

      ws.current.onclose = event => {
        logger.info('🔌 Escalation WebSocket closed', {
          code: event.code,
          reason: event.reason,
        });
        setIsConnected(false);
        setIsConnecting(false);

        // Clear ping interval
        if (pingInterval.current) {
          clearInterval(pingInterval.current);
          pingInterval.current = null;
        }

        // Attempt reconnection if not intentional close
        if (
          event.code !== 1000 &&
          reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS
        ) {
          reconnectAttempts.current++;
          logger.info('🔄 Attempting to reconnect', {
            attempt: reconnectAttempts.current,
            maxAttempts: MAX_RECONNECT_ATTEMPTS,
          });

          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, RECONNECT_INTERVAL);
        } else if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
          setConnectionError('Maximum reconnection attempts reached');
          logger.error(
            new Error('Maximum reconnection attempts reached'),
            { context: 'escalation_websocket' }
          );
        }
      };

      ws.current.onerror = event => {
        // Only log as error if we were authenticated and connection failed
        // Pre-auth connection attempts are normal and expected
        if (isAuthenticated && token) {
          const errorMessage =
            event instanceof ErrorEvent
              ? event.message || 'WebSocket connection error'
              : 'WebSocket connection error';
          logger.error(new Error(errorMessage), {
            context: 'escalation_websocket',
          });
          setConnectionError(errorMessage);
        } else {
          // Silent fail for pre-auth - this is expected
          logger.debug('WebSocket connection not established (awaiting authentication)');
        }
        setIsConnecting(false);
      };
    } catch (error) {
      logger.error(error as Error, {
        context: 'escalation_websocket_creation',
      });
      setConnectionError('Failed to create WebSocket connection');
      setIsConnecting(false);
    }
  }, [isAuthenticated, token, buildWebSocketUrl]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (pingInterval.current) {
      clearInterval(pingInterval.current);
      pingInterval.current = null;
    }

    if (ws.current) {
      ws.current.close(1000, 'Client disconnect');
      ws.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    reconnectAttempts.current = 0;
  }, []);

  // Reconnect to WebSocket
  const reconnect = useCallback(() => {
    logger.info('🔄 Manual reconnect requested');
    disconnect();
    setTimeout(() => {
      connect();
    }, 100);
  }, [connect, disconnect]);

  // Send ping message
  const sendPing = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'ping' }));
      logger.debug('Sent ping to escalation WebSocket');
    }
  }, []);

  // Subscribe to specific escalation updates
  const subscribe = useCallback((escalationId: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(
        JSON.stringify({
          type: 'subscribe',
          escalation_id: escalationId,
        })
      );
      logger.info('Subscribed to escalation', { escalationId });
    }
  }, []);

  // Unsubscribe from specific escalation updates
  const unsubscribe = useCallback((escalationId: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(
        JSON.stringify({
          type: 'unsubscribe',
          escalation_id: escalationId,
        })
      );
      logger.info('Unsubscribed from escalation', { escalationId });
    }
  }, []);

  // Auto-connect on mount if authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // CRITICAL: Only run when authentication changes, not when connect/disconnect change
    // Otherwise causes infinite reconnection loop
  }, [isAuthenticated, token]);

  return {
    isConnected,
    isConnecting,
    connectionError,
    lastEvent,
    stats,
    sendPing,
    subscribe,
    unsubscribe,
    reconnect,
  };
}
