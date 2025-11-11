'use client';

import {
  AlertCircle,
  CheckCircle,
  ChevronDown,
  Clock,
  Filter,
  MessageSquare,
  Search,
  User,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { EscalationCard } from '@/components/escalations/EscalationCard';
import { useToast } from '@/components/ui/Toast';
import { useEscalationWebSocket } from '@/hooks/useEscalationWebSocket';

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
  const router = useRouter();
  const toast = useToast();
  
  // WebSocket connection for real-time updates
  const {
    isConnected: wsConnected,
    lastEvent: wsLastEvent,
    stats: wsStats,
  } = useEscalationWebSocket();

  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

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
      setLastUpdated(new Date());
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

  // Handle WebSocket events for real-time updates
  useEffect(() => {
    if (!wsLastEvent) return;

    const { type, data } = wsLastEvent;

    if (type === 'escalation_created' && data) {
      // Show toast notification
      toast.showToast({
        type: 'error',
        title: '🚨 New Escalation',
        message: `${data.priority?.toUpperCase()} priority from ${data.customer_phone}`,
        duration: 5000,
        action: {
          label: 'View',
          onClick: () => router.push(`/escalations/${data.id}`),
        },
      });

      // Refresh escalations list
      fetchEscalations();
    } else if (type === 'escalation_updated' && data) {
      // Show toast for assignment
      if (data.update_type === 'assigned') {
        toast.success('Escalation Assigned', `Escalation ${data.id.slice(0, 8)}... has been assigned`);
      }

      // Refresh escalations list
      fetchEscalations();
    } else if (type === 'escalation_resolved' && data) {
      // Show toast for resolution
      toast.success('Escalation Resolved', `Escalation ${data.id.slice(0, 8)}... has been resolved`);

      // Refresh escalations list
      fetchEscalations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wsLastEvent]);

  // Smart auto-refresh: Only when page is visible and has active escalations
  useEffect(() => {
    if (!autoRefresh) return;

    // Skip if no pending/in-progress escalations (nothing to monitor)
    const hasActiveEscalations = escalations.some(
      e =>
        e.status === 'pending' ||
        e.status === 'assigned' ||
        e.status === 'in_progress'
    );
    if (!hasActiveEscalations && escalations.length > 0) return;

    // Check if page is visible (stop refreshing when tab is inactive)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchEscalations(); // Refresh immediately when tab becomes visible
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Refresh every 60 seconds (reduced from 30s for efficiency)
    const interval = setInterval(() => {
      if (!document.hidden) {
        fetchEscalations();
      }
    }, 60000); // 60 seconds

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRefresh, escalations.length]);

  // Format last updated time
  const getLastUpdatedText = () => {
    const seconds = Math.floor(
      (new Date().getTime() - lastUpdated.getTime()) / 1000
    );
    if (seconds < 10) return 'Just now';
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return lastUpdated.toLocaleTimeString();
  };

  // Stats (use WebSocket stats if available, fallback to local count)
  const stats = {
    total: wsStats.total_active > 0 ? wsStats.total_active : escalations.length,
    pending: wsStats.pending > 0 ? wsStats.pending : escalations.filter(e => e.status === 'pending').length,
    in_progress: wsStats.in_progress > 0 ? wsStats.in_progress : escalations.filter(
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
            {/* WebSocket Connection Indicator */}
            <div className="flex items-center space-x-2">
              {wsConnected ? (
                <div className="flex items-center space-x-1.5 px-2.5 py-1.5 bg-green-50 border border-green-200 rounded-lg">
                  <Wifi size={14} className="text-green-600" />
                  <span className="text-xs font-medium text-green-700">Live</span>
                </div>
              ) : (
                <div className="flex items-center space-x-1.5 px-2.5 py-1.5 bg-gray-50 border border-gray-200 rounded-lg">
                  <WifiOff size={14} className="text-gray-500" />
                  <span className="text-xs font-medium text-gray-600">Offline</span>
                </div>
              )}
            </div>
            <div className="h-6 w-px bg-gray-300"></div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock size={14} />
              <span>Updated: {getLastUpdatedText()}</span>
            </div>
            <div className="h-6 w-px bg-gray-300"></div>
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={e => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
              />
              <span className="text-gray-700">Smart refresh (60s)</span>
            </label>
            <button
              onClick={() => fetchEscalations()}
              disabled={loading}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Refreshing...</span>
                </>
              ) : (
                <span>Refresh Now</span>
              )}
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
          {escalations.map(escalation => (
            <EscalationCard 
              key={escalation.id} 
              escalation={escalation} 
            />
          ))}
        </div>
      )}
    </div>
  );
}
