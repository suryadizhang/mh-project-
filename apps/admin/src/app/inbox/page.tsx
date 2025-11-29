'use client';

import {
  Circle,
  Clock,
  Facebook,
  Instagram,
  Mail,
  MessageCircle,
  MessageSquare,
  Phone,
  Plus,
  Send,
  Sparkles,
  Target,
  UserPlus,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { FilterBar } from '@/components/ui/filter-bar';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Modal } from '@/components/ui/modal';
import { StatsCard } from '@/components/ui/stats-card';
import { useToast } from '@/components/ui/Toast';
import { LabelList } from '@/components/email/LabelBadge';
import { LabelPicker } from '@/components/email/LabelPicker';
import {
  useFilters,
  usePagination,
  useSearch,
  useSocialThreads,
} from '@/hooks/useApi';
import { smsService } from '@/services/api';
import { emailService, labelService } from '@/services/email-api';
import type {
  Email,
  EmailThread as EmailThreadType,
  Label,
} from '@/types/email';

// Channel types
const CHANNELS = {
  ALL: 'all',
  FACEBOOK: 'facebook',
  INSTAGRAM: 'instagram',
  SMS: 'sms',
  EMAIL: 'email', // Future
} as const;

type ChannelType = (typeof CHANNELS)[keyof typeof CHANNELS];

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
  // Toast notifications
  const toast = useToast();

  // State
  const [activeChannel, setActiveChannel] = useState<ChannelType>(CHANNELS.ALL);
  const [selectedThread, setSelectedThread] = useState<any>(null);
  const [messageText, setMessageText] = useState('');
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const [smsThreads, setSmsThreads] = useState<any[]>([]);
  const [loadingSms, setLoadingSms] = useState(false);
  const [emailThreads, setEmailThreads] = useState<Email[]>([]);
  const [loadingEmail, setLoadingEmail] = useState(false);
  const [labels, setLabels] = useState<Label[]>([]);
  const [showLabelPicker, setShowLabelPicker] = useState(false);

  // Pagination and filters
  const { page, limit } = usePagination(1, 50);
  const {
    query: searchQuery,
    debouncedQuery,
    setQuery: setSearchQuery,
  } = useSearch();
  const { filters, updateFilter, resetFilters } = useFilters({
    status: '',
  });

  // Combine all filters for API call (social threads)
  const apiFilters = useMemo(
    () => ({
      ...filters,
      platform:
        activeChannel !== CHANNELS.ALL && activeChannel !== CHANNELS.SMS
          ? activeChannel
          : undefined,
      search: debouncedQuery,
      page,
      limit,
      sort_by: 'updated_at',
      sort_order: 'desc' as const,
    }),
    [activeChannel, filters, debouncedQuery, page, limit]
  );

  // Fetch social media threads (FB/IG)
  const {
    data: socialResponse,
    loading: loadingSocial,
    error,
    refetch: refetchSocial,
  } = useSocialThreads(activeChannel !== CHANNELS.SMS ? apiFilters : null);

  const socialThreads = socialResponse?.data || [];

  // Load SMS threads when channel is active
  const loadSmsThreads = useCallback(async () => {
    if (activeChannel !== CHANNELS.SMS && activeChannel !== CHANNELS.ALL)
      return;

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

  // Load email threads when channel is active
  const loadEmailThreads = useCallback(async () => {
    if (activeChannel !== CHANNELS.EMAIL && activeChannel !== CHANNELS.ALL)
      return;

    setLoadingEmail(true);
    try {
      const response = await emailService.getEmails({ page: 1, limit: 50 });
      setEmailThreads(response.emails || []);
    } catch (err) {
      console.error('Failed to load email threads:', err);
    } finally {
      setLoadingEmail(false);
    }
  }, [activeChannel]);

  // Load labels on mount
  const loadLabels = useCallback(async () => {
    try {
      const data = await labelService.getLabels();
      setLabels(data);
    } catch (err) {
      console.error('Failed to load labels:', err);
    }
  }, []);

  // Load SMS and Email on mount and when channel changes
  useEffect(() => {
    if (activeChannel === CHANNELS.SMS || activeChannel === CHANNELS.ALL) {
      loadSmsThreads();
    }
    if (activeChannel === CHANNELS.EMAIL || activeChannel === CHANNELS.ALL) {
      loadEmailThreads();
    }
    loadLabels();
  }, [activeChannel, loadSmsThreads, loadEmailThreads, loadLabels]);

  // Combine and filter all threads based on active channel
  const allThreads = useMemo(() => {
    let combined: any[] = [];

    if (activeChannel === CHANNELS.ALL) {
      // Show all channels
      combined = [
        ...socialThreads.map((t: any) => ({ ...t, channel: t.platform })),
        ...smsThreads.map((t: any) => ({ ...t, channel: CHANNELS.SMS })),
        ...emailThreads.map((e: Email) => ({
          ...e,
          channel: CHANNELS.EMAIL,
          thread_id: e.thread_id,
          customer_name: e.from_name || e.from_address.split('@')[0],
          updated_at: e.received_at,
          is_read: e.is_read,
        })),
      ];
    } else if (activeChannel === CHANNELS.SMS) {
      // Show only SMS
      combined = smsThreads.map((t: any) => ({ ...t, channel: CHANNELS.SMS }));
    } else if (activeChannel === CHANNELS.EMAIL) {
      // Show only Email
      combined = emailThreads.map((e: Email) => ({
        ...e,
        channel: CHANNELS.EMAIL,
        thread_id: e.thread_id,
        customer_name: e.from_name || e.from_address.split('@')[0],
        updated_at: e.received_at,
        is_read: e.is_read,
      }));
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
  }, [socialThreads, smsThreads, emailThreads, activeChannel]);

  const loading = loadingSocial || loadingSms || loadingEmail;
  const totalCount = allThreads.length;

  // Calculate stats by channel
  const stats = useMemo(() => {
    const allCombined = [
      ...socialThreads.map((t: any) => ({ ...t, channel: t.platform })),
      ...smsThreads.map((t: any) => ({ ...t, channel: CHANNELS.SMS })),
      ...emailThreads.map((e: Email) => ({
        ...e,
        channel: CHANNELS.EMAIL,
        is_read: e.is_read,
      })),
    ];

    const unreadCount = allCombined.filter((t: any) => !t.is_read).length;
    const fbCount = allCombined.filter(
      (t: any) => t.channel === CHANNELS.FACEBOOK
    ).length;
    const igCount = allCombined.filter(
      (t: any) => t.channel === CHANNELS.INSTAGRAM
    ).length;
    const smsCount = smsThreads.length;
    const emailCount = emailThreads.length;

    return {
      total: allCombined.length,
      unread: unreadCount,
      facebook: fbCount,
      instagram: igCount,
      sms: smsCount,
      email: emailCount,
    };
  }, [socialThreads, smsThreads, emailThreads]);

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
            Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
          },
          body: JSON.stringify({ status: 'read' }),
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
        await fetch(
          `/api/v1/inbox/threads/${selectedThread.thread_id}/messages`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
            },
            body: JSON.stringify({
              content: messageText,
              direction: 'outbound',
              message_type: 'text',
            }),
          }
        );
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
      toast.error(
        'Failed to send message',
        'Please check your connection and try again'
      );
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
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
        },
        body: JSON.stringify({
          thread_id: threadId,
          name: thread.customer_name || thread.from_name || 'Unknown',
          email: thread.customer_email || '',
          phone: thread.phone_number || '',
          source: thread.channel || 'social',
          notes: `Converted from ${thread.channel} thread`,
        }),
      });

      if (response.ok) {
        toast.success(
          'Converted to lead!',
          'Thread has been added to leads pipeline'
        );
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
      toast.error(
        'Conversion failed',
        'Unable to create lead from this thread'
      );
    }
  };

  // AI Auto-Reply
  const [aiGenerating, setAiGenerating] = useState(false);

  const handleAIAutoReply = async () => {
    if (!selectedThread) return;

    try {
      setAiGenerating(true);
      const threadId = selectedThread.thread_id || selectedThread.id;

      const response = await fetch(
        `/api/v1/inbox/threads/${threadId}/ai-reply`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to generate AI reply');

      const data = await response.json();
      setMessageText(data.reply || data.suggested_reply || '');
    } catch (err) {
      console.error('Failed to generate AI reply:', err);
      toast.error('AI generation failed', 'Please try generating reply again');
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
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
        },
        body: JSON.stringify({
          assignee_id: parseInt(assigneeId),
        }),
      });

      if (!response.ok) throw new Error('Failed to assign thread');

      toast.success('Thread assigned!', 'Team member has been notified');
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
      toast.error('Assignment failed', 'Unable to assign thread at this time');
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
          <h1 className="text-3xl font-bold text-gray-900">
            Communication Inbox
          </h1>
          <p className="text-gray-600">
            Unified inbox for all customer communications
          </p>
        </div>
        <Button onClick={handleRefresh}>
          <MessageSquare className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-6">
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
        <StatsCard
          title="Email"
          value={stats.email}
          icon={Mail}
          color="purple"
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

            {/* Email Tab */}
            <button
              onClick={() => handleChannelChange(CHANNELS.EMAIL)}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeChannel === CHANNELS.EMAIL
                  ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                Email ({stats.email})
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
            onFilterChange={(key, value) =>
              updateFilter(key as 'status', value)
            }
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
          <div className="flex flex-col md:flex-row h-auto md:h-[600px]">
            {/* Thread List Sidebar */}
            <div className="w-full md:w-1/3 border-r-0 md:border-r border-b md:border-b-0 border-gray-200 overflow-y-auto max-h-96 md:max-h-none">
              <div className="p-4 border-b border-gray-200 bg-gray-50 sticky top-0 z-10">
                <h3 className="font-semibold text-gray-900">
                  Conversations ({allThreads.length})
                </h3>
              </div>

              <div className="divide-y divide-gray-200">
                {allThreads.map((thread: any, index) => {
                  const channel =
                    CHANNEL_CONFIG[
                      thread.channel as keyof typeof CHANNEL_CONFIG
                    ] || CHANNEL_CONFIG[CHANNELS.FACEBOOK];
                  const ChannelIcon = channel.icon;
                  const threadId =
                    thread.thread_id || thread.id || `thread-${index}`;

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
                            <ChannelIcon
                              className={`w-4 h-4 ${channel.text}`}
                            />
                          </div>
                          <span className="font-medium text-gray-900">
                            {thread.customer_name ||
                              thread.from_name ||
                              thread.phone_number ||
                              'Unknown'}
                          </span>
                        </div>
                        {!thread.is_read && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full" />
                        )}
                      </div>

                      {/* Last Message Preview */}
                      <p className="text-sm text-gray-600 mb-1 line-clamp-2">
                        {thread.last_message ||
                          thread.message ||
                          thread.subject ||
                          'No messages yet'}
                      </p>

                      {/* Labels for Email Threads */}
                      {thread.channel === CHANNELS.EMAIL &&
                        thread.labels &&
                        thread.labels.length > 0 && (
                          <div className="mb-2">
                            <LabelList
                              labels={labels.filter(l =>
                                thread.labels.includes(l.slug)
                              )}
                              maxVisible={2}
                              size="sm"
                            />
                          </div>
                        )}

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
            <div className="flex-1 flex flex-col w-full md:w-2/3">
              {selectedThread ? (
                <>
                  {/* Conversation Header */}
                  <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-sm font-medium text-gray-700">
                            {(selectedThread.customer_name ||
                              selectedThread.from_name ||
                              selectedThread.phone_number ||
                              'U')[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900 text-sm sm:text-base">
                            {selectedThread.customer_name ||
                              selectedThread.from_name ||
                              selectedThread.phone_number ||
                              'Unknown'}
                          </h3>
                          <p className="text-xs text-gray-500 flex flex-wrap items-center gap-2">
                            <span>
                              {CHANNEL_CONFIG[
                                selectedThread.channel as keyof typeof CHANNEL_CONFIG
                              ]?.label || 'Unknown'}
                            </span>
                            {selectedThread.channel === CHANNELS.SMS &&
                              selectedThread.phone_number && (
                                <span className="flex items-center">
                                  <Phone className="w-3 h-3 mr-1" />
                                  <span className="text-xs">
                                    {selectedThread.phone_number}
                                  </span>
                                </span>
                              )}
                            {selectedThread.channel === CHANNELS.EMAIL &&
                              selectedThread.from_address && (
                                <span className="text-xs">
                                  {selectedThread.from_address}
                                </span>
                              )}
                          </p>
                          {/* Email Labels */}
                          {selectedThread.channel === CHANNELS.EMAIL && (
                            <div className="mt-2 flex items-center gap-2">
                              {selectedThread.labels &&
                              selectedThread.labels.length > 0 ? (
                                <LabelList
                                  labels={labels.filter(l =>
                                    selectedThread.labels.includes(l.slug)
                                  )}
                                  onRemove={async labelSlug => {
                                    const updatedLabels =
                                      selectedThread.labels.filter(
                                        (l: string) => l !== labelSlug
                                      );
                                    await emailService.updateEmail(
                                      selectedThread.message_id,
                                      {
                                        labels: updatedLabels,
                                      }
                                    );
                                    await loadEmailThreads();
                                  }}
                                  maxVisible={5}
                                  size="sm"
                                />
                              ) : (
                                <span className="text-xs text-gray-400">
                                  No labels
                                </span>
                              )}
                              <button
                                onClick={() => setShowLabelPicker(true)}
                                className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
                              >
                                <Plus className="w-3 h-3" />
                                Add Label
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleConvertToLead(selectedThread)}
                        className="w-full sm:w-auto"
                      >
                        <Target className="w-4 h-4 mr-1" />
                        <span className="text-xs sm:text-sm">
                          Convert to Lead
                        </span>
                      </Button>
                    </div>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
                    <div className="space-y-4">
                      {selectedThread.messages?.map(
                        (message: any, index: number) => {
                          const isFromCustomer =
                            message.direction === 'inbound' ||
                            message.direction === 'in';

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
                                <p className="text-sm">
                                  {message.text || message.message}
                                </p>
                                <p
                                  className={`text-xs mt-1 ${
                                    isFromCustomer
                                      ? 'text-gray-500'
                                      : 'text-blue-100'
                                  }`}
                                >
                                  {formatTime(
                                    message.timestamp || message.created_at
                                  )}
                                </p>
                              </div>
                            </div>
                          );
                        }
                      )}

                      {/* Placeholder if no messages */}
                      {(!selectedThread.messages ||
                        selectedThread.messages.length === 0) && (
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
                    <div className="mb-3 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 p-2 bg-gray-50 rounded-lg">
                      <div className="flex flex-wrap sm:flex-nowrap items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleAIAutoReply}
                          disabled={aiGenerating}
                          className="flex-1 sm:flex-none text-purple-600 border-purple-300 hover:bg-purple-50 min-w-0"
                        >
                          <Sparkles
                            className={`w-4 h-4 mr-1 flex-shrink-0 ${aiGenerating ? 'animate-spin' : ''}`}
                          />
                          <span className="truncate">
                            {aiGenerating ? 'Generating...' : 'AI Reply'}
                          </span>
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setAssignModalOpen(true)}
                          className="flex-1 sm:flex-none text-blue-600 border-blue-300 hover:bg-blue-50 min-w-0"
                        >
                          <UserPlus className="w-4 h-4 mr-1 flex-shrink-0" />
                          <span className="truncate">Assign</span>
                        </Button>
                      </div>
                      <span className="text-xs text-gray-500 text-center sm:text-right">
                        AI-powered features
                      </span>
                    </div>

                    {/* Quick Replies */}
                    {showQuickReplies && (
                      <div className="mb-3 flex flex-wrap gap-2">
                        {getQuickReplies().map(reply => (
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
                        onChange={e => setMessageText(e.target.value)}
                        placeholder={
                          selectedThread.channel === CHANNELS.SMS
                            ? 'Type SMS message...'
                            : 'Type your message...'
                        }
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        rows={2}
                        onKeyDown={e => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                      />
                      <Button
                        onClick={handleSendMessage}
                        disabled={!messageText.trim()}
                      >
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
                    <p className="text-lg">
                      Select a conversation to view messages
                    </p>
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
                onChange={e => setAssigneeId(e.target.value)}
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
                  {selectedThread.customer_name ||
                    selectedThread.from_name ||
                    selectedThread.phone_number}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Channel:{' '}
                  {CHANNEL_CONFIG[
                    selectedThread.channel as keyof typeof CHANNEL_CONFIG
                  ]?.label || 'Unknown'}
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

      {/* Label Picker Modal */}
      {showLabelPicker && selectedThread?.channel === CHANNELS.EMAIL && (
        <LabelPicker
          isOpen={showLabelPicker}
          onClose={() => setShowLabelPicker(false)}
          selectedLabels={selectedThread.labels || []}
          onToggleLabel={async labelSlug => {
            const currentLabels = selectedThread.labels || [];
            const updatedLabels = currentLabels.includes(labelSlug)
              ? currentLabels.filter((l: string) => l !== labelSlug)
              : [...currentLabels, labelSlug];

            try {
              await emailService.updateEmail(selectedThread.message_id, {
                labels: updatedLabels,
              });
              // Update local state
              setSelectedThread({
                ...selectedThread,
                labels: updatedLabels,
              });
              // Reload email threads
              await loadEmailThreads();
              toast.success(
                'Labels updated',
                'Email labels have been updated successfully'
              );
            } catch (error) {
              toast.error('Failed to update labels', 'Please try again');
            }
          }}
        />
      )}
    </div>
  );
}
