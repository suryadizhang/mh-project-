'use client';

import {
  AlertCircle,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  Download,
  FileText,
  Filter,
  RefreshCw,
  Search,
  Shield,
  User,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { logger } from '@/lib/logger';
import { tokenManager } from '@/services/api';

interface AuditLog {
  id: string;
  action_type: string;
  action_category: string;
  description: string;
  user_id: string | null;
  user_email: string | null;
  user_role: string | null;
  target_type: string | null;
  target_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  request_method: string | null;
  request_path: string | null;
  status_code: number | null;
  severity: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

interface AuditStats {
  total_events: number;
  security_events: number;
  authentication_events: number;
  data_change_events: number;
  system_events: number;
  events_today: number;
  events_this_week: number;
  unique_users: number;
  failed_actions: number;
  success_rate: number;
}

interface FilterOptions {
  action_categories: string[];
  action_types: string[];
  severities: string[];
  target_types: string[];
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [actionCategory, setActionCategory] = useState<string>('');
  const [actionType, setActionType] = useState<string>('');
  const [severity, setSeverity] = useState<string>('');
  const [userRole, setUserRole] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);

  // 5-Tier RBAC roles for filtering
  const USER_ROLES = [
    { value: 'SUPER_ADMIN', label: 'Super Admin', icon: '👑' },
    { value: 'ADMIN', label: 'Admin', icon: '🔧' },
    { value: 'CUSTOMER_SUPPORT', label: 'Customer Support', icon: '🎧' },
    { value: 'STATION_MANAGER', label: 'Station Manager', icon: '📍' },
    { value: 'CHEF', label: 'Chef', icon: '👨‍🍳' },
  ];

  // Category tabs for quick navigation
  const CATEGORY_TABS = [
    { value: '', label: 'All Events', icon: '📋', color: 'gray' },
    {
      value: 'authentication',
      label: 'Authentication',
      icon: '🔐',
      color: 'blue',
    },
    {
      value: 'data_modification',
      label: 'Data Changes',
      icon: '📝',
      color: 'green',
    },
    { value: 'security', label: 'Security', icon: '🛡️', color: 'red' },
    { value: 'system', label: 'System', icon: '⚙️', color: 'purple' },
  ];

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const totalPages = Math.ceil(totalCount / pageSize);

  useEffect(() => {
    fetchFilterOptions();
    fetchStats();
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [page, actionCategory, actionType, severity, userRole, dateFrom, dateTo]);

  const fetchStats = async () => {
    setStatsLoading(true);
    try {
      const token = tokenManager.getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${API_ENDPOINTS.ADMIN.AUDIT_LOGS_STATS}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setStats(data.data);
      }
    } catch (err) {
      logger.error(err as Error, { context: 'fetch_audit_stats' });
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchFilterOptions = async () => {
    try {
      const token = tokenManager.getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${API_ENDPOINTS.ADMIN.AUDIT_LOGS_ACTIONS}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setFilterOptions(data.data);
      }
    } catch (err) {
      logger.error(err as Error, { context: 'fetch_filter_options' });
    }
  };

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = tokenManager.getToken();
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (searchQuery) params.append('search', searchQuery);
      if (actionCategory) params.append('action_category', actionCategory);
      if (actionType) params.append('action_type', actionType);
      if (severity) params.append('severity', severity);
      if (userRole) params.append('user_role', userRole);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${API_ENDPOINTS.ADMIN.AUDIT_LOGS}?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setLogs(data.data || []);
        setTotalCount(data.total || 0);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch audit logs');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      logger.error(err as Error, { context: 'fetch_audit_logs' });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  const handleRefresh = () => {
    fetchStats();
    fetchLogs();
  };

  const clearFilters = () => {
    setSearchQuery('');
    setActionCategory('');
    setActionType('');
    setSeverity('');
    setUserRole('');
    setDateFrom('');
    setDateTo('');
    setPage(1);
  };

  const exportLogs = async () => {
    try {
      const token = tokenManager.getToken();
      const params = new URLSearchParams({
        page: '1',
        page_size: '1000',
      });

      if (searchQuery) params.append('search', searchQuery);
      if (actionCategory) params.append('action_category', actionCategory);
      if (actionType) params.append('action_type', actionType);
      if (severity) params.append('severity', severity);
      if (userRole) params.append('user_role', userRole);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${API_ENDPOINTS.ADMIN.AUDIT_LOGS}?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        const csv = convertToCSV(data.data || []);
        downloadCSV(
          csv,
          `audit-logs-${new Date().toISOString().split('T')[0]}.csv`
        );
      }
    } catch (err) {
      logger.error(err as Error, { context: 'export_audit_logs' });
    }
  };

  const convertToCSV = (data: AuditLog[]) => {
    const headers = [
      'Timestamp',
      'Action Type',
      'Category',
      'Severity',
      'User Email',
      'User Role',
      'Description',
      'Target Type',
      'Target ID',
      'IP Address',
      'Status Code',
    ];
    const rows = data.map(log => [
      log.created_at,
      log.action_type,
      log.action_category,
      log.severity,
      log.user_email || '',
      log.user_role || '',
      log.description,
      log.target_type || '',
      log.target_id || '',
      log.ip_address || '',
      log.status_code?.toString() || '',
    ]);
    return [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');
  };

  const downloadCSV = (csv: string, filename: string) => {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'authentication':
        return <User className="w-4 h-4" />;
      case 'security':
        return <Shield className="w-4 h-4" />;
      case 'data_change':
        return <FileText className="w-4 h-4" />;
      case 'system':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="w-8 h-8 text-red-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
            <p className="text-gray-600">
              Comprehensive system activity and security audit trail
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportLogs}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Stats Dashboard */}
      {statsLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="h-8 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-2xl font-bold text-gray-900">
                {stats.total_events.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Total Events</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-2xl font-bold text-blue-600">
                {stats.events_today.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Events Today</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-2xl font-bold text-orange-600">
                {stats.security_events.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Security Events</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-2xl font-bold text-red-600">
                {stats.failed_actions.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Failed Actions</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-2xl font-bold text-green-600">
                {stats.success_rate.toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Success Rate</p>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Category Sub-Navigation Tabs */}
      <div className="flex flex-wrap gap-2 bg-white rounded-lg p-2 shadow-sm border">
        {CATEGORY_TABS.map(tab => (
          <button
            key={tab.value}
            onClick={() => {
              setActionCategory(tab.value);
              setPage(1);
            }}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
              flex items-center gap-2
              ${
                actionCategory === tab.value
                  ? tab.color === 'blue'
                    ? 'bg-blue-100 text-blue-800 ring-2 ring-blue-500'
                    : tab.color === 'green'
                      ? 'bg-green-100 text-green-800 ring-2 ring-green-500'
                      : tab.color === 'red'
                        ? 'bg-red-100 text-red-800 ring-2 ring-red-500'
                        : tab.color === 'purple'
                          ? 'bg-purple-100 text-purple-800 ring-2 ring-purple-500'
                          : 'bg-gray-100 text-gray-800 ring-2 ring-gray-500'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }
            `}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {actionCategory === tab.value && (
              <span className="ml-1 text-xs opacity-75">●</span>
            )}
          </button>
        ))}
      </div>

      {/* Filters Card */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Filters
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="mb-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search by description, email, action type..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
              <Button type="submit">Search</Button>
              <Button type="button" variant="outline" onClick={clearFilters}>
                Clear
              </Button>
            </div>
          </form>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 pt-4 border-t">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={actionCategory}
                  onChange={e => {
                    setActionCategory(e.target.value);
                    setPage(1);
                  }}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-red-500"
                >
                  <option value="">All Categories</option>
                  {filterOptions?.action_categories.map(cat => (
                    <option key={cat} value={cat}>
                      {cat
                        .replace(/_/g, ' ')
                        .replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Action Type
                </label>
                <select
                  value={actionType}
                  onChange={e => {
                    setActionType(e.target.value);
                    setPage(1);
                  }}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-red-500"
                >
                  <option value="">All Types</option>
                  {filterOptions?.action_types.map(type => (
                    <option key={type} value={type}>
                      {type
                        .replace(/_/g, ' ')
                        .replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Severity
                </label>
                <select
                  value={severity}
                  onChange={e => {
                    setSeverity(e.target.value);
                    setPage(1);
                  }}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-red-500"
                >
                  <option value="">All Severities</option>
                  {filterOptions?.severities.map(sev => (
                    <option key={sev} value={sev}>
                      {sev.charAt(0).toUpperCase() + sev.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User Role
                </label>
                <select
                  value={userRole}
                  onChange={e => {
                    setUserRole(e.target.value);
                    setPage(1);
                  }}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-red-500"
                >
                  <option value="">All Roles</option>
                  {USER_ROLES.map(role => (
                    <option key={role.value} value={role.value}>
                      {role.icon} {role.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Calendar className="inline w-4 h-4 mr-1" />
                  From Date
                </label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={e => {
                    setDateFrom(e.target.value);
                    setPage(1);
                  }}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-red-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Calendar className="inline w-4 h-4 mr-1" />
                  To Date
                </label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={e => {
                    setDateTo(e.target.value);
                    setPage(1);
                  }}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-red-500"
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800">
                Error Loading Audit Logs
              </h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Audit Logs Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              Audit Log Entries
              {totalCount > 0 && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({totalCount.toLocaleString()} total)
                </span>
              )}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="animate-pulse flex space-x-4 p-4 border rounded-lg"
                >
                  <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                No audit logs found
              </h3>
              <p className="text-gray-500 mb-4">
                {searchQuery ||
                actionCategory ||
                actionType ||
                severity ||
                userRole ||
                dateFrom ||
                dateTo
                  ? 'Try adjusting your filters or search query'
                  : 'Audit logs will appear here as users perform actions in the system'}
              </p>
              {(searchQuery ||
                actionCategory ||
                actionType ||
                severity ||
                userRole ||
                dateFrom ||
                dateTo) && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSearchQuery('');
                    setActionCategory('');
                    setActionType('');
                    setSeverity('');
                    setUserRole('');
                    setDateFrom('');
                    setDateTo('');
                  }}
                >
                  Clear All Filters
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Timestamp
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Category / Action
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      User
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Description
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Severity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Details
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {logs.map(log => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 mr-2 text-gray-400" />
                          {formatDate(log.created_at)}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getCategoryIcon(log.action_category)}
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {log.action_category
                                .replace(/_/g, ' ')
                                .replace(/\b\w/g, l => l.toUpperCase())}
                            </div>
                            <div className="text-xs text-gray-500">
                              {log.action_type.replace(/_/g, ' ')}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {log.user_email || 'System'}
                          </div>
                          {log.user_role && (
                            <div className="text-xs text-gray-500">
                              {log.user_role}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div
                          className="text-sm text-gray-900 max-w-xs truncate"
                          title={log.description}
                        >
                          {log.description}
                        </div>
                        {log.target_type && (
                          <div className="text-xs text-gray-500">
                            Target: {log.target_type}{' '}
                            {log.target_id &&
                              `(${log.target_id.substring(0, 8)}...)`}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Badge className={getSeverityColor(log.severity)}>
                          {log.severity}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-500">
                        {log.ip_address && <div>IP: {log.ip_address}</div>}
                        {log.status_code && (
                          <div>
                            Status:{' '}
                            <span
                              className={
                                log.status_code >= 400
                                  ? 'text-red-600'
                                  : 'text-green-600'
                              }
                            >
                              {log.status_code}
                            </span>
                          </div>
                        )}
                        {log.request_method && (
                          <div>
                            {log.request_method} {log.request_path}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <div className="text-sm text-gray-600">
                Showing {(page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, totalCount)} of{' '}
                {totalCount.toLocaleString()} entries
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </Button>
                <div className="flex items-center gap-1">
                  {[...Array(Math.min(5, totalPages))].map((_, i) => {
                    let pageNum: number;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (page <= 3) {
                      pageNum = i + 1;
                    } else if (page >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }
                    return (
                      <Button
                        key={pageNum}
                        variant={page === pageNum ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setPage(pageNum)}
                        className="w-10"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
