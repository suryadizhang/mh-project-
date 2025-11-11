# 🔧 Maintenance Alert & Monitoring System Design

**Generated:** November 2025  
**Project:** MyHibachi WebApp  
**Target:** Super Admin Dashboard  
**Purpose:** Proactive system health monitoring and maintenance alerts

---

## 📊 Executive Summary

### System Overview
A comprehensive monitoring dashboard for super admins to track system health, code quality, performance metrics, and receive proactive maintenance alerts.

### Key Features
✅ **Real-time Health Monitoring** - Live system status indicators  
✅ **Automated Alerts** - Proactive notifications for issues  
✅ **Code Quality Tracking** - Monitor technical debt and quality metrics  
✅ **Performance Dashboards** - Track API, WebSocket, and database performance  
✅ **Maintenance Checklists** - Guided system maintenance workflows  
✅ **Error Tracking** - Centralized error aggregation and analysis

---

## 🎯 Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Super Admin Dashboard                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Health    │  │  Alerts &   │  │   Code      │        │
│  │  Monitors   │  │ Maintenance │  │  Quality    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                   Alert Engine                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │  Metric    │  │   Rule     │  │ Notification│          │
│  │ Collectors │  │  Evaluator │  │   Sender    │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└──────────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                   Data Sources                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │   FastAPI  │  │ PostgreSQL │  │   Redis    │          │
│  │   Metrics  │  │   Metrics  │  │  Metrics   │          │
│  └────────────┘  └────────────┘  └────────────┘          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │  WebSocket │  │   Celery   │  │    Logs    │          │
│  │   Metrics  │  │   Metrics  │  │Aggregation │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└──────────────────────────────────────────────────────────┘
```

---

## 🎨 UI/UX Design

### 1. **Super Admin Dashboard Layout**

```typescript
// apps/admin/src/app/super-admin/maintenance/page.tsx

import { SystemHealthWidget } from '@/components/maintenance/SystemHealthWidget';
import { AlertsPanel } from '@/components/maintenance/AlertsPanel';
import { MetricsGrid } from '@/components/maintenance/MetricsGrid';
import { MaintenanceChecklist } from '@/components/maintenance/MaintenanceChecklist';
import { CodeQualityScore } from '@/components/maintenance/CodeQualityScore';

export default function MaintenanceDashboard() {
  return (
    <div className="p-6 space-y-6">
      {/* System Health Overview - Top Banner */}
      <SystemHealthWidget />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Active Alerts */}
        <div className="lg:col-span-2">
          <AlertsPanel />
        </div>

        {/* Right: Code Quality */}
        <div>
          <CodeQualityScore />
        </div>
      </div>

      {/* Performance Metrics */}
      <MetricsGrid />

      {/* Maintenance Checklist */}
      <MaintenanceChecklist />
    </div>
  );
}
```

### 2. **System Health Widget**

Visual representation of overall system health with color-coded indicators.

```typescript
// apps/admin/src/components/maintenance/SystemHealthWidget.tsx

import { AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react';

interface HealthStatus {
  component: string;
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  message: string;
  lastCheck: Date;
  metrics?: {
    label: string;
    value: string;
    threshold?: string;
  }[];
}

export function SystemHealthWidget() {
  const [healthData, setHealthData] = useState<HealthStatus[]>([
    {
      component: 'FastAPI Backend',
      status: 'healthy',
      message: 'All endpoints responding normally',
      lastCheck: new Date(),
      metrics: [
        { label: 'Avg Response Time', value: '45ms', threshold: '<100ms' },
        { label: 'Error Rate', value: '0.2%', threshold: '<1%' },
        { label: 'Uptime', value: '99.98%', threshold: '>99.9%' },
      ],
    },
    {
      component: 'PostgreSQL Database',
      status: 'healthy',
      message: 'Database connections normal',
      lastCheck: new Date(),
      metrics: [
        { label: 'Active Connections', value: '12/100', threshold: '<80' },
        { label: 'Query Time (P95)', value: '23ms', threshold: '<50ms' },
        { label: 'Disk Usage', value: '42%', threshold: '<80%' },
      ],
    },
    {
      component: 'Redis Cache',
      status: 'healthy',
      message: 'Cache hit ratio optimal',
      lastCheck: new Date(),
      metrics: [
        { label: 'Hit Rate', value: '94.2%', threshold: '>90%' },
        { label: 'Memory Usage', value: '1.2GB/4GB', threshold: '<80%' },
        { label: 'Connected Clients', value: '8', threshold: '<100' },
      ],
    },
    {
      component: 'WebSocket Service',
      status: 'healthy',
      message: 'Real-time updates functioning',
      lastCheck: new Date(),
      metrics: [
        { label: 'Active Connections', value: '23', threshold: '<1000' },
        { label: 'Message Latency', value: '12ms', threshold: '<100ms' },
        { label: 'Error Rate', value: '0.0%', threshold: '<0.5%' },
      ],
    },
    {
      component: 'Celery Workers',
      status: 'degraded',
      message: 'High queue backlog detected',
      lastCheck: new Date(),
      metrics: [
        { label: 'Active Workers', value: '2/4', threshold: '>=3' },
        { label: 'Queue Length', value: '45', threshold: '<20' },
        { label: 'Task Failure Rate', value: '3.2%', threshold: '<2%' },
      ],
    },
  ]);

  const getStatusIcon = (status: HealthStatus['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'degraded':
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'down':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'unknown':
        return <Clock className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: HealthStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-50 border-green-200';
      case 'degraded':
        return 'bg-yellow-50 border-yellow-200';
      case 'down':
        return 'bg-red-50 border-red-200';
      case 'unknown':
        return 'bg-gray-50 border-gray-200';
    }
  };

  const overallStatus = healthData.some(h => h.status === 'down')
    ? 'down'
    : healthData.some(h => h.status === 'degraded')
    ? 'degraded'
    : 'healthy';

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Overall Status Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-3">
            {getStatusIcon(overallStatus)}
            <span>System Health</span>
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Last updated: {new Date().toLocaleTimeString()}
          </p>
        </div>
        
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
        >
          Refresh Status
        </button>
      </div>

      {/* Component Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {healthData.map((health) => (
          <div
            key={health.component}
            className={`p-4 rounded-lg border-2 transition-all hover:shadow-md ${getStatusColor(
              health.status
            )}`}
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-semibold text-gray-900">{health.component}</h3>
              {getStatusIcon(health.status)}
            </div>

            <p className="text-sm text-gray-700 mb-3">{health.message}</p>

            {health.metrics && (
              <div className="space-y-1">
                {health.metrics.map((metric) => (
                  <div
                    key={metric.label}
                    className="flex justify-between text-xs"
                  >
                    <span className="text-gray-600">{metric.label}:</span>
                    <span className="font-medium text-gray-900">
                      {metric.value}
                      {metric.threshold && (
                        <span className="text-gray-500 ml-1">
                          ({metric.threshold})
                        </span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-3 pt-3 border-t border-gray-200">
              <button className="text-xs text-orange-600 hover:text-orange-700 font-medium">
                View Details →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Visual Design:**

```
┌───────────────────────────────────────────────────────────────┐
│  ✅ System Health                        [Refresh Status]     │
│  Last updated: 2:34:12 PM                                     │
├───────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ FastAPI      │  │ PostgreSQL   │  │ Redis Cache  │       │
│  │ Backend  ✅  │  │ Database ✅  │  │          ✅  │       │
│  │              │  │              │  │              │       │
│  │ All endpoints│  │ Database     │  │ Cache hit    │       │
│  │ responding   │  │ connections  │  │ ratio optimal│       │
│  │              │  │              │  │              │       │
│  │ Response: 45ms│ │ Connections: │  │ Hit Rate:    │       │
│  │ Error: 0.2%  │  │ 12/100       │  │ 94.2%        │       │
│  │ Uptime:99.98%│  │ Query: 23ms  │  │ Memory: 1.2GB│       │
│  │              │  │              │  │              │       │
│  │ View Details→│  │ View Details→│  │ View Details→│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ WebSocket    │  │ Celery       │                         │
│  │ Service  ✅  │  │ Workers  ⚠️  │                         │
│  │              │  │              │                         │
│  │ Real-time    │  │ High queue   │                         │
│  │ updates OK   │  │ backlog      │                         │
│  │              │  │              │                         │
│  │ Connections: │  │ Workers: 2/4 │                         │
│  │ 23           │  │ Queue: 45    │                         │
│  │ Latency: 12ms│  │ Failures:3.2%│                         │
│  │              │  │              │                         │
│  │ View Details→│  │ View Details→│                         │
│  └──────────────┘  └──────────────┘                         │
└───────────────────────────────────────────────────────────────┘
```

---

### 3. **Alerts Panel**

Display active alerts with severity levels and actionable recommendations.

```typescript
// apps/admin/src/components/maintenance/AlertsPanel.tsx

interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  category: 'performance' | 'security' | 'code_quality' | 'system';
  title: string;
  description: string;
  action: string;
  actionLink?: string;
  timestamp: Date;
  dismissed: boolean;
}

export function AlertsPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([
    {
      id: '1',
      severity: 'warning',
      category: 'performance',
      title: 'High Celery Queue Backlog',
      description: '45 tasks pending in queue. Average wait time: 3.5 minutes.',
      action: 'Scale up Celery workers or investigate slow tasks',
      actionLink: '/super-admin/celery',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      dismissed: false,
    },
    {
      id: '2',
      severity: 'info',
      category: 'code_quality',
      title: 'Code Quality Score: 9.1/10',
      description: 'Testing coverage at 7/10. Consider adding unit tests.',
      action: 'Review testing recommendations',
      actionLink: '/super-admin/code-quality',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      dismissed: false,
    },
    {
      id: '3',
      severity: 'critical',
      category: 'security',
      title: 'CVE-2024-1234 Detected',
      description: 'Vulnerable dependency: fastapi[all]==0.104.0',
      action: 'Update to fastapi[all]>=0.105.0',
      actionLink: '/super-admin/dependencies',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      dismissed: false,
    },
  ]);

  const getSeverityStyle = (severity: Alert['severity']) => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: 'bg-red-600',
          text: 'text-red-800',
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          icon: 'bg-yellow-600',
          text: 'text-yellow-800',
        };
      case 'info':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: 'bg-blue-600',
          text: 'text-blue-800',
        };
    }
  };

  const getTimeAgo = (date: Date) => {
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const dismissAlert = (id: string) => {
    setAlerts(alerts.map(a => (a.id === id ? { ...a, dismissed: true } : a)));
  };

  const activeAlerts = alerts.filter(a => !a.dismissed);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">
          Active Alerts ({activeAlerts.length})
        </h2>
        <button className="text-sm text-orange-600 hover:text-orange-700 font-medium">
          View All
        </button>
      </div>

      <div className="space-y-3">
        {activeAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
            <p className="text-gray-600">No active alerts</p>
          </div>
        ) : (
          activeAlerts.map((alert) => {
            const style = getSeverityStyle(alert.severity);
            return (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border-2 ${style.bg} ${style.border}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span
                        className={`w-2 h-2 rounded-full ${style.icon}`}
                      ></span>
                      <span className={`text-xs font-medium uppercase ${style.text}`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs text-gray-500">·</span>
                      <span className="text-xs text-gray-500">
                        {alert.category.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-500">·</span>
                      <span className="text-xs text-gray-500">
                        {getTimeAgo(alert.timestamp)}
                      </span>
                    </div>

                    <h3 className="font-semibold text-gray-900 mb-1">
                      {alert.title}
                    </h3>
                    <p className="text-sm text-gray-700 mb-3">
                      {alert.description}
                    </p>

                    <div className="flex items-center space-x-3">
                      <button className="text-sm text-orange-600 hover:text-orange-700 font-medium">
                        {alert.action} →
                      </button>
                      <button
                        onClick={() => dismissAlert(alert.id)}
                        className="text-sm text-gray-500 hover:text-gray-700"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
```

**Visual Design:**

```
┌───────────────────────────────────────────────────────────────┐
│  Active Alerts (3)                              [View All]    │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 🔴 CRITICAL · security · 30m ago                        │ │
│  │                                                          │ │
│  │ CVE-2024-1234 Detected                                  │ │
│  │ Vulnerable dependency: fastapi[all]==0.104.0            │ │
│  │                                                          │ │
│  │ [Update to fastapi[all]>=0.105.0 →]  [Dismiss]        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 🟡 WARNING · performance · 15m ago                      │ │
│  │                                                          │ │
│  │ High Celery Queue Backlog                               │ │
│  │ 45 tasks pending in queue. Average wait: 3.5 minutes.   │ │
│  │                                                          │ │
│  │ [Scale up Celery workers →]  [Dismiss]                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 🔵 INFO · code_quality · 2h ago                         │ │
│  │                                                          │ │
│  │ Code Quality Score: 9.1/10                              │ │
│  │ Testing coverage at 7/10. Consider adding unit tests.   │ │
│  │                                                          │ │
│  │ [Review testing recommendations →]  [Dismiss]           │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

---

### 4. **Code Quality Score Widget**

Display real-time code quality metrics based on audit results.

```typescript
// apps/admin/src/components/maintenance/CodeQualityScore.tsx

interface CodeQualityMetrics {
  overall: number;
  architecture: number;
  security: number;
  performance: number;
  testing: number;
  lastAudit: Date;
  trends: {
    metric: string;
    change: number;
  }[];
}

export function CodeQualityScore() {
  const [metrics] = useState<CodeQualityMetrics>({
    overall: 9.1,
    architecture: 10.0,
    security: 10.0,
    performance: 9.5,
    testing: 7.0,
    lastAudit: new Date(),
    trends: [
      { metric: 'Architecture', change: 0 },
      { metric: 'Security', change: +0.5 },
      { metric: 'Performance', change: +0.2 },
      { metric: 'Testing', change: -0.5 },
    ],
  });

  const getScoreColor = (score: number) => {
    if (score >= 9) return 'text-green-600';
    if (score >= 7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score: number) => {
    if (score >= 9) return 'bg-green-100';
    if (score >= 7) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Code Quality</h2>

      {/* Overall Score Circle */}
      <div className="flex flex-col items-center mb-6">
        <div
          className={`w-32 h-32 rounded-full ${getScoreBg(
            metrics.overall
          )} flex items-center justify-center`}
        >
          <div className="text-center">
            <div className={`text-4xl font-bold ${getScoreColor(metrics.overall)}`}>
              {metrics.overall}
            </div>
            <div className="text-xs text-gray-600">/ 10</div>
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-3">
          Last audit: {metrics.lastAudit.toLocaleDateString()}
        </p>
      </div>

      {/* Individual Metrics */}
      <div className="space-y-3">
        {[
          { label: 'Architecture', score: metrics.architecture },
          { label: 'Security', score: metrics.security },
          { label: 'Performance', score: metrics.performance },
          { label: 'Testing', score: metrics.testing },
        ].map((metric) => (
          <div key={metric.label}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">
                {metric.label}
              </span>
              <span className={`text-sm font-bold ${getScoreColor(metric.score)}`}>
                {metric.score}/10
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  metric.score >= 9
                    ? 'bg-green-600'
                    : metric.score >= 7
                    ? 'bg-yellow-600'
                    : 'bg-red-600'
                }`}
                style={{ width: `${(metric.score / 10) * 100}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {/* Trends */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Recent Trends</h3>
        <div className="space-y-2">
          {metrics.trends.map((trend) => (
            <div key={trend.metric} className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{trend.metric}</span>
              <span
                className={
                  trend.change > 0
                    ? 'text-green-600'
                    : trend.change < 0
                    ? 'text-red-600'
                    : 'text-gray-600'
                }
              >
                {trend.change > 0 ? '+' : ''}
                {trend.change.toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <button className="mt-6 w-full px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors">
        Run Full Audit
      </button>
    </div>
  );
}
```

**Visual Design:**

```
┌──────────────────────────┐
│  Code Quality            │
├──────────────────────────┤
│      ┌────────┐          │
│      │  9.1   │          │
│      │  /10   │          │
│      └────────┘          │
│  Last audit: Nov 5, 2025 │
│                          │
│  Architecture            │
│  ████████████ 10/10      │
│                          │
│  Security                │
│  ████████████ 10/10      │
│                          │
│  Performance             │
│  ███████████  9.5/10     │
│                          │
│  Testing                 │
│  ████████     7.0/10     │
│                          │
│  Recent Trends           │
│  Architecture     ±0.0   │
│  Security        +0.5 ↑  │
│  Performance     +0.2 ↑  │
│  Testing         -0.5 ↓  │
│                          │
│  [Run Full Audit]        │
└──────────────────────────┘
```

---

### 5. **Performance Metrics Grid**

Real-time performance dashboards for key services.

```typescript
// apps/admin/src/components/maintenance/MetricsGrid.tsx

export function MetricsGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* API Response Time */}
      <MetricCard
        title="API Response Time"
        value="45ms"
        trend={-5}
        subtitle="Avg last 24h"
        threshold="<100ms"
        status="healthy"
      />

      {/* WebSocket Latency */}
      <MetricCard
        title="WebSocket Latency"
        value="12ms"
        trend={+2}
        subtitle="Real-time updates"
        threshold="<100ms"
        status="healthy"
      />

      {/* Database Query Time */}
      <MetricCard
        title="DB Query Time (P95)"
        value="23ms"
        trend={-8}
        subtitle="95th percentile"
        threshold="<50ms"
        status="healthy"
      />

      {/* Celery Task Queue */}
      <MetricCard
        title="Celery Queue"
        value="45"
        trend={+15}
        subtitle="Pending tasks"
        threshold="<20"
        status="warning"
      />

      {/* Error Rate */}
      <MetricCard
        title="Error Rate"
        value="0.2%"
        trend={-0.1}
        subtitle="Last 24h"
        threshold="<1%"
        status="healthy"
      />

      {/* Cache Hit Rate */}
      <MetricCard
        title="Cache Hit Rate"
        value="94.2%"
        trend={+2.5}
        subtitle="Redis cache"
        threshold=">90%"
        status="healthy"
      />

      {/* Active Users */}
      <MetricCard
        title="Active Sessions"
        value="234"
        trend={+12}
        subtitle="Current users"
        threshold="-"
        status="healthy"
      />

      {/* Memory Usage */}
      <MetricCard
        title="Memory Usage"
        value="62%"
        trend={+5}
        subtitle="Backend server"
        threshold="<80%"
        status="healthy"
      />
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string;
  trend: number;
  subtitle: string;
  threshold: string;
  status: 'healthy' | 'warning' | 'critical';
}

function MetricCard({ title, value, trend, subtitle, threshold, status }: MetricCardProps) {
  const statusColors = {
    healthy: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
    critical: 'border-red-200 bg-red-50',
  };

  return (
    <div className={`p-4 rounded-lg border-2 ${statusColors[status]}`}>
      <h3 className="text-sm font-medium text-gray-600 mb-1">{title}</h3>
      <div className="flex items-baseline space-x-2">
        <span className="text-3xl font-bold text-gray-900">{value}</span>
        {trend !== 0 && (
          <span
            className={`text-sm ${
              trend > 0 ? 'text-red-600' : 'text-green-600'
            }`}
          >
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}
          </span>
        )}
      </div>
      <p className="text-xs text-gray-600 mt-1">{subtitle}</p>
      <p className="text-xs text-gray-500 mt-2">Threshold: {threshold}</p>
    </div>
  );
}
```

---

### 6. **Maintenance Checklist**

Guided maintenance workflows with automation suggestions.

```typescript
// apps/admin/src/components/maintenance/MaintenanceChecklist.tsx

interface MaintenanceTask {
  id: string;
  category: 'daily' | 'weekly' | 'monthly';
  title: string;
  description: string;
  automated: boolean;
  lastRun?: Date;
  nextRun?: Date;
  status: 'pending' | 'completed' | 'failed';
  action?: () => void;
}

export function MaintenanceChecklist() {
  const [tasks] = useState<MaintenanceTask[]>([
    {
      id: '1',
      category: 'daily',
      title: 'Database Backup',
      description: 'Automated PostgreSQL backup to S3',
      automated: true,
      lastRun: new Date(Date.now() - 2 * 60 * 60 * 1000),
      nextRun: new Date(Date.now() + 22 * 60 * 60 * 1000),
      status: 'completed',
    },
    {
      id: '2',
      category: 'daily',
      title: 'Log Rotation',
      description: 'Compress and archive old log files',
      automated: true,
      lastRun: new Date(Date.now() - 12 * 60 * 60 * 1000),
      nextRun: new Date(Date.now() + 12 * 60 * 60 * 1000),
      status: 'completed',
    },
    {
      id: '3',
      category: 'weekly',
      title: 'Security Updates',
      description: 'Check for CVEs and update dependencies',
      automated: false,
      lastRun: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
      nextRun: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
      status: 'pending',
    },
    {
      id: '4',
      category: 'weekly',
      title: 'Performance Audit',
      description: 'Review slow queries and optimize',
      automated: false,
      lastRun: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      nextRun: new Date(),
      status: 'pending',
    },
    {
      id: '5',
      category: 'monthly',
      title: 'Code Quality Audit',
      description: 'Run comprehensive code quality analysis',
      automated: false,
      lastRun: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
      nextRun: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000),
      status: 'completed',
    },
  ]);

  const getTimeUntil = (date: Date) => {
    const seconds = Math.floor((date.getTime() - Date.now()) / 1000);
    if (seconds < 0) return 'Overdue';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Maintenance Checklist</h2>

      {['daily', 'weekly', 'monthly'].map((category) => (
        <div key={category} className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 uppercase mb-3">
            {category} Tasks
          </h3>
          <div className="space-y-2">
            {tasks
              .filter((t) => t.category === category)
              .map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={task.status === 'completed'}
                      className="w-5 h-5 text-orange-600"
                    />
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-gray-900">{task.title}</h4>
                        {task.automated && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                            Auto
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{task.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">
                      Next: {task.nextRun ? getTimeUntil(task.nextRun) : 'N/A'}
                    </p>
                    {!task.automated && (
                      <button className="text-xs text-orange-600 hover:text-orange-700 font-medium">
                        Run Now
                      </button>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## 🔔 Alert Engine Implementation

### Backend Service

```python
# apps/backend/app/services/alert_service.py

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class AlertCategory(str, Enum):
    PERFORMANCE = "performance"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    SYSTEM = "system"

@dataclass
class Alert:
    id: str
    severity: AlertSeverity
    category: AlertCategory
    title: str
    description: str
    action: str
    action_link: Optional[str]
    timestamp: datetime
    dismissed: bool = False

class AlertService:
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client
        self.alert_rules = self._load_alert_rules()
    
    def _load_alert_rules(self):
        """Define alert thresholds and rules"""
        return {
            "api_response_time": {
                "threshold": 100,  # ms
                "severity": AlertSeverity.WARNING,
                "category": AlertCategory.PERFORMANCE,
            },
            "celery_queue_length": {
                "threshold": 20,
                "severity": AlertSeverity.WARNING,
                "category": AlertCategory.PERFORMANCE,
            },
            "error_rate": {
                "threshold": 1.0,  # %
                "severity": AlertSeverity.CRITICAL,
                "category": AlertCategory.SYSTEM,
            },
            "database_connections": {
                "threshold": 80,  # % of max
                "severity": AlertSeverity.WARNING,
                "category": AlertCategory.PERFORMANCE,
            },
        }
    
    async def evaluate_metrics(self):
        """Check all metrics against alert rules"""
        alerts: List[Alert] = []
        
        # Check API response time
        avg_response_time = await self._get_avg_response_time()
        if avg_response_time > self.alert_rules["api_response_time"]["threshold"]:
            alerts.append(Alert(
                id=f"api_response_{datetime.now().timestamp()}",
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PERFORMANCE,
                title="High API Response Time",
                description=f"Average response time: {avg_response_time}ms (threshold: 100ms)",
                action="Review slow endpoints and optimize queries",
                action_link="/super-admin/performance",
                timestamp=datetime.now(),
            ))
        
        # Check Celery queue
        queue_length = await self._get_celery_queue_length()
        if queue_length > self.alert_rules["celery_queue_length"]["threshold"]:
            alerts.append(Alert(
                id=f"celery_queue_{datetime.now().timestamp()}",
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PERFORMANCE,
                title="High Celery Queue Backlog",
                description=f"{queue_length} tasks pending (threshold: 20)",
                action="Scale up Celery workers or investigate slow tasks",
                action_link="/super-admin/celery",
                timestamp=datetime.now(),
            ))
        
        # Check error rate
        error_rate = await self._get_error_rate()
        if error_rate > self.alert_rules["error_rate"]["threshold"]:
            alerts.append(Alert(
                id=f"error_rate_{datetime.now().timestamp()}",
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.SYSTEM,
                title="High Error Rate Detected",
                description=f"Error rate: {error_rate}% (threshold: 1%)",
                action="Check logs for recurring errors",
                action_link="/super-admin/logs",
                timestamp=datetime.now(),
            ))
        
        # Store alerts in Redis
        for alert in alerts:
            await self._store_alert(alert)
        
        return alerts
    
    async def _get_avg_response_time(self) -> float:
        """Get average API response time from metrics"""
        # Implementation: Query Prometheus or metrics database
        pass
    
    async def _get_celery_queue_length(self) -> int:
        """Get current Celery queue length"""
        # Implementation: Query Celery broker
        pass
    
    async def _get_error_rate(self) -> float:
        """Calculate error rate percentage"""
        # Implementation: Query error tracking service
        pass
    
    async def _store_alert(self, alert: Alert):
        """Store alert in Redis for quick access"""
        key = f"alert:{alert.id}"
        await self.redis.setex(
            key,
            timedelta(days=7),  # Keep alerts for 7 days
            alert.model_dump_json()
        )
    
    async def get_active_alerts(self) -> List[Alert]:
        """Retrieve all active (non-dismissed) alerts"""
        keys = await self.redis.keys("alert:*")
        alerts = []
        
        for key in keys:
            data = await self.redis.get(key)
            alert = Alert.model_validate_json(data)
            if not alert.dismissed:
                alerts.append(alert)
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    async def dismiss_alert(self, alert_id: str):
        """Mark alert as dismissed"""
        key = f"alert:{alert_id}"
        data = await self.redis.get(key)
        
        if data:
            alert = Alert.model_validate_json(data)
            alert.dismissed = True
            await self.redis.setex(
                key,
                timedelta(days=7),
                alert.model_dump_json()
            )
```

### API Endpoints

```python
# apps/backend/app/api/maintenance.py

from fastapi import APIRouter, Depends
from app.services.alert_service import AlertService
from app.core.deps import get_alert_service, get_current_super_admin

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

@router.get("/alerts")
async def get_alerts(
    alert_service: AlertService = Depends(get_alert_service),
    current_user = Depends(get_current_super_admin)
):
    """Get all active alerts"""
    alerts = await alert_service.get_active_alerts()
    return {"alerts": alerts}

@router.post("/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    alert_service: AlertService = Depends(get_alert_service),
    current_user = Depends(get_current_super_admin)
):
    """Dismiss an alert"""
    await alert_service.dismiss_alert(alert_id)
    return {"status": "dismissed"}

@router.get("/health")
async def get_system_health(
    current_user = Depends(get_current_super_admin)
):
    """Get system health status"""
    # Implementation: Aggregate health from all services
    pass

@router.get("/metrics")
async def get_performance_metrics(
    current_user = Depends(get_current_super_admin)
):
    """Get performance metrics"""
    # Implementation: Query Prometheus or metrics database
    pass
```

### Celery Task for Periodic Evaluation

```python
# apps/backend/app/services/celery_tasks.py

from celery import Celery
from app.services.alert_service import AlertService

@app.task
async def evaluate_alerts():
    """Periodic task to evaluate metrics and generate alerts"""
    alert_service = AlertService(db_session, redis_client)
    alerts = await alert_service.evaluate_metrics()
    
    # Send notifications for critical alerts
    critical_alerts = [a for a in alerts if a.severity == "critical"]
    for alert in critical_alerts:
        await send_admin_notification(alert)

# Schedule: Run every 5 minutes
app.conf.beat_schedule = {
    'evaluate-alerts': {
        'task': 'tasks.evaluate_alerts',
        'schedule': 300.0,  # 5 minutes
    },
}
```

---

## 🚀 Implementation Roadmap

### ✅ Existing Infrastructure (Already Built)
1. ✅ FastAPI backend with WebSocket real-time updates
2. ✅ Celery task system with Redis broker
3. ✅ WhatsApp notifications (Twilio integration)
4. ✅ RingCentral SMS/Voice system
5. ✅ PostgreSQL database
6. ✅ Next.js 15 frontend with TypeScript
7. ✅ Redis caching layer

### Phase 1: Alert System Backend (Week 1)
**Leverage Existing: WhatsApp + RingCentral for notifications**

1. ⏳ Create AlertService (apps/backend/app/services/alert_service.py)
   - Alert thresholds and rules
   - Metric evaluation logic
   - Redis storage for alerts

2. ⏳ Create API endpoints (apps/backend/app/api/maintenance.py)
   - GET /api/maintenance/alerts
   - POST /api/maintenance/alerts/{id}/dismiss
   - GET /api/maintenance/health
   - GET /api/maintenance/metrics

3. ⏳ Create AlertNotification model (apps/backend/app/models/alert_notification.py)
   - alert_id, admin_phone, notification_method (whatsapp/sms)
   - Use existing WhatsApp/RingCentral services

4. ⏳ Extend Celery tasks (apps/backend/app/services/celery_tasks.py)
   - evaluate_alerts() - runs every 5 minutes
   - send_alert_notification() - uses WhatsApp/RingCentral
   - Reuse existing notification infrastructure

### Phase 2: Frontend Dashboard (Week 2)
**Create 5 React components**

1. ⏳ apps/admin/src/app/super-admin/maintenance/page.tsx (main dashboard)
2. ⏳ apps/admin/src/components/maintenance/SystemHealthWidget.tsx
3. ⏳ apps/admin/src/components/maintenance/AlertsPanel.tsx
4. ⏳ apps/admin/src/components/maintenance/CodeQualityScore.tsx
5. ⏳ apps/admin/src/components/maintenance/MetricsGrid.tsx
6. ⏳ apps/admin/src/components/maintenance/MaintenanceChecklist.tsx
7. ⏳ apps/admin/src/components/maintenance/AlertSubscriptionSettings.tsx (manage notification phone numbers)

### Phase 3: Performance Optimizations (Week 3)
**Implement priority recommendations from PERFORMANCE_ANALYSIS_RECOMMENDATIONS.md**

**Backend:**
1. ⏳ Add database indexes for common queries
   - escalations(status, created_at)
   - escalations(priority, status)
   - escalations(customer_phone)

2. ⏳ Implement Redis caching for stats endpoints
   - Cache escalation counts (60s TTL)
   - Cache dashboard metrics (30s TTL)

3. ⏳ Add API pagination
   - Cursor-based pagination for escalations list

4. ⏳ Optimize WebSocket message batching
   - Batch updates within 500ms window

**Frontend:**
1. ⏳ Add memoization to EscalationCard component
   - Use React.memo with custom comparison

2. ⏳ Implement dynamic imports for heavy components
   - Lazy load EscalationDetail
   - Lazy load FilterPanel

3. ⏳ Add virtual scrolling for escalation lists
   - Use @tanstack/react-virtual

### Phase 4: Testing (Week 4)
**Improve testing score from 7/10 to 9/10**

1. ⏳ Unit tests for useEscalationWebSocket hook
   - Connection/reconnection logic
   - Message handling
   - Error scenarios

2. ⏳ Unit tests for EscalationService
   - create_escalation()
   - update_escalation()
   - get_escalations()

3. ⏳ Integration tests for WebSocket
   - End-to-end message flow
   - Authentication

4. ⏳ Unit tests for AlertService
   - evaluate_metrics()
   - get_active_alerts()
   - dismiss_alert()

5. ⏳ Component tests for maintenance UI
   - SystemHealthWidget rendering
   - AlertsPanel interactions

### Phase 5: Alert Notification Setup (Week 5)
**Admin UI to configure who receives alerts**

1. ⏳ Super admin settings page
   - Add/remove notification recipients
   - Choose notification method (WhatsApp/SMS)
   - Set alert severity filters (critical only, warning+, all)

2. ⏳ Backend alert routing
   - Query notification preferences from database
   - Route to WhatsApp or RingCentral based on preference
   - Respect severity filters

3. ⏳ Alert templates
   - Format alerts for WhatsApp
   - Format alerts for SMS
   - Include actionable links

**Example WhatsApp Alert:**
```
🔴 CRITICAL ALERT
High Celery Queue Backlog

45 tasks pending (threshold: 20)
Avg wait: 3.5 minutes

Action: Scale up Celery workers
View: https://admin.myhibachi.com/super-admin/celery

Reply DISMISS to dismiss this alert
```

**Example SMS Alert:**
```
[CRITICAL] High Celery Queue Backlog
45 tasks pending (>20). 
View: admin.myhibachi.com/super-admin/celery
```

---

## 📊 Success Metrics

### Key Performance Indicators
- **MTTR (Mean Time To Resolution):** <30 minutes for critical issues
- **Alert Precision:** >90% (minimize false positives)
- **System Uptime:** >99.9%
- **Admin Response Time:** <5 minutes for critical alerts
- **Maintenance Task Completion:** >95% on time

---

## 🎯 Conclusion

This maintenance alert system provides:
✅ **Proactive Monitoring** - Detect issues before they impact users  
✅ **Actionable Insights** - Clear recommendations for each alert  
✅ **Automation** - Reduce manual maintenance overhead  
✅ **Visibility** - Centralized dashboard for system health  
✅ **Scalability** - Architecture supports future growth

**Next Steps:**
1. Review this design with stakeholders
2. Prioritize features based on business needs
3. Begin Phase 1 implementation
4. Iterate based on feedback

---

**Document Status:** Draft for Review  
**Owner:** Development Team  
**Last Updated:** November 2025
