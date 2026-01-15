'use client';

/**
 * Scaling Health Dashboard
 *
 * Real-time system health monitoring dashboard for super administrators.
 * Displays:
 * - Overall system health status
 * - Database connectivity and pool stats
 * - Redis cache status
 * - System resources (CPU, Memory, Disk)
 * - Process information
 * - API response times
 *
 * @module ScalingDashboard
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  HardDrive,
  MemoryStick,
  RefreshCw,
  Server,
  Settings,
  Wifi,
  WifiOff,
  Zap,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { tokenManager } from '@/services/api';

// ============================================================================
// Types
// ============================================================================

interface ServiceHealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time_ms?: number;
  details: string;
  error?: string;
  timestamp?: string;
}

interface SystemMetrics {
  cpu: {
    count: number;
    usage_percent: number;
  };
  memory: {
    total_gb: number;
    available_gb: number;
    used_gb: number;
    used_percent: number;
  };
  disk: {
    total_gb: number;
    free_gb: number;
    used_gb: number;
    used_percent: number;
  };
  process: {
    pid: number;
    memory_mb: number;
    cpu_percent: number;
    threads: number;
    open_files: number;
  };
  available: boolean;
}

interface DetailedHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime_seconds: number;
  version: string;
  environment: string;
  services: {
    database: ServiceHealthCheck;
    redis: ServiceHealthCheck;
    stripe: ServiceHealthCheck;
  };
  system: SystemMetrics;
  configuration: {
    stripe_configured: boolean;
    email_configured: boolean;
    ai_configured: boolean;
    rate_limiting_enabled: boolean;
    debug_mode: boolean;
    environment: string;
  };
}

interface ReadinessResponse {
  status: 'ready' | 'not_ready';
  timestamp: string;
  checks: {
    database: ServiceHealthCheck;
    redis: ServiceHealthCheck;
    stripe: ServiceHealthCheck;
  };
  ready: boolean;
  details?: string;
}

// ============================================================================
// Utility Functions
// ============================================================================

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

  return parts.join(' ');
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
    case 'ready':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'degraded':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'unhealthy':
    case 'not_ready':
      return 'bg-red-100 text-red-800 border-red-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'healthy':
    case 'ready':
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    case 'degraded':
      return <AlertCircle className="h-5 w-5 text-yellow-600" />;
    case 'unhealthy':
    case 'not_ready':
      return <AlertCircle className="h-5 w-5 text-red-600" />;
    default:
      return <Activity className="h-5 w-5 text-gray-600" />;
  }
}

function getProgressColor(percent: number): string {
  if (percent < 50) return 'bg-green-500';
  if (percent < 75) return 'bg-yellow-500';
  if (percent < 90) return 'bg-orange-500';
  return 'bg-red-500';
}

// ============================================================================
// Sub-components
// ============================================================================

function ServiceStatusCard({
  name,
  service,
  icon: Icon,
}: {
  name: string;
  service: ServiceHealthCheck;
  icon: React.ElementType;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Icon className="h-6 w-6 text-gray-600" />
            </div>
            <div>
              <h3 className="font-semibold">{name}</h3>
              <p className="text-sm text-gray-500">{service.details}</p>
            </div>
          </div>
          <Badge className={getStatusColor(service.status)}>
            {service.status}
          </Badge>
        </div>
        {service.response_time_ms && (
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
            <Clock className="h-4 w-4" />
            <span>{service.response_time_ms.toFixed(2)}ms response time</span>
          </div>
        )}
        {service.error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            {service.error}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ResourceProgressBar({
  label,
  used,
  total,
  unit,
  icon: Icon,
}: {
  label: string;
  used: number;
  total: number;
  unit: string;
  icon: React.ElementType;
}) {
  const percent = (used / total) * 100;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium">{label}</span>
        </div>
        <span className="text-sm text-gray-500">
          {used.toFixed(1)} / {total.toFixed(1)} {unit} ({percent.toFixed(1)}%)
        </span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getProgressColor(percent)}`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </div>
  );
}

function ProcessInfoCard({ process }: { process: SystemMetrics['process'] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Server className="h-5 w-5" />
          Process Information
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">{process.pid}</p>
            <p className="text-sm text-gray-500">PID</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-purple-600">
              {process.memory_mb.toFixed(0)}
            </p>
            <p className="text-sm text-gray-500">Memory (MB)</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-green-600">
              {process.threads}
            </p>
            <p className="text-sm text-gray-500">Threads</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-orange-600">
              {process.open_files}
            </p>
            <p className="text-sm text-gray-500">Open Files</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ConfigurationStatus({
  config,
}: {
  config: DetailedHealthResponse['configuration'];
}) {
  const configItems = [
    { key: 'Stripe', value: config.stripe_configured },
    { key: 'Email', value: config.email_configured },
    { key: 'AI Services', value: config.ai_configured },
    { key: 'Rate Limiting', value: config.rate_limiting_enabled },
    { key: 'Debug Mode', value: config.debug_mode, invertColor: true },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Settings className="h-5 w-5" />
          Configuration Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {configItems.map(item => (
            <div key={item.key} className="flex items-center justify-between">
              <span className="text-sm">{item.key}</span>
              <Badge
                variant="outline"
                className={
                  item.invertColor
                    ? item.value
                      ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
                      : 'bg-green-50 text-green-700 border-green-200'
                    : item.value
                      ? 'bg-green-50 text-green-700 border-green-200'
                      : 'bg-gray-50 text-gray-500 border-gray-200'
                }
              >
                {item.value
                  ? item.invertColor
                    ? 'Enabled'
                    : 'Configured'
                  : 'Not Configured'}
              </Badge>
            </div>
          ))}
          <div className="pt-2 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Environment</span>
              <Badge variant="secondary">{config.environment}</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function ScalingDashboardPage() {
  const { isSuperAdmin } = useAuth();
  const [healthData, setHealthData] = useState<DetailedHealthResponse | null>(
    null
  );
  const [readinessData, setReadinessData] = useState<ReadinessResponse | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchHealthData = useCallback(async (showRefreshing = true) => {
    if (showRefreshing) setRefreshing(true);
    setError(null);

    try {
      const token = tokenManager.getToken();
      const baseUrl = process.env.NEXT_PUBLIC_API_URL;

      // Fetch both endpoints in parallel
      const [detailedRes, readinessRes] = await Promise.all([
        fetch(`${baseUrl}/api/v1/health/detailed`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${baseUrl}/api/v1/health/readiness`, {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => null), // Readiness might return 503 if not ready
      ]);

      if (detailedRes.ok) {
        const detailedData = await detailedRes.json();
        setHealthData(detailedData);
      } else {
        throw new Error('Failed to fetch health data');
      }

      if (readinessRes) {
        // Handle both success and 503 responses
        const readinessJson = await readinessRes.json();
        if (readinessRes.ok) {
          setReadinessData(readinessJson);
        } else {
          // Construct a valid ReadinessResponse object for non-OK statuses
          setReadinessData({
            status: 'not_ready',
            timestamp: new Date().toISOString(),
            checks: readinessJson.checks || {},
            ready: false,
            details:
              typeof readinessJson.detail === 'string'
                ? readinessJson.detail
                : 'Service not ready',
          });
        }
      }

      setLastRefresh(new Date());
    } catch (err) {
      console.error('Health data fetch error:', err);
      setError(
        err instanceof Error ? err.message : 'Failed to fetch health data'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchHealthData(false);
  }, [fetchHealthData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchHealthData(false);
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchHealthData]);

  // Access control
  if (!isSuperAdmin) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Access Denied</AlertTitle>
          <AlertDescription>
            Only super administrators can access the scaling dashboard.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/4" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded" />
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  // Error state
  if (error && !healthData) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error Loading Dashboard</AlertTitle>
          <AlertDescription className="flex flex-col gap-2">
            <span>{error}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchHealthData()}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <main
      className="container mx-auto p-6 space-y-6"
      role="main"
      aria-label="Scaling Health Dashboard"
    >
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Activity className="h-8 w-8 text-blue-600" aria-hidden="true" />
            Scaling Health Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Real-time system health monitoring and metrics
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-500" aria-live="polite">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={autoRefresh ? 'bg-green-50' : ''}
              aria-pressed={autoRefresh}
              aria-label={`Auto-refresh is ${autoRefresh ? 'enabled' : 'disabled'}`}
            >
              {autoRefresh ? (
                <Wifi
                  className="h-4 w-4 mr-1 text-green-600"
                  aria-hidden="true"
                />
              ) : (
                <WifiOff className="h-4 w-4 mr-1" aria-hidden="true" />
              )}
              Auto-refresh {autoRefresh ? 'On' : 'Off'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchHealthData()}
              disabled={refreshing}
              aria-label="Refresh health data"
            >
              <RefreshCw
                className={`h-4 w-4 mr-1 ${refreshing ? 'animate-spin' : ''}`}
                aria-hidden="true"
              />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      {/* Overall Status Banner */}
      {healthData && (
        <Card
          className={`border-2 ${
            healthData.status === 'healthy'
              ? 'border-green-300 bg-green-50'
              : healthData.status === 'degraded'
                ? 'border-yellow-300 bg-yellow-50'
                : 'border-red-300 bg-red-50'
          }`}
          role="status"
          aria-live="polite"
        >
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {getStatusIcon(healthData.status)}
                <div>
                  <h2 className="text-xl font-semibold capitalize">
                    System Status: {healthData.status}
                  </h2>
                  <p className="text-sm text-gray-600">
                    Environment: {healthData.environment} | Version:{' '}
                    {healthData.version}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2 text-lg font-medium">
                  <Zap className="h-5 w-5 text-blue-600" />
                  Uptime: {formatUptime(healthData.uptime_seconds)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Service Status Cards */}
      {healthData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ServiceStatusCard
            name="Database"
            service={healthData.services.database}
            icon={Database}
          />
          <ServiceStatusCard
            name="Redis Cache"
            service={healthData.services.redis}
            icon={Server}
          />
          <ServiceStatusCard
            name="Stripe Payments"
            service={healthData.services.stripe}
            icon={Settings}
          />
        </div>
      )}

      {/* System Resources */}
      {healthData?.system?.available && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              System Resources
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <ResourceProgressBar
              label="CPU Usage"
              used={healthData.system.cpu.usage_percent}
              total={100}
              unit="%"
              icon={Cpu}
            />
            <ResourceProgressBar
              label="Memory"
              used={healthData.system.memory.used_gb}
              total={healthData.system.memory.total_gb}
              unit="GB"
              icon={MemoryStick}
            />
            <ResourceProgressBar
              label="Disk Space"
              used={healthData.system.disk.used_gb}
              total={healthData.system.disk.total_gb}
              unit="GB"
              icon={HardDrive}
            />
            <div className="pt-2 text-sm text-gray-500 flex items-center gap-2">
              <Cpu className="h-4 w-4" />
              <span>CPU Cores: {healthData.system.cpu.count}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Process Info & Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {healthData?.system?.process && (
          <ProcessInfoCard process={healthData.system.process} />
        )}
        {healthData?.configuration && (
          <ConfigurationStatus config={healthData.configuration} />
        )}
      </div>

      {/* Readiness Status */}
      {readinessData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              Kubernetes Readiness
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Badge
                className={`text-lg py-1 px-3 ${getStatusColor(readinessData.status)}`}
              >
                {readinessData.status.toUpperCase()}
              </Badge>
              <span className="text-gray-600">
                {readinessData.details || 'All systems operational'}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Footer with timestamp */}
      <footer className="text-center text-sm text-gray-400 pt-4">
        Dashboard auto-refreshes every 30 seconds when enabled.
        <br />
        Data timestamp:{' '}
        {healthData?.timestamp
          ? new Date(healthData.timestamp).toLocaleString()
          : 'N/A'}
      </footer>
    </main>
  );
}
