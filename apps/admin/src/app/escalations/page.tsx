'use client';

import {
  AlertCircle,
  CheckCircle,
  ChevronDown,
  Clock,
  Filter,
  Mail,
  MessageSquare,
  Phone,
  Search,
  User,
  XCircle,
} from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

interface Escalation {
  id: string;
  conversation_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  reason: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  method: 'phone' | 'email' | 'preferred_method';
  status:
    | 'pending'
    | 'assigned'
    | 'in_progress'
    | 'waiting_customer'
    | 'resolved'
    | 'closed'
    | 'error';
  assigned_to_id?: string;
  assigned_to?: {
    id: string;
    full_name: string;
    email: string;
  };
  sms_sent: boolean;
  call_initiated: boolean;
  created_at: string;
  updated_at: string;
  escalated_at?: string;
}

interface EscalationListResponse {
  escalations: Escalation[];
  total: number;
  page: number;
  per_page: number;
}

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch escalations
  const fetchEscalations = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.append('status', statusFilter);
      if (priorityFilter !== 'all') params.append('priority', priorityFilter);
      if (searchQuery) params.append('search', searchQuery);

      const response = await fetch(`/api/v1/escalations?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch escalations');

      const data: EscalationListResponse = await response.json();
      setEscalations(data.escalations);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load escalations'
      );
    } finally {
      setLoading(false);
    }
  };

  // Initial load and filter changes
  useEffect(() => {
    fetchEscalations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, priorityFilter, searchQuery]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchEscalations();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRefresh]);

  // Priority badge styling
  const getPriorityStyle = (priority: Escalation['priority']) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  // Status badge styling
  const getStatusStyle = (status: Escalation['status']) => {
    switch (status) {
      case 'pending':
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
          icon: Clock,
        };
      case 'assigned':
        return {
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          border: 'border-blue-200',
          icon: User,
        };
      case 'in_progress':
        return {
          bg: 'bg-purple-100',
          text: 'text-purple-800',
          border: 'border-purple-200',
          icon: MessageSquare,
        };
      case 'waiting_customer':
        return {
          bg: 'bg-yellow-100',
          text: 'text-yellow-800',
          border: 'border-yellow-200',
          icon: Clock,
        };
      case 'resolved':
        return {
          bg: 'bg-green-100',
          text: 'text-green-800',
          border: 'border-green-200',
          icon: CheckCircle,
        };
      case 'closed':
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-600',
          border: 'border-gray-200',
          icon: XCircle,
        };
      case 'error':
        return {
          bg: 'bg-red-100',
          text: 'text-red-800',
          border: 'border-red-200',
          icon: AlertCircle,
        };
    }
  };

  // Format time ago
  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  // Get contact method icon
  const getMethodIcon = (method: Escalation['method']) => {
    switch (method) {
      case 'phone':
        return <Phone size={16} />;
      case 'email':
        return <Mail size={16} />;
      case 'preferred_method':
        return <MessageSquare size={16} />;
    }
  };

  // Stats
  const stats = {
    total: escalations.length,
    pending: escalations.filter(e => e.status === 'pending').length,
    in_progress: escalations.filter(
      e => e.status === 'in_progress' || e.status === 'assigned'
    ).length,
    resolved: escalations.filter(e => e.status === 'resolved').length,
  };

  if (loading && escalations.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading escalations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              🆘 Escalations Inbox
            </h1>
            <p className="text-gray-600 mt-1">
              Manage customer support escalations
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={e => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
              />
              <span className="text-gray-700">Auto-refresh (30s)</span>
            </label>
            <button
              onClick={() => fetchEscalations()}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              Refresh Now
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.total}
                </p>
              </div>
              <div className="bg-gray-100 p-3 rounded-full">
                <MessageSquare className="text-gray-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {stats.pending}
                </p>
              </div>
              <div className="bg-yellow-100 p-3 rounded-full">
                <Clock className="text-yellow-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.in_progress}
                </p>
              </div>
              <div className="bg-blue-100 p-3 rounded-full">
                <User className="text-blue-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Resolved</p>
                <p className="text-2xl font-bold text-green-600">
                  {stats.resolved}
                </p>
              </div>
              <div className="bg-green-100 p-3 rounded-full">
                <CheckCircle className="text-green-600" size={24} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              size={20}
            />
            <input
              type="text"
              placeholder="Search by customer name, phone, or reason..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Filter size={20} />
            <span>Filters</span>
            <ChevronDown
              size={16}
              className={`transition-transform ${showFilters ? 'rotate-180' : ''}`}
            />
          </button>
        </div>

        {/* Filter Options */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200 flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              >
                <option value="all">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="assigned">Assigned</option>
                <option value="in_progress">In Progress</option>
                <option value="waiting_customer">Waiting Customer</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
                <option value="error">Error</option>
              </select>
            </div>

            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={priorityFilter}
                onChange={e => setPriorityFilter(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              >
                <option value="all">All Priorities</option>
                <option value="urgent">Urgent</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div className="flex-1"></div>
          </div>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start space-x-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-medium text-red-900">
              Error Loading Escalations
            </h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Escalations List */}
      {escalations.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No escalations found
          </h3>
          <p className="text-gray-600">
            {searchQuery || statusFilter !== 'all' || priorityFilter !== 'all'
              ? 'Try adjusting your filters'
              : 'Great news! There are no pending escalations at the moment.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {escalations.map(escalation => {
            const statusStyle = getStatusStyle(escalation.status);
            const StatusIcon = statusStyle.icon;

            return (
              <Link
                key={escalation.id}
                href={`/escalations/${escalation.id}`}
                className="block bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md hover:border-orange-300 transition-all"
              >
                <div className="flex items-start justify-between">
                  {/* Left Side - Customer Info */}
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {escalation.customer_name}
                      </h3>

                      {/* Priority Badge */}
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full border ${getPriorityStyle(escalation.priority)}`}
                      >
                        {escalation.priority.toUpperCase()}
                      </span>

                      {/* Status Badge */}
                      <span
                        className={`flex items-center space-x-1 px-2 py-1 text-xs font-medium rounded-full border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}
                      >
                        <StatusIcon size={12} />
                        <span>{escalation.status.replace('_', ' ')}</span>
                      </span>

                      {/* Method Icon */}
                      <span
                        className="text-gray-500"
                        title={`Preferred: ${escalation.method}`}
                      >
                        {getMethodIcon(escalation.method)}
                      </span>
                    </div>

                    <p className="text-gray-700 mb-3 line-clamp-2">
                      {escalation.reason}
                    </p>

                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <div className="flex items-center space-x-1">
                        <Phone size={14} />
                        <span>{escalation.customer_phone}</span>
                      </div>
                      {escalation.customer_email && (
                        <div className="flex items-center space-x-1">
                          <Mail size={14} />
                          <span>{escalation.customer_email}</span>
                        </div>
                      )}
                      {escalation.assigned_to && (
                        <div className="flex items-center space-x-1">
                          <User size={14} />
                          <span>
                            Assigned to: {escalation.assigned_to.full_name}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right Side - Time & Actions */}
                  <div className="flex flex-col items-end space-y-2 ml-4">
                    <span className="text-sm text-gray-500">
                      {getTimeAgo(escalation.created_at)}
                    </span>

                    <div className="flex items-center space-x-2">
                      {escalation.sms_sent && (
                        <span className="flex items-center space-x-1 px-2 py-1 bg-green-50 text-green-700 rounded-full text-xs">
                          <MessageSquare size={12} />
                          <span>SMS Sent</span>
                        </span>
                      )}
                      {escalation.call_initiated && (
                        <span className="flex items-center space-x-1 px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">
                          <Phone size={12} />
                          <span>Called</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
