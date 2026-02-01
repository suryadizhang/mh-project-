'use client';

/**
 * Email Monitor Tab Component
 * ===========================
 *
 * Displays real-time status of email monitoring systems:
 * - Gmail Monitor (Payment Notifications)
 * - IONOS Monitor (Customer Support)
 *
 * Uses the /api/v1/health/email-monitors endpoint for data.
 *
 * @see apps/backend/src/routers/v1/health.py for endpoint
 * @see apps/backend/src/workers/email_monitoring_tasks.py for tasks
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Mail,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Loader2,
  Activity,
  Server,
} from 'lucide-react';
import { toast } from 'sonner';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { apiFetch } from '@/lib/api';

// ========== Types ==========

interface MonitorStatus {
  status: 'healthy' | 'degraded' | 'error' | 'unknown';
  last_check: string | null;
  last_success: string | null;
  last_error: string | null;
  consecutive_failures: number;
  emails_processed_today: number;
  credentials_valid: boolean;
}

interface EmailMonitorHealth {
  status: 'healthy' | 'degraded' | 'critical' | 'unknown';
  timestamp: string;
  monitors: {
    gmail: MonitorStatus;
    ionos: MonitorStatus;
  };
  celery_status: {
    worker_active: boolean;
    beat_active: boolean;
    last_heartbeat: string | null;
  };
}

// ========== Helper Functions ==========

function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-500';
    case 'degraded':
      return 'bg-yellow-500';
    case 'error':
    case 'critical':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
}

function getStatusBadgeVariant(
  status: string
): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'healthy':
      return 'default';
    case 'degraded':
      return 'secondary';
    case 'error':
    case 'critical':
      return 'destructive';
    default:
      return 'outline';
  }
}

function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return 'Never';
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    return date.toLocaleString();
  } catch {
    return timestamp;
  }
}

// ========== Monitor Card Component ==========

interface MonitorCardProps {
  title: string;
  description: string;
  icon: typeof Mail;
  monitor: MonitorStatus;
}

function MonitorCard({
  title,
  description,
  icon: Icon,
  monitor,
}: MonitorCardProps) {
  const statusIcon = {
    healthy: <CheckCircle2 className="h-5 w-5 text-green-500" />,
    degraded: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
    error: <XCircle className="h-5 w-5 text-red-500" />,
    unknown: <Clock className="h-5 w-5 text-gray-400" />,
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-muted-foreground" />
          <div>
            <CardTitle className="text-base font-medium">{title}</CardTitle>
            <CardDescription className="text-xs">{description}</CardDescription>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={getStatusBadgeVariant(monitor.status)}>
            {monitor.status.toUpperCase()}
          </Badge>
          {statusIcon[monitor.status]}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm">
          {/* Left Column */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Check:</span>
              <span className="font-mono">
                {formatTimestamp(monitor.last_check)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Success:</span>
              <span className="font-mono">
                {formatTimestamp(monitor.last_success)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Processed Today:</span>
              <span className="font-mono">
                {monitor.emails_processed_today}
              </span>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Credentials:</span>
              <span
                className={
                  monitor.credentials_valid ? 'text-green-600' : 'text-red-600'
                }
              >
                {monitor.credentials_valid ? '✓ Valid' : '✗ Invalid'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Failures:</span>
              <span
                className={`font-mono ${
                  monitor.consecutive_failures > 0
                    ? 'text-red-600 font-bold'
                    : 'text-green-600'
                }`}
              >
                {monitor.consecutive_failures}
              </span>
            </div>
            {monitor.last_error && (
              <div className="col-span-2">
                <span className="text-muted-foreground">Last Error:</span>
                <p className="text-xs text-red-600 mt-1 font-mono truncate">
                  {monitor.last_error}
                </p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ========== Main Component ==========

export function EmailMonitorTab() {
  const [health, setHealth] = useState<EmailMonitorHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHealth = useCallback(async (showToast = false) => {
    try {
      if (showToast) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const response = await apiFetch<EmailMonitorHealth>(
        '/api/v1/health/email-monitors'
      );

      if (!response.success || !response.data) {
        throw new Error(
          response.error || 'Failed to fetch email monitor health'
        );
      }

      setHealth(response.data);

      if (showToast) {
        toast.success('Email monitor status refreshed');
      }
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'Failed to load email monitor health';
      setError(message);
      if (showToast) {
        toast.error(message);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadHealth();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => loadHealth(), 30000);
    return () => clearInterval(interval);
  }, [loadHealth]);

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !health) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8 text-center">
          <XCircle className="h-12 w-12 mx-auto text-red-500 mb-4" />
          <p className="text-red-600 font-medium">
            Failed to load email monitor status
          </p>
          <p className="text-sm text-red-500 mt-2">{error}</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => loadHealth(true)}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Status Overview */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Email Monitoring Systems</h3>
          <p className="text-sm text-muted-foreground">
            Real-time status of email monitors for payment and customer support
            tracking
          </p>
        </div>
        <div className="flex items-center gap-4">
          {health && (
            <div className="flex items-center gap-2">
              <div
                className={`h-3 w-3 rounded-full ${getStatusColor(
                  health.status
                )}`}
              />
              <span className="text-sm font-medium">
                Overall: {health.status.toUpperCase()}
              </span>
            </div>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadHealth(true)}
            disabled={refreshing}
          >
            {refreshing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
        </div>
      </div>

      {/* Monitor Cards Grid */}
      {health && (
        <div className="grid gap-4 md:grid-cols-2">
          <MonitorCard
            title="Gmail Monitor"
            description="Payment notifications (myhibachichef@gmail.com)"
            icon={Mail}
            monitor={health.monitors.gmail}
          />
          <MonitorCard
            title="IONOS Monitor"
            description="Customer support inbox (cs@myhibachichef.com)"
            icon={Server}
            monitor={health.monitors.ionos}
          />
        </div>
      )}

      {/* Celery Status Card */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-5 w-5" />
              Background Worker Status
            </CardTitle>
            <CardDescription>
              Celery worker and beat scheduler status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <div
                  className={`h-3 w-3 rounded-full ${
                    health.celery_status.worker_active
                      ? 'bg-green-500'
                      : 'bg-red-500'
                  }`}
                />
                <span className="text-sm">
                  Worker:{' '}
                  {health.celery_status.worker_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div
                  className={`h-3 w-3 rounded-full ${
                    health.celery_status.beat_active
                      ? 'bg-green-500'
                      : 'bg-red-500'
                  }`}
                />
                <span className="text-sm">
                  Beat:{' '}
                  {health.celery_status.beat_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                Last Heartbeat:{' '}
                {formatTimestamp(health.celery_status.last_heartbeat)}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-blue-800">
                Email Monitor Schedule
              </p>
              <ul className="mt-2 space-y-1 text-blue-700">
                <li>
                  • Email checks run every <strong>5 minutes</strong>
                </li>
                <li>
                  • Health check runs every <strong>10 minutes</strong>
                </li>
                <li>
                  • Alerts trigger after <strong>3 consecutive failures</strong>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default EmailMonitorTab;
