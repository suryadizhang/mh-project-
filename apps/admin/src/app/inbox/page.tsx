'use client';

import { useState, useCallback, useMemo } from 'react';
import {
  MessageSquare,
  Send,
  Facebook,
  Instagram,
  MessageCircle,
  Mail,
  Target,
  Clock,
  CheckCircle,
  Circle,
  Sparkles,
  Phone,
  UserPlus,
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
import { smsService } from '@/services/api';

// Channel types
const CHANNELS = {
  ALL: 'all',
  FACEBOOK: 'facebook',
  INSTAGRAM: 'instagram',
  SMS: 'sms',
  EMAIL: 'email', // Future
} as const;

type ChannelType = typeof CHANNELS[keyof typeof CHANNELS];

// Channel configuration with colors, icons, and labels
const CHANNEL_CONFIG = {
  [CHANNELS.FACEBOOK]: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    icon: Facebook,
    label: 'Facebook',
    borderColor: 'border-blue-600',
  },
  [CHANNELS.INSTAGRAM]: {
    bg: 'bg-pink-50',
    text: 'text-pink-600',
    icon: Instagram,
    label: 'Instagram',
    borderColor: 'border-pink-600',
  },
  [CHANNELS.SMS]: {
    bg: 'bg-green-50',
    text: 'text-green-600',
    icon: MessageCircle,
    label: 'SMS',
    borderColor: 'border-green-600',
  },
  [CHANNELS.EMAIL]: {
    bg: 'bg-purple-50',
    text: 'text-purple-600',
    icon: Mail,
    label: 'Email',
    borderColor: 'border-purple-600',
  },
};

// Quick reply templates (channel-aware)
const QUICK_REPLIES = {
  general: [
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
  ],
  sms: [
    {
      label: '👋 Hi',
      text: 'Hi! Thanks for contacting MyHibachi. How can we help?',
    },
    {
      label: '📅 Book',
      text: 'To book: visit myhibachi.com or call us. What date were you thinking?',
    },
    {
      label: '💰 Price',
      text: 'Pricing depends on guest count and menu. Share your details for a quote!',
    },
    {
      label: '📍 Location',
      text: 'We serve Sacramento area. Where is your event?',
    },
  ],
};

export default function UnifiedInboxPage() {
  // State
  const [activeChannel, setActiveChannel] = useState<ChannelType>(CHANNELS.ALL);
  const [selectedThread, setSelectedThread] = useState<any>(null);
  const [messageText, setMessageText] = useState('');
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const [smsThreads, setSmsThreads] = useState<any[]>([]);
  const [loadingSms, setLoadingSms] = useState(false);

  // Pagination and filters
  const { page, limit } = usePagination(1, 50);
  const { query: searchQuery, debouncedQuery, setQuery: setSearchQuery } = useSearch();
  const { filters, updateFilter, resetFilters } = useFilters({
    status: '',
  });

  // Combine all filters for API call (social threads)
  const apiFilters = useMemo(
    () => ({
      ...filters,
      platform: activeChannel !== CHANNELS.ALL && activeChannel !== CHANNELS.SMS ? activeChannel : undefined,
      search: debouncedQuery,
      page,
      limit,
      sort_by: 'updated_at',
      sort_order: 'desc' as const,
    }),
    [activeChannel, filters, debouncedQuery, page, limit]
  );

  // Fetch social media threads (FB/IG)
  const { data: socialResponse, loading: loadingSocial, error, refetch: refetchSocial } = useSocialThreads(
    activeChannel !== CHANNELS.SMS ? apiFilters : null
  );

  const socialThreads = socialResponse?.data || [];

  // Load SMS threads when channel is active
  const loadSmsThreads = useCallback(async () => {
    if (activeChannel !== CHANNELS.SMS && activeChannel !== CHANNELS.ALL) return;

    setLoadingSms(true);
    try {
      const response = await smsService.getMessages();
      setSmsThreads(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Failed to load SMS threads:', err);
    } finally {
      setLoadingSms(false);
    }
  }, [activeChannel]);

  // Load SMS on mount and when channel changes
  useMemo(() => {
    if (activeChannel === CHANNELS.SMS || activeChannel === CHANNELS.ALL) {
      loadSmsThreads();
    }
  }, [activeChannel, loadSmsThreads]);

  // Combine and filter all threads based on active channel
  const allThreads = useMemo(() => {
    let combined: any[] = [];

    if (activeChannel === CHANNELS.ALL) {
      // Show all channels
      combined = [
        ...socialThreads.map((t: any) => ({ ...t, channel: t.platform })),
        ...smsThreads.map((t: any) => ({ ...t, channel: CHANNELS.SMS })),
      ];
    } else if (activeChannel === CHANNELS.SMS) {
      // Show only SMS
      combined = smsThreads.map((t: any) => ({ ...t, channel: CHANNELS.SMS }));
    } else {
      // Show only selected social platform
      combined = socialThreads.map((t: any) => ({ ...t, channel: t.platform }));
    }

    // Sort by updated_at descending
    return combined.sort((a, b) => {
      const dateA = new Date(a.updated_at || a.timestamp).getTime();
      const dateB = new Date(b.updated_at || b.timestamp).getTime();
      return dateB - dateA;
    });
  }, [socialThreads, smsThreads, activeChannel]);

  const loading = loadingSocial || loadingSms;
  const totalCount = allThreads.length;

  // Calculate stats by channel
  const stats = useMemo(() => {
    const allCombined = [
      ...socialThreads.map((t: any) => ({ ...t, channel: t.platform })),
      ...smsThreads.map((t: any) => ({ ...t, channel: CHANNELS.SMS })),
    ];

    const unreadCount = allCombined.filter((t: any) => !t.is_read).length;
    const fbCount = allCombined.filter((t: any) => t.channel === CHANNELS.FACEBOOK).length;
    const igCount = allCombined.filter((t: any) => t.channel === CHANNELS.INSTAGRAM).length;
    const smsCount = smsThreads.length;

    return {
      total: allCombined.length,
      unread: unreadCount,
      facebook: fbCount,
      instagram: igCount,
      sms: smsCount,
    };
  }, [socialThreads, smsThreads]);

  // Handlers
  const handleChannelChange = (channel: ChannelType) => {
    setActiveChannel(channel);
    setSelectedThread(null); // Clear selection when switching channels
  };

  const handleThreadClick = async (thread: any) => {
    setSelectedThread(thread);
    
    // Mark as read if unread
    if (thread.status === 'unread') {
      try {
        await fetch(`/api/v1/inbox/threads/${thread.thread_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
          },
          body: JSON.stringify({ status: 'read' })
        });
        
        // Refresh threads to show updated status
        if (thread.channel === CHANNELS.SMS) {
          await loadSmsThreads();
        } else {
          await refetchSocial();
        }
      } catch (err) {
        console.error('Failed to mark as read:', err);
      }
    }
  };

  const handleSendMessage = async () => {
    if (!messageText.trim() || !selectedThread) return;

    try {
      if (selectedThread.channel === CHANNELS.SMS) {
        // Send SMS
        await smsService.sendSMS({
          to: selectedThread.phone_number,
          message: messageText,
        });
      } else {
        // Send social media message via inbox API
        await fetch(`/api/v1/inbox/threads/${selectedThread.thread_id}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
          },
          body: JSON.stringify({
            content: messageText,
            direction: 'outbound',
            message_type: 'text'
          })
        });
      }

      setMessageText('');
      setShowQuickReplies(false);

      // Refresh threads
      if (selectedThread.channel === CHANNELS.SMS) {
        await loadSmsThreads();
      } else {
        await refetchSocial();
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      alert('Failed to send message. Please try again.');
    }
  };

  const handleQuickReply = (text: string) => {
    setMessageText(text);
    setShowQuickReplies(false);
  };

  const handleConvertToLead = async (thread: any) => {
    try {
      const threadId = thread.thread_id || thread.id;
      const response = await fetch('/api/leads/social-threads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          thread_id: threadId,
          name: thread.customer_name || thread.from_name || 'Unknown',
          email: thread.customer_email || '',
          phone: thread.phone_number || '',
          source: thread.channel || 'social',
          notes: `Converted from ${thread.channel} thread`,
        })
      });
      
      if (response.ok) {
        alert('Thread converted to lead successfully!');
        // Optionally refresh threads
        if (thread.channel === CHANNELS.SMS) {
          await loadSmsThreads();
        } else {
          await refetchSocial();
        }
      } else {
        throw new Error('Failed to convert');
      }
    } catch (err) {
      console.error('Failed to convert to lead:', err);
      alert('Failed to convert thread to lead. Please try again.');
    }
  };

  // AI Auto-Reply
  const [aiGenerating, setAiGenerating] = useState(false);
  
  const handleAIAutoReply = async () => {
    if (!selectedThread) return;

    try {
      setAiGenerating(true);
      const threadId = selectedThread.thread_id || selectedThread.id;
      
      const response = await fetch(`/api/v1/inbox/threads/${threadId}/ai-reply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
      });

      if (!response.ok) throw new Error('Failed to generate AI reply');

      const data = await response.json();
      setMessageText(data.reply || data.suggested_reply || '');
    } catch (err) {
      console.error('Failed to generate AI reply:', err);
      alert('Failed to generate AI reply. Please try again.');
    } finally {
      setAiGenerating(false);
    }
  };

  // Thread Assignment
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [assigneeId, setAssigneeId] = useState('');
  
  const handleAssignThread = async () => {
    if (!selectedThread || !assigneeId) return;

    try {
      const threadId = selectedThread.thread_id || selectedThread.id;
      
      const response = await fetch(`/api/v1/inbox/threads/${threadId}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          assignee_id: parseInt(assigneeId)
        })
      });

      if (!response.ok) throw new Error('Failed to assign thread');

      alert('Thread assigned successfully!');
      setAssignModalOpen(false);
      setAssigneeId('');

      // Refresh threads
      if (selectedThread.channel === CHANNELS.SMS) {
        await loadSmsThreads();
      } else {
        await refetchSocial();
      }
    } catch (err) {
      console.error('Failed to assign thread:', err);
      alert('Failed to assign thread. Please try again.');
    }
  };

  const handleClearFilters = () => {
    resetFilters();
    setSearchQuery('');
  };

  const handleRefresh = () => {
    if (activeChannel === CHANNELS.SMS || activeChannel === CHANNELS.ALL) {
      loadSmsThreads();
    }
    if (activeChannel !== CHANNELS.SMS) {
      refetchSocial();
    }
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

  // Get quick replies based on channel
  const getQuickReplies = () => {
    if (selectedThread?.channel === CHANNELS.SMS) {
      return QUICK_REPLIES.sms;
    }
    return QUICK_REPLIES.general;
  };

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <EmptyState
          icon={MessageSquare}
          title="Error Loading Inbox"
          description={error}
          actionLabel="Try Again"
          onAction={handleRefresh}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Communication Inbox</h1>
          <p className="text-gray-600">Unified inbox for all customer communications</p>
        </div>
        <Button onClick={handleRefresh}>
          <MessageSquare className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <StatsCard
          title="Total Messages"
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
        <StatsCard
          title="SMS"
          value={stats.sms}
          icon={MessageCircle}
          color="green"
        />
      </div>

      {/* Channel Tabs */}
      <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200">
          <div className="flex">
            {/* All Channels Tab */}
            <button
              onClick={() => handleChannelChange(CHANNELS.ALL)}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeChannel === CHANNELS.ALL
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                All ({stats.total})
              </div>
            </button>

            {/* Facebook Tab */}
            <button
              onClick={() => handleChannelChange(CHANNELS.FACEBOOK)}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeChannel === CHANNELS.FACEBOOK
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <Facebook className="w-4 h-4" />
                Facebook ({stats.facebook})
              </div>
            </button>

            {/* Instagram Tab */}
            <button
              onClick={() => handleChannelChange(CHANNELS.INSTAGRAM)}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeChannel === CHANNELS.INSTAGRAM
                  ? 'text-pink-600 border-b-2 border-pink-600 bg-pink-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <Instagram className="w-4 h-4" />
                Instagram ({stats.instagram})
              </div>
            </button>

            {/* SMS Tab */}
            <button
              onClick={() => handleChannelChange(CHANNELS.SMS)}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeChannel === CHANNELS.SMS
                  ? 'text-green-600 border-b-2 border-green-600 bg-green-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <MessageCircle className="w-4 h-4" />
                SMS ({stats.sms})
              </div>
            </button>

            {/* Email Tab (Future) */}
            <button
              disabled
              className="px-6 py-3 text-sm font-medium text-gray-400 cursor-not-allowed"
            >
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                Email (Soon)
              </div>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <FilterBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            searchPlaceholder="Search conversations..."
            filters={[
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
            onFilterChange={(key, value) => updateFilter(key as 'status', value)}
            onClearFilters={handleClearFilters}
            showClearButton
          />
        </div>

        {/* Loading State */}
        {loading && (
          <div className="p-8">
            <LoadingSpinner message="Loading messages..." />
          </div>
        )}

        {/* Empty State */}
        {!loading && allThreads.length === 0 && (
          <div className="p-8">
            <EmptyState
              icon={MessageSquare}
              title="No messages found"
              description={
                Object.values(filters).some(Boolean) || debouncedQuery
                  ? 'Try adjusting your filters or search query'
                  : 'Customer messages will appear here once they reach out'
              }
            />
          </div>
        )}

        {/* Inbox Layout */}
        {!loading && allThreads.length > 0 && (
          <div className="flex h-[600px]">
            {/* Thread List Sidebar */}
            <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="font-semibold text-gray-900">
                  Conversations ({allThreads.length})
                </h3>
              </div>

              <div className="divide-y divide-gray-200">
                {allThreads.map((thread: any, index) => {
                  const channel = CHANNEL_CONFIG[thread.channel as keyof typeof CHANNEL_CONFIG] || CHANNEL_CONFIG[CHANNELS.FACEBOOK];
                  const ChannelIcon = channel.icon;
                  const threadId = thread.thread_id || thread.id || `thread-${index}`;

                  return (
                    <div
                      key={threadId}
                      onClick={() => handleThreadClick(thread)}
                      className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedThread?.thread_id === thread.thread_id ||
                        selectedThread?.id === thread.id
                          ? `bg-${channel.text.split('-')[1]}-50 border-l-4 ${channel.borderColor}`
                          : !thread.is_read
                          ? 'bg-blue-50 bg-opacity-30'
                          : ''
                      }`}
                    >
                      {/* Thread Header */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`p-1 rounded ${channel.bg}`}>
                            <ChannelIcon className={`w-4 h-4 ${channel.text}`} />
                          </div>
                          <span className="font-medium text-gray-900">
                            {thread.customer_name || thread.from_name || thread.phone_number || 'Unknown'}
                          </span>
                        </div>
                        {!thread.is_read && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full" />
                        )}
                      </div>

                      {/* Last Message Preview */}
                      <p className="text-sm text-gray-600 mb-1 line-clamp-2">
                        {thread.last_message || thread.message || 'No messages yet'}
                      </p>

                      {/* Time and Channel */}
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {formatTime(thread.updated_at || thread.timestamp)}
                        </span>
                        <span className={channel.text}>{channel.label}</span>
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
                            {(selectedThread.customer_name || selectedThread.from_name || selectedThread.phone_number || 'U')[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {selectedThread.customer_name || selectedThread.from_name || selectedThread.phone_number || 'Unknown'}
                          </h3>
                          <p className="text-xs text-gray-500 flex items-center gap-2">
                            {CHANNEL_CONFIG[selectedThread.channel as keyof typeof CHANNEL_CONFIG]?.label || 'Unknown'}
                            {selectedThread.channel === CHANNELS.SMS && selectedThread.phone_number && (
                              <span className="flex items-center">
                                <Phone className="w-3 h-3 mr-1" />
                                {selectedThread.phone_number}
                              </span>
                            )}
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
                        const isFromCustomer = message.direction === 'inbound' || message.direction === 'in';

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
                              <p className="text-sm">{message.text || message.message}</p>
                              <p
                                className={`text-xs mt-1 ${
                                  isFromCustomer ? 'text-gray-500' : 'text-blue-100'
                                }`}
                              >
                                {formatTime(message.timestamp || message.created_at)}
                              </p>
                            </div>
                          </div>
                        );
                      })}

                      {/* Placeholder if no messages */}
                      {(!selectedThread.messages || selectedThread.messages.length === 0) && (
                        <div className="text-center text-gray-500 py-8">
                          <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                          <p>No messages in this conversation yet</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Message Input */}
                  <div className="p-4 border-t border-gray-200 bg-white">
                    {/* AI Actions Bar */}
                    <div className="mb-3 flex items-center justify-between gap-2 p-2 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleAIAutoReply}
                          disabled={aiGenerating}
                          className="text-purple-600 border-purple-300 hover:bg-purple-50"
                        >
                          <Sparkles className={`w-4 h-4 mr-1 ${aiGenerating ? 'animate-spin' : ''}`} />
                          {aiGenerating ? 'Generating...' : 'AI Reply'}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setAssignModalOpen(true)}
                          className="text-blue-600 border-blue-300 hover:bg-blue-50"
                        >
                          <UserPlus className="w-4 h-4 mr-1" />
                          Assign
                        </Button>
                      </div>
                      <span className="text-xs text-gray-500">AI-powered features</span>
                    </div>

                    {/* Quick Replies */}
                    {showQuickReplies && (
                      <div className="mb-3 flex flex-wrap gap-2">
                        {getQuickReplies().map((reply) => (
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
                        <MessageSquare className="w-5 h-5" />
                      </button>
                      <textarea
                        value={messageText}
                        onChange={(e) => setMessageText(e.target.value)}
                        placeholder={
                          selectedThread.channel === CHANNELS.SMS
                            ? 'Type SMS message...'
                            : 'Type your message...'
                        }
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
                    {selectedThread.channel === CHANNELS.SMS && (
                      <p className="text-xs text-gray-500 mt-2">
                        {messageText.length}/160 characters
                      </p>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <p className="text-lg">Select a conversation to view messages</p>
                    <p className="text-sm text-gray-400 mt-2">
                      {activeChannel === CHANNELS.ALL
                        ? 'Showing all channels'
                        : `Showing ${CHANNEL_CONFIG[activeChannel]?.label || 'messages'}`}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Assignment Modal */}
      {assignModalOpen && (
        <Modal
          isOpen={assignModalOpen}
          onClose={() => {
            setAssignModalOpen(false);
            setAssigneeId('');
          }}
          title="Assign Thread"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Assign to Team Member
              </label>
              <select
                value={assigneeId}
                onChange={(e) => setAssigneeId(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="">Select a team member</option>
                <option value="1">Admin User</option>
                <option value="2">Sales Team</option>
                <option value="3">Support Team</option>
                <option value="4">Manager</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                The assigned team member will be notified
              </p>
            </div>

            {selectedThread && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Thread:</span>{' '}
                  {selectedThread.customer_name || selectedThread.from_name || selectedThread.phone_number}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Channel: {CHANNEL_CONFIG[selectedThread.channel as keyof typeof CHANNEL_CONFIG]?.label || 'Unknown'}
                </p>
              </div>
            )}

            <div className="flex justify-end gap-3 mt-6">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setAssignModalOpen(false);
                  setAssigneeId('');
                }}
              >
                Cancel
              </Button>
              <Button
                type="button"
                onClick={handleAssignThread}
                disabled={!assigneeId}
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Assign Thread
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
