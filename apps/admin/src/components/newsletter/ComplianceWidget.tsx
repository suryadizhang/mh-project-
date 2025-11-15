'use client';

import { AlertTriangle, CheckCircle, RefreshCw, ShieldCheck, XCircle } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

interface ComplianceMetrics {
  consent_rate: number;
  unsubscribe_rate: number;
  delivery_success_rate: number;
  complaint_rate: number;
  total_subscribers: number;
  sms_consented: number;
  pending_unsubscribes: number;
  compliance_score: number;
  violations: Array<{
    type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    count: number;
  }>;
}

export function ComplianceWidget() {
  const [metrics, setMetrics] = useState<ComplianceMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchComplianceMetrics = useCallback(async () => {
    const loading = metrics === null ? setIsLoading : setIsRefreshing;
    loading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/newsletter/compliance/metrics`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch compliance metrics');

      const data = await response.json();
      setMetrics(data);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [metrics]);

  useEffect(() => {
    fetchComplianceMetrics();

    // Set up WebSocket connection for real-time updates
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(`${wsUrl}/ws/compliance-updates`);

      ws.onopen = () => {
        console.log('Connected to compliance updates WebSocket');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'compliance_update') {
          fetchComplianceMetrics();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };
    } catch (err) {
      console.error('Failed to establish WebSocket connection:', err);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [fetchComplianceMetrics]);

  if (isLoading) {
    return (
      <div className="bg-white shadow sm:rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <XCircle className="w-5 h-5 text-red-600 mr-2" />
          <p className="text-sm text-red-800">Failed to load compliance data</p>
        </div>
      </div>
    );
  }

  const getComplianceStatusColor = (score: number) => {
    if (score >= 95) return 'text-green-600';
    if (score >= 90) return 'text-yellow-600';
    if (score >= 85) return 'text-orange-600';
    return 'text-red-600';
  };

  const getComplianceStatusBg = (score: number) => {
    if (score >= 95) return 'bg-green-50 border-green-200';
    if (score >= 90) return 'bg-yellow-50 border-yellow-200';
    if (score >= 85) return 'bg-orange-50 border-orange-200';
    return 'bg-red-50 border-red-200';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const criticalViolations = metrics.violations.filter(v => v.severity === 'critical');
  const highViolations = metrics.violations.filter(v => v.severity === 'high');

  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <ShieldCheck className="w-6 h-6 text-blue-600 mr-2" />
            <div>
              <h2 className="text-lg font-medium text-gray-900">
                TCPA Compliance Status
              </h2>
              {lastUpdated && (
                <p className="text-xs text-gray-500 mt-1">
                  Last updated: {new Date().getTime() - lastUpdated.getTime() < 60000 
                    ? `${Math.floor((new Date().getTime() - lastUpdated.getTime()) / 1000)} seconds ago`
                    : `${Math.floor((new Date().getTime() - lastUpdated.getTime()) / 60000)} minutes ago`}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={fetchComplianceMetrics}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Overall Compliance Score */}
        <div
          className={`border rounded-lg p-4 mb-6 ${getComplianceStatusBg(metrics.compliance_score)}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">
                Overall Compliance Score
              </p>
              <p className={`text-3xl font-bold ${getComplianceStatusColor(metrics.compliance_score)}`}>
                {metrics.compliance_score.toFixed(1)}%
              </p>
            </div>
            <div className="text-right">
              {metrics.compliance_score >= 95 ? (
                <CheckCircle className="w-12 h-12 text-green-600" />
              ) : (
                <AlertTriangle className="w-12 h-12 text-yellow-600" />
              )}
            </div>
          </div>
          <div className="mt-3">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  metrics.compliance_score >= 95
                    ? 'bg-green-600'
                    : metrics.compliance_score >= 90
                    ? 'bg-yellow-600'
                    : 'bg-red-600'
                }`}
                style={{ width: `${metrics.compliance_score}%` }}
              />
            </div>
          </div>
        </div>

        {/* Critical Violations Alert */}
        {criticalViolations.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <XCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800 mb-2">
                  Critical Violations Detected
                </h3>
                <ul className="space-y-1">
                  {criticalViolations.map((violation, index) => (
                    <li key={index} className="text-sm text-red-700">
                      • {violation.message} ({violation.count} occurrences)
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* High Priority Violations */}
        {highViolations.length > 0 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-orange-800 mb-2">
                  High Priority Issues
                </h3>
                <ul className="space-y-1">
                  {highViolations.map((violation, index) => (
                    <li key={index} className="text-sm text-orange-700">
                      • {violation.message} ({violation.count} occurrences)
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">SMS Consent Rate</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {metrics.consent_rate.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {metrics.sms_consented.toLocaleString()} / {metrics.total_subscribers.toLocaleString()} subscribers
            </p>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">Unsubscribe Rate</p>
            <p
              className={`text-2xl font-bold mt-1 ${
                metrics.unsubscribe_rate <= 0.5 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {metrics.unsubscribe_rate.toFixed(2)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Target: &lt; 0.5% per campaign
            </p>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">Delivery Success Rate</p>
            <p
              className={`text-2xl font-bold mt-1 ${
                metrics.delivery_success_rate >= 95 ? 'text-green-600' : 'text-yellow-600'
              }`}
            >
              {metrics.delivery_success_rate.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Target: &gt; 95%
            </p>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">Complaint Rate</p>
            <p
              className={`text-2xl font-bold mt-1 ${
                metrics.complaint_rate <= 0.1 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {metrics.complaint_rate.toFixed(3)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Target: &lt; 0.1%
            </p>
          </div>
        </div>

        {/* Pending Actions */}
        {metrics.pending_unsubscribes > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-blue-600 mr-2" />
              <div>
                <p className="text-sm font-medium text-blue-800">
                  {metrics.pending_unsubscribes} pending unsubscribe request
                  {metrics.pending_unsubscribes > 1 ? 's' : ''}
                </p>
                <p className="text-xs text-blue-700 mt-1">
                  Process within 10 days to maintain compliance
                </p>
              </div>
            </div>
          </div>
        )}

        {/* All Violations List */}
        {metrics.violations.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              All Compliance Issues
            </h3>
            <div className="space-y-2">
              {metrics.violations.map((violation, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mr-2 ${getSeverityColor(
                          violation.severity
                        )}`}
                      >
                        {violation.severity.toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-900">{violation.type}</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{violation.message}</p>
                  </div>
                  <span className="text-sm font-medium text-gray-700">
                    {violation.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Compliance Documentation Link */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            <a
              href="/docs/tcpa-compliance"
              className="text-blue-600 hover:text-blue-700 underline"
            >
              View TCPA Compliance Documentation
            </a>
            {' • '}
            <a
              href="/docs/audit-trail"
              className="text-blue-600 hover:text-blue-700 underline"
            >
              View Audit Trail
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
