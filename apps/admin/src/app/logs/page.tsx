'use client';

/**
 * System Logs Page - Real-time error and activity logging
 *
 * Connects to backend API:
 * - GET /api/admin/error-logs/ - List error logs with filtering
 * - GET /api/admin/error-logs/{id} - Get log details
 * - POST /api/admin/error-logs/{id}/resolve - Mark as resolved
 * - GET /api/admin/error-logs/statistics/overview - Get stats
 * - GET /api/admin/error-logs/export/csv - Export logs
 */

import { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle,
  Download,
  Filter,
  Info,
  RefreshCw,
  Search,
  XCircle,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';

// ============================================================================
// Types
// ============================================================================

interface ErrorLog {
  id: number;
  level: 'ERROR' | 'WARNING' | 'INFO' | 'DEBUG';
  message: string;
  path: string;
  error_type: string;
  user_id: string | null;
  request_id: string | null;
  resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
  timestamp: string;
}

interface LogStatistics {
  total: number;
  by_level: {
    ERROR: number;
    WARNING: number;
    INFO: number;
    DEBUG: number;
  };
  unresolved: number;
  last_24h: number;
}

// ============================================================================
// Main Component
// ============================================================================

export default function LogsPage() {
  const { token } = useAuth();
  const [logs, setLogs] = useState<ErrorLog[]>([]);
  const [stats, setStats] = useState<LogStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [levelFilter, setLevelFilter] = useState<string>('');
  const [resolvedFilter, setResolvedFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 50;

  // Fetch logs from API
  const fetchLogs = useCallback(async () => {
    if (!token) return;

    try {
      setRefreshing(true);

      const params = new URLSearchParams();
      params.append('page', currentPage.toString());
      params.append('limit', logsPerPage.toString());
      if (levelFilter) params.append('level', levelFilter);
      if (resolvedFilter !== '') params.append('resolved', resolvedFilter);
      if (searchQuery) params.append('path', searchQuery);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/admin/error-logs/?${params}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.statusText}`);
      }

      const data = await response.json();
      setLogs(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching logs:', err);
      setError(err instanceof Error ? err.message : 'Failed to load logs');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token, currentPage, levelFilter, resolvedFilter, searchQuery]);

  // Fetch statistics
  const fetchStats = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/admin/error-logs/statistics/overview`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, [token]);

  // Mark log as resolved
  const resolveLog = async (logId: number) => {
    if (!token) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/admin/error-logs/${logId}/resolve`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        // Update local state
        setLogs(prev =>
          prev.map(log =>
            log.id === logId
              ? {
                  ...log,
                  resolved: true,
                  resolved_at: new Date().toISOString(),
                }
              : log
          )
        );
        fetchStats(); // Refresh stats
      }
    } catch (err) {
      console.error('Error resolving log:', err);
    }
  };

  // Export logs as CSV
  const exportLogs = async () => {
    if (!token) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/admin/error-logs/export/csv`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `error-logs-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Error exporting logs:', err);
    }
  };

  // Initial load
  useEffect(() => {
    fetchLogs();
    fetchStats();
  }, [fetchLogs, fetchStats]);

  // Get icon for log level
  const getLogIcon = (level: string) => {
    switch (level) {
      case 'ERROR':
        return <XCircle className="w-5 h-5 text-red-500" aria-hidden="true" />;
      case 'WARNING':
        return (
          <AlertCircle className="w-5 h-5 text-yellow-500" aria-hidden="true" />
        );
      case 'INFO':
        return <Info className="w-5 h-5 text-blue-500" aria-hidden="true" />;
      case 'DEBUG':
        return (
          <CheckCircle className="w-5 h-5 text-gray-500" aria-hidden="true" />
        );
      default:
        return <Info className="w-5 h-5 text-blue-500" aria-hidden="true" />;
    }
  };

  // Get color for log level
  const getLogColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'border-l-red-500 bg-red-50';
      case 'WARNING':
        return 'border-l-yellow-500 bg-yellow-50';
      case 'INFO':
        return 'border-l-blue-500 bg-blue-50';
      case 'DEBUG':
        return 'border-l-gray-500 bg-gray-50';
      default:
        return 'border-l-blue-500 bg-blue-50';
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" aria-label="Loading logs...">
        <div className="h-10 bg-gray-200 rounded w-1/3"></div>
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-24 bg-gray-200 rounded"></div>
          ))}
        </div>
        <div className="h-96 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <main className="space-y-6" role="main" aria-label="System Logs">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Logs</h1>
          <p className="text-gray-600">Monitor system errors and activities</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchLogs();
              fetchStats();
            }}
            disabled={refreshing}
            aria-label="Refresh logs"
          >
            <RefreshCw
              className={`h-4 w-4 mr-1 ${refreshing ? 'animate-spin' : ''}`}
              aria-hidden="true"
            />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportLogs}
            aria-label="Export logs as CSV"
          >
            <Download className="h-4 w-4 mr-1" aria-hidden="true" />
            Export
          </Button>
        </div>
      </header>

      {/* Statistics Cards */}
      {stats && (
        <div
          className="grid grid-cols-1 md:grid-cols-4 gap-4"
          role="region"
          aria-label="Log statistics"
        >
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Logs</p>
                  <p className="text-2xl font-bold">{stats.total}</p>
                </div>
                <Info className="h-8 w-8 text-blue-500" aria-hidden="true" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Errors</p>
                  <p className="text-2xl font-bold text-red-600">
                    {stats.by_level.ERROR}
                  </p>
                </div>
                <XCircle className="h-8 w-8 text-red-500" aria-hidden="true" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Unresolved</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {stats.unresolved}
                  </p>
                </div>
                <AlertCircle
                  className="h-8 w-8 text-yellow-500"
                  aria-hidden="true"
                />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Last 24h</p>
                  <p className="text-2xl font-bold">{stats.last_24h}</p>
                </div>
                <CheckCircle
                  className="h-8 w-8 text-green-500"
                  aria-hidden="true"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="py-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" aria-hidden="true" />
              <select
                className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={levelFilter}
                onChange={e => setLevelFilter(e.target.value)}
                aria-label="Filter by log level"
              >
                <option value="">All Levels</option>
                <option value="ERROR">Error</option>
                <option value="WARNING">Warning</option>
                <option value="INFO">Info</option>
                <option value="DEBUG">Debug</option>
              </select>
            </div>
            <select
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={resolvedFilter}
              onChange={e => setResolvedFilter(e.target.value)}
              aria-label="Filter by resolved status"
            >
              <option value="">All Status</option>
              <option value="false">Unresolved</option>
              <option value="true">Resolved</option>
            </select>
            <div className="relative flex-1">
              <Search
                className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500"
                aria-hidden="true"
              />
              <input
                type="text"
                placeholder="Search by path..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                aria-label="Search logs"
              />
            </div>
            <Button variant="default" onClick={fetchLogs}>
              Apply Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <div
          className="bg-red-50 border border-red-200 rounded-lg p-4"
          role="alert"
        >
          <div className="flex items-center">
            <XCircle className="h-5 w-5 text-red-500 mr-2" aria-hidden="true" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Logs List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Logs ({logs.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Info
                className="h-12 w-12 mx-auto mb-4 text-gray-400"
                aria-hidden="true"
              />
              <p>No logs found matching your criteria</p>
            </div>
          ) : (
            <div
              className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto"
              role="log"
            >
              {logs.map(log => (
                <div
                  key={log.id}
                  className={`p-4 border-l-4 ${getLogColor(log.level)} ${log.resolved ? 'opacity-60' : ''}`}
                >
                  <div className="flex items-start gap-3">
                    {getLogIcon(log.level)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant={
                            log.level === 'ERROR' ? 'destructive' : 'secondary'
                          }
                        >
                          {log.level}
                        </Badge>
                        {log.resolved && (
                          <Badge variant="outline" className="text-green-600">
                            Resolved
                          </Badge>
                        )}
                        <span className="text-xs text-gray-500">
                          {log.error_type}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-gray-900 break-words">
                        {log.message}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-gray-500">
                        <span>{new Date(log.timestamp).toLocaleString()}</span>
                        <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">
                          {log.path}
                        </span>
                        {log.user_id && <span>User: {log.user_id}</span>}
                        {log.request_id && (
                          <span>Request: {log.request_id.slice(0, 8)}...</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {!log.resolved && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => resolveLog(log.id)}
                          aria-label="Mark as resolved"
                        >
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            aria-hidden="true"
                          />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {logs.length >= logsPerPage && (
        <nav className="flex justify-center gap-2" aria-label="Pagination">
          <Button
            variant="outline"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </Button>
          <span className="px-4 py-2 text-gray-600">Page {currentPage}</span>
          <Button
            variant="outline"
            onClick={() => setCurrentPage(p => p + 1)}
            disabled={logs.length < logsPerPage}
          >
            Next
          </Button>
        </nav>
      )}
    </main>
  );
}
