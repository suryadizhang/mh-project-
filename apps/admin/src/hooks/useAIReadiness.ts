/**
 * useAIReadiness Hook
 *
 * Custom React hook for AI Readiness monitoring with auto-refresh
 * Manages state for dashboard, alerts, and real-time updates.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { AIReadinessService } from '@/services/aiReadinessService';
import type {
  Alert,
  IntentReadiness,
  IntentType,
  ReadinessDashboard,
  RoutingStats,
  SystemConfig,
} from '@/types/aiReadiness';

interface UseAIReadinessOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
  onError?: (error: Error) => void;
}

interface UseAIReadinessReturn {
  // Data
  dashboard: ReadinessDashboard | null;
  alerts: Alert[];
  routingStats: RoutingStats | null;
  config: SystemConfig | null;

  // Loading states
  loading: boolean;
  refreshing: boolean;

  // Errors
  error: Error | null;

  // Actions
  refresh: () => Promise<void>;
  updateTrafficSplit: (intent: IntentType, percentage: number) => Promise<void>;
  enableAI: (
    reason: string,
    intents?: IntentType[],
    startPercentage?: number
  ) => Promise<void>;
  disableAI: (reason: string, emergency?: boolean) => Promise<void>;
  rollbackIntent: (intent: IntentType, reason: string) => Promise<void>;
  dismissAlert: (alertId: string) => void;

  // Utility
  getIntentReadiness: (intent: IntentType) => IntentReadiness | null;
  isReady: boolean;
  canActivate: boolean;
}

/**
 * Main hook for AI Readiness management
 */
export function useAIReadiness(
  options: UseAIReadinessOptions = {}
): UseAIReadinessReturn {
  const {
    autoRefresh = true,
    refreshInterval = 30000, // 30 seconds
    onError,
  } = options;

  // State
  const [dashboard, setDashboard] = useState<ReadinessDashboard | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [routingStats, setRoutingStats] = useState<RoutingStats | null>(null);
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Refs for interval management
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  /**
   * Fetch all dashboard data
   */
  const fetchData = useCallback(
    async (isRefresh = false) => {
      if (!isMountedRef.current) return;

      try {
        if (isRefresh) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        setError(null);

        // Fetch dashboard data (includes alerts and routing stats)
        const dashboardData = await AIReadinessService.getDashboard();

        if (!isMountedRef.current) return;

        setDashboard(dashboardData);
        setAlerts(dashboardData.recent_alerts || []);
        setRoutingStats(dashboardData.routing_stats);

        // Optionally fetch config on initial load
        if (!isRefresh && !config) {
          const configData = await AIReadinessService.getConfig();
          if (isMountedRef.current) {
            setConfig(configData);
          }
        }
      } catch (err) {
        const error =
          err instanceof Error
            ? err
            : new Error('Failed to fetch AI readiness data');

        if (isMountedRef.current) {
          setError(error);
          if (onError) {
            onError(error);
          }
        }

        console.error('useAIReadiness fetch error:', error);
      } finally {
        if (isMountedRef.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [config, onError]
  );

  /**
   * Manual refresh
   */
  const refresh = useCallback(async () => {
    await fetchData(true);
  }, [fetchData]);

  /**
   * Update traffic split for an intent
   */
  const updateTrafficSplit = useCallback(
    async (intent: IntentType, percentage: number) => {
      try {
        await AIReadinessService.updateTrafficSplit(intent, percentage);
        await refresh(); // Refresh data after update
      } catch (err) {
        const error =
          err instanceof Error
            ? err
            : new Error('Failed to update traffic split');
        setError(error);
        if (onError) {
          onError(error);
        }
        throw error;
      }
    },
    [refresh, onError]
  );

  /**
   * Enable local AI (one-click activation)
   */
  const enableAI = useCallback(
    async (
      reason: string,
      intents?: IntentType[],
      startPercentage?: number
    ) => {
      try {
        await AIReadinessService.enableLocalAI({
          reason,
          enable_intents: intents,
          start_percentage: startPercentage,
        });
        await refresh(); // Refresh data after activation
      } catch (err) {
        const error =
          err instanceof Error ? err : new Error('Failed to enable local AI');
        setError(error);
        if (onError) {
          onError(error);
        }
        throw error;
      }
    },
    [refresh, onError]
  );

  /**
   * Disable local AI
   */
  const disableAI = useCallback(
    async (reason: string, emergency = false) => {
      try {
        await AIReadinessService.disableLocalAI({ reason, emergency });
        await refresh(); // Refresh data after disabling
      } catch (err) {
        const error =
          err instanceof Error ? err : new Error('Failed to disable local AI');
        setError(error);
        if (onError) {
          onError(error);
        }
        throw error;
      }
    },
    [refresh, onError]
  );

  /**
   * Rollback an intent
   */
  const rollbackIntent = useCallback(
    async (intent: IntentType, reason: string) => {
      try {
        await AIReadinessService.rollbackIntent(intent, reason);
        await refresh(); // Refresh data after rollback
      } catch (err) {
        const error =
          err instanceof Error ? err : new Error('Failed to rollback intent');
        setError(error);
        if (onError) {
          onError(error);
        }
        throw error;
      }
    },
    [refresh, onError]
  );

  /**
   * Dismiss an alert (local state only)
   */
  const dismissAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  }, []);

  /**
   * Get readiness for a specific intent
   */
  const getIntentReadiness = useCallback(
    (intent: IntentType): IntentReadiness | null => {
      if (!dashboard?.intent_breakdown) return null;
      return dashboard.intent_breakdown[intent] || null;
    },
    [dashboard]
  );

  // Computed values
  const isReady = dashboard?.overall_readiness.status === 'ready';
  const canActivate = dashboard?.overall_readiness.can_activate || false;

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh setup
  useEffect(() => {
    if (!autoRefresh) return;

    intervalRef.current = setInterval(() => {
      fetchData(true);
    }, refreshInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, fetchData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    // Data
    dashboard,
    alerts,
    routingStats,
    config,

    // Loading states
    loading,
    refreshing,

    // Errors
    error,

    // Actions
    refresh,
    updateTrafficSplit,
    enableAI,
    disableAI,
    rollbackIntent,
    dismissAlert,

    // Utility
    getIntentReadiness,
    isReady,
    canActivate,
  };
}

/**
 * Lightweight hook for just shadow learning stats
 */
export function useShadowLearningStats(
  autoRefresh = true,
  refreshInterval = 30000
) {
  const [stats, setStats] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      const data = await AIReadinessService.getShadowStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error('Failed to fetch shadow stats')
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();

    if (autoRefresh) {
      const interval = setInterval(fetchStats, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchStats, autoRefresh, refreshInterval]);

  return { stats, loading, error, refresh: fetchStats };
}

/**
 * Hook for Ollama health monitoring
 */
export function useOllamaHealth(autoRefresh = true, refreshInterval = 60000) {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const data = await AIReadinessService.checkOllamaHealth();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error('Failed to check Ollama health')
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();

    if (autoRefresh) {
      const interval = setInterval(checkHealth, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [checkHealth, autoRefresh, refreshInterval]);

  return { health, loading, error, checkHealth };
}

export default useAIReadiness;
