/**
 * Unit tests for useEscalationWebSocket hook
 * Tests WebSocket connection, message handling, reconnection, and error scenarios
 */

import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useEscalationWebSocket } from '../useEscalationWebSocket';

// Mock WebSocket
class MockWebSocket {
  url: string;
  readyState: number = WebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 10);
  }

  send(data: string) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    // Mock implementation - data is intentionally not used in test
    void data;
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }

  // Test helpers
  simulateMessage(data: unknown) {
    const event = new MessageEvent('message', {
      data: JSON.stringify(data),
    });
    this.onmessage?.(event);
  }

  simulateError() {
    this.onerror?.(new Event('error'));
  }
}

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket as unknown as typeof WebSocket;

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    token: 'test-token',
    isAuthenticated: true,
  }),
}));

describe('useEscalationWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Connection Establishment', () => {
    it('should establish WebSocket connection on mount', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(result.current.isConnecting).toBe(false);
    });

    it('should set initial stats to zero', () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      expect(result.current.stats).toEqual({
        total_active: 0,
        pending: 0,
        assigned: 0,
        in_progress: 0,
      });
    });
  });

  describe('Message Handling', () => {
    it('should handle escalation_created message', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const mockEscalation = {
        id: 'esc-123',
        customer_name: 'John Doe',
        status: 'pending',
        priority: 'high',
      };

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.simulateMessage({
          type: 'escalation_created',
          data: mockEscalation,
        });
      });

      await waitFor(() => {
        expect(result.current.lastEvent).toMatchObject({
          type: 'escalation_created',
          data: mockEscalation,
        });
      });
    });

    it('should handle escalation_updated message', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const mockUpdate = {
        id: 'esc-123',
        status: 'resolved',
      };

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.simulateMessage({
          type: 'escalation_updated',
          data: mockUpdate,
        });
      });

      await waitFor(() => {
        expect(result.current.lastEvent).toMatchObject({
          type: 'escalation_updated',
          data: mockUpdate,
        });
      });
    });

    it('should handle stats_updated message', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const mockStats = {
        total_active: 15,
        pending: 8,
        assigned: 3,
        in_progress: 5,
      };

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.simulateMessage({
          type: 'stats_updated',
          stats: mockStats,
        });
      });

      await waitFor(() => {
        expect(result.current.stats.total_active).toBe(15);
        expect(result.current.stats.pending).toBe(8);
      });
    });

    it('should ignore unknown message types', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const initialLastEvent = result.current.lastEvent;

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.simulateMessage({
          type: 'unknown_type',
          data: { foo: 'bar' },
        });
      });

      // lastEvent should not change for unknown message types
      expect(result.current.lastEvent).toBe(initialLastEvent);
    });

    it('should handle malformed JSON messages gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        // Simulate raw message event with invalid JSON
        const event = new MessageEvent('message', {
          data: 'invalid-json',
        });
        wsInstance?.onmessage?.(event);
      });

      expect(result.current.isConnected).toBe(true); // Should still be connected
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  describe('Reconnection Logic', () => {
    it('should reconnect on connection close', async () => {
      vi.useFakeTimers();

      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.close();
      });

      expect(result.current.isConnected).toBe(false);

      // Wait for reconnection attempt (3 seconds)
      act(() => {
        vi.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(result.current.isConnecting).toBe(true);
      });

      vi.useRealTimers();
    });

    it('should provide manual reconnect method', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.close();
      });

      expect(result.current.isConnected).toBe(false);

      act(() => {
        result.current.reconnect();
      });

      await waitFor(() => {
        expect(result.current.isConnecting).toBe(true);
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle WebSocket errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.simulateError();
      });

      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('should set connectionError on error', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.simulateError();
      });

      await waitFor(() => {
        expect(result.current.connectionError).toBeTruthy();
      });
    });
  });

  describe('Methods', () => {
    it('should provide sendPing method', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(typeof result.current.sendPing).toBe('function');

      act(() => {
        result.current.sendPing();
      });

      // Method should not throw
      expect(result.current.isConnected).toBe(true);
    });

    it('should provide subscribe method', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(typeof result.current.subscribe).toBe('function');

      act(() => {
        result.current.subscribe('esc-123');
      });

      // Method should not throw
      expect(result.current.isConnected).toBe(true);
    });

    it('should provide unsubscribe method', async () => {
      const { result } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(typeof result.current.unsubscribe).toBe('function');

      act(() => {
        result.current.unsubscribe('esc-123');
      });

      // Method should not throw
      expect(result.current.isConnected).toBe(true);
    });
  });

  describe('Cleanup', () => {
    it('should close WebSocket on unmount', async () => {
      const { result, unmount } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
      const closeSpy = vi.spyOn(wsInstance!, 'close');

      unmount();

      expect(closeSpy).toHaveBeenCalled();
    });

    it('should clear reconnection timer on unmount', async () => {
      vi.useFakeTimers();

      const { result, unmount } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      act(() => {
        const wsInstance = (result.current as unknown as { ws: { current: MockWebSocket } }).ws?.current;
        wsInstance?.close();
      });

      unmount();

      // Advance time to check if reconnection happens (it shouldn't)
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      expect(result.current.isConnected).toBe(false);

      vi.useRealTimers();
    });
  });

  describe('Performance', () => {
    it('should not create multiple WebSocket connections on re-render', async () => {
      const connectSpy = vi.spyOn(global, 'WebSocket');

      const { rerender } = renderHook(() => useEscalationWebSocket());

      await waitFor(() => {
        expect(connectSpy).toHaveBeenCalledTimes(1);
      });

      // Trigger multiple re-renders
      rerender();
      rerender();
      rerender();

      // Should still only have one WebSocket connection
      expect(connectSpy).toHaveBeenCalledTimes(1);

      connectSpy.mockRestore();
    });
  });
});

