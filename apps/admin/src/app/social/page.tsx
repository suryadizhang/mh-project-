'use client';

import { useState, useCallback, useMemo } from 'react';
import {
  MessageSquare,
  Send,
  Facebook,
  Instagram,
  Target,
  Clock,
  CheckCircle,
  Circle,
  Sparkles,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { StatsCard } from '@/components/ui/stats-card';
import { FilterBar } from '@/components/ui/filter-bar';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Modal } from '@/components/ui/modal';
import {
  useSocialThreads,
  usePagination,
  useFilters,
  useSearch,
} from '@/hooks/useApi';

const PLATFORMS = {
  FACEBOOK: 'facebook',
  INSTAGRAM: 'instagram',
} as const;

const PLATFORM_COLORS = {
  [PLATFORMS.FACEBOOK]: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    icon: Facebook,
    label: 'Facebook',
  },
  [PLATFORMS.INSTAGRAM]: {
    bg: 'bg-pink-50',
    text: 'text-pink-600',
    icon: Instagram,
    label: 'Instagram',
  },
};

const QUICK_REPLIES = [
  {
    label: '👋 Greeting',
    text: 'Hi! Thank you for reaching out to MyHibachi. How can we help you today?',
  },
  {
    label: '📅 Booking Info',
    text: 'We offer hibachi catering for events of all sizes! You can book directly on our website or give us a call to discuss your needs.',
  },
  {
    label: '💰 Pricing',
    text: 'Our pricing varies based on guest count, location, and menu selection. I can provide a detailed quote if you share your event details!',
  },
  {
    label: '📍 Service Areas',
    text: 'We currently serve the Sacramento area and surrounding regions. Please let us know your location for availability.',
  },
  {
    label: '✅ Yes',
    text: 'Yes, absolutely! Let me help you with that.',
  },
];

export default function SocialInboxPage() {
  // State
  const [selectedThread, setSelectedThread] = useState<any>(null);
  const [messageText, setMessageText] = useState('');
  const [showQuickReplies, setShowQuickReplies] = useState(false);

  // Pagination and filters
  const { page, limit } = usePagination(1, 50);
  const { query: searchQuery, debouncedQuery, setQuery: setSearchQuery } = useSearch();
  const { filters, updateFilter, resetFilters } = useFilters({
    platform: '',
    status: '',
  });

  // Combine all filters for API call
  const apiFilters = useMemo(
    () => ({
      ...filters,
      search: debouncedQuery,
      page,
      limit,
      sort_by: 'updated_at',
      sort_order: 'desc' as const,
    }),
    [filters, debouncedQuery, page, limit]
  );

  // Fetch threads data
  const { data: threadsResponse, loading, error, refetch } = useSocialThreads(apiFilters);

  const threads = threadsResponse?.data || [];
  const totalCount = threadsResponse?.total_count || 0;

  // Calculate stats
  const stats = useMemo(() => {
    const unreadCount = threads.filter((t: any) => !t.is_read).length;
    const fbCount = threads.filter((t: any) => t.platform === PLATFORMS.FACEBOOK).length;
    const igCount = threads.filter((t: any) => t.platform === PLATFORMS.INSTAGRAM).length;

    // Average response time (in hours)
    const avgResponseTime = threads.length > 0
      ? threads.reduce((sum: number, t: any) => {
          if (t.first_response_time) {
            const hours = new Date(t.first_response_time).getTime() - new Date(t.created_at).getTime();
            return sum + (hours / (1000 * 60 * 60));
          }
          return sum;
        }, 0) / threads.length
      : 0;

    return {
      total: totalCount,
      unread: unreadCount,
      facebook: fbCount,
      instagram: igCount,
      avgResponseTime: avgResponseTime.toFixed(1),
    };
  }, [threads, totalCount]);

  // Handlers
  const handleThreadClick = (thread: any) => {
    setSelectedThread(thread);
    // TODO: Mark as read
  };

  const handleSendMessage = () => {
    if (!messageText.trim() || !selectedThread) return;

    // TODO: Call send message API
    console.log('Sending message:', messageText, 'to thread:', selectedThread.thread_id);
    setMessageText('');
    setShowQuickReplies(false);
  };

  const handleQuickReply = (text: string) => {
    setMessageText(text);
    setShowQuickReplies(false);
  };

  const handleConvertToLead = (thread: any) => {
    // TODO: Call convert to lead API
    console.log('Converting thread to lead:', thread.thread_id);
  };

  const handleClearFilters = () => {
    resetFilters();
    setSearchQuery('');
  };

  // Format date/time
  const formatTime = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffHours < 1) {
      const diffMins = Math.floor(diffMs / (1000 * 60));
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    }
  };

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <EmptyState
          icon={MessageSquare}
          title="Error Loading Social Inbox"
          description={error}
          actionLabel="Try Again"
          onAction={refetch}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Social Media Inbox</h1>
          <p className="text-gray-600">Manage Facebook and Instagram messages</p>
        </div>
        <Button onClick={refetch}>
          <MessageSquare className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          title="Total Threads"
          value={stats.total}
          icon={MessageSquare}
          color="blue"
        />
        <StatsCard
          title="Unread"
          value={stats.unread}
          subtitle="needs response"
          icon={Circle}
          color="red"
        />
        <StatsCard
          title="Facebook"
          value={stats.facebook}
          icon={Facebook}
          color="blue"
        />
        <StatsCard
          title="Instagram"
          value={stats.instagram}
          icon={Instagram}
          color="purple"
        />
      </div>

      {/* Filters */}
      <FilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search messages..."
        filters={[
          {
            key: 'platform',
            label: 'All Platforms',
            options: [
              { label: 'Facebook', value: PLATFORMS.FACEBOOK },
              { label: 'Instagram', value: PLATFORMS.INSTAGRAM },
            ],
            value: filters.platform,
          },
          {
            key: 'status',
            label: 'All Status',
            options: [
              { label: 'Unread', value: 'unread' },
              { label: 'Read', value: 'read' },
            ],
            value: filters.status,
          },
        ]}
        onFilterChange={(key, value) => updateFilter(key as 'platform' | 'status', value)}
        onClearFilters={handleClearFilters}
        showClearButton
      />

      {/* Loading State */}
      {loading && <LoadingSpinner message="Loading messages..." />}

      {/* Empty State */}
      {!loading && threads.length === 0 && (
        <EmptyState
          icon={MessageSquare}
          title="No messages found"
          description={
            Object.values(filters).some(Boolean) || debouncedQuery
              ? 'Try adjusting your filters or search query'
              : 'Social media messages will appear here once customers reach out'
          }
        />
      )}

      {/* Inbox Layout */}
      {!loading && threads.length > 0 && (
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="flex h-[600px]">
            {/* Thread List Sidebar */}
            <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="font-semibold text-gray-900">Messages ({threads.length})</h3>
              </div>

              <div className="divide-y divide-gray-200">
                {threads.map((thread: any) => {
                  const platform = PLATFORM_COLORS[thread.platform as keyof typeof PLATFORM_COLORS] || PLATFORM_COLORS[PLATFORMS.FACEBOOK];
                  const PlatformIcon = platform.icon;

                  return (
                    <div
                      key={thread.thread_id}
                      onClick={() => handleThreadClick(thread)}
                      className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedThread?.thread_id === thread.thread_id
                          ? 'bg-blue-50 border-l-4 border-blue-600'
                          : !thread.is_read
                          ? 'bg-blue-50 bg-opacity-30'
                          : ''
                      }`}
                    >
                      {/* Thread Header */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`p-1 rounded ${platform.bg}`}>
                            <PlatformIcon className={`w-4 h-4 ${platform.text}`} />
                          </div>
                          <span className="font-medium text-gray-900">
                            {thread.customer_name || 'Unknown User'}
                          </span>
                        </div>
                        {!thread.is_read && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full" />
                        )}
                      </div>

                      {/* Last Message Preview */}
                      <p className="text-sm text-gray-600 mb-1 line-clamp-2">
                        {thread.last_message || 'No messages yet'}
                      </p>

                      {/* Time and Platform */}
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {formatTime(thread.updated_at)}
                        </span>
                        <span className={platform.text}>{platform.label}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Conversation View */}
            <div className="flex-1 flex flex-col">
              {selectedThread ? (
                <>
                  {/* Conversation Header */}
                  <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {(selectedThread.customer_name || 'U')[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {selectedThread.customer_name || 'Unknown User'}
                          </h3>
                          <p className="text-xs text-gray-500">
                            {PLATFORM_COLORS[selectedThread.platform as keyof typeof PLATFORM_COLORS]?.label || 'Unknown'}
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleConvertToLead(selectedThread)}
                      >
                        <Target className="w-4 h-4 mr-1" />
                        Convert to Lead
                      </Button>
                    </div>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
                    <div className="space-y-4">
                      {selectedThread.messages?.map((message: any, index: number) => {
                        const isFromCustomer = message.direction === 'inbound';

                        return (
                          <div
                            key={index}
                            className={`flex ${isFromCustomer ? 'justify-start' : 'justify-end'}`}
                          >
                            <div
                              className={`max-w-[70%] p-3 rounded-lg ${
                                isFromCustomer
                                  ? 'bg-white text-gray-900'
                                  : 'bg-blue-600 text-white'
                              }`}
                            >
                              <p className="text-sm">{message.text}</p>
                              <p
                                className={`text-xs mt-1 ${
                                  isFromCustomer ? 'text-gray-500' : 'text-blue-100'
                                }`}
                              >
                                {formatTime(message.timestamp)}
                              </p>
                            </div>
                          </div>
                        );
                      })}

                      {/* Placeholder if no messages */}
                      {(!selectedThread.messages || selectedThread.messages.length === 0) && (
                        <div className="text-center text-gray-500 py-8">
                          <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                          <p>No messages in this thread yet</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Message Input */}
                  <div className="p-4 border-t border-gray-200 bg-white">
                    {/* Quick Replies */}
                    {showQuickReplies && (
                      <div className="mb-3 flex flex-wrap gap-2">
                        {QUICK_REPLIES.map((reply) => (
                          <button
                            key={reply.label}
                            onClick={() => handleQuickReply(reply.text)}
                            className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
                          >
                            {reply.label}
                          </button>
                        ))}
                      </div>
                    )}

                    <div className="flex gap-2">
                      <button
                        onClick={() => setShowQuickReplies(!showQuickReplies)}
                        className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                        title="Quick Replies"
                      >
                        <Sparkles className="w-5 h-5" />
                      </button>
                      <textarea
                        value={messageText}
                        onChange={(e) => setMessageText(e.target.value)}
                        placeholder="Type your message..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        rows={2}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                      />
                      <Button onClick={handleSendMessage} disabled={!messageText.trim()}>
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <p className="text-lg">Select a conversation to view messages</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
