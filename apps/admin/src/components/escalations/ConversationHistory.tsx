'use client';

import { Calendar, Filter, Search, X } from 'lucide-react';
import { useMemo, useState } from 'react';

import { getMessageStatus, MessageReadReceipt } from './MessageReadReceipt';

export interface HistoryMessage {
  message_id: string;
  from: string;
  to: string;
  text: string;
  direction: 'inbound' | 'outbound';
  timestamp: string;
  source?: 'admin_panel' | 'ringcentral_app';
  read_at?: string;
  delivered_at?: string;
  failed?: boolean;
  sending?: boolean;
}

export interface HistoryCall {
  rc_call_id: string;
  from: string;
  to: string;
  started_at: string;
  ended_at?: string;
  duration?: number;
  status: string;
  has_recording?: boolean;
}

interface ConversationHistoryProps {
  customerName: string;
  smsMessages: HistoryMessage[];
  calls: HistoryCall[];
}

type MessageType = 'all' | 'sms' | 'calls';
type DateRange = 'all' | 'today' | 'week' | 'month' | 'custom';

export function ConversationHistory({
  customerName,
  smsMessages,
  calls,
}: ConversationHistoryProps) {
  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [messageType, setMessageType] = useState<MessageType>('all');
  const [dateRange, setDateRange] = useState<DateRange>('all');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Filter SMS messages
  const filteredSmsMessages = useMemo(() => {
    if (messageType === 'calls') return [];

    let filtered = [...smsMessages];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(msg => msg.text.toLowerCase().includes(query));
    }

    // Date filter
    const now = new Date();
    let startDate: Date | null = null;
    let endDate: Date | null = null;

    switch (dateRange) {
      case 'today':
        startDate = new Date(now.setHours(0, 0, 0, 0));
        endDate = new Date(now.setHours(23, 59, 59, 999));
        break;
      case 'week':
        startDate = new Date(now.setDate(now.getDate() - 7));
        endDate = new Date();
        break;
      case 'month':
        startDate = new Date(now.setDate(now.getDate() - 30));
        endDate = new Date();
        break;
      case 'custom':
        if (customStartDate) startDate = new Date(customStartDate);
        if (customEndDate) endDate = new Date(customEndDate);
        break;
    }

    if (startDate || endDate) {
      filtered = filtered.filter(msg => {
        const msgDate = new Date(msg.timestamp);
        if (startDate && msgDate < startDate) return false;
        if (endDate && msgDate > endDate) return false;
        return true;
      });
    }

    return filtered.sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [
    smsMessages,
    searchQuery,
    messageType,
    dateRange,
    customStartDate,
    customEndDate,
  ]);

  // Filter calls
  const filteredCalls = useMemo(() => {
    if (messageType === 'sms') return [];

    let filtered = [...calls];

    // Date filter
    const now = new Date();
    let startDate: Date | null = null;
    let endDate: Date | null = null;

    switch (dateRange) {
      case 'today':
        startDate = new Date(now.setHours(0, 0, 0, 0));
        endDate = new Date(now.setHours(23, 59, 59, 999));
        break;
      case 'week':
        startDate = new Date(now.setDate(now.getDate() - 7));
        endDate = new Date();
        break;
      case 'month':
        startDate = new Date(now.setDate(now.getDate() - 30));
        endDate = new Date();
        break;
      case 'custom':
        if (customStartDate) startDate = new Date(customStartDate);
        if (customEndDate) endDate = new Date(customEndDate);
        break;
    }

    if (startDate || endDate) {
      filtered = filtered.filter(call => {
        const callDate = new Date(call.started_at);
        if (startDate && callDate < startDate) return false;
        if (endDate && callDate > endDate) return false;
        return true;
      });
    }

    return filtered.sort(
      (a, b) =>
        new Date(a.started_at).getTime() - new Date(b.started_at).getTime()
    );
  }, [calls, messageType, dateRange, customStartDate, customEndDate]);

  // Create unified timeline
  const timeline = useMemo(() => {
    const items: Array<{
      type: 'sms' | 'call';
      timestamp: string;
      data: HistoryMessage | HistoryCall;
    }> = [];

    filteredSmsMessages.forEach(msg => {
      items.push({
        type: 'sms',
        timestamp: msg.timestamp,
        data: msg,
      });
    });

    filteredCalls.forEach(call => {
      items.push({
        type: 'call',
        timestamp: call.started_at,
        data: call,
      });
    });

    return items.sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [filteredSmsMessages, filteredCalls]);

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setMessageType('all');
    setDateRange('all');
    setCustomStartDate('');
    setCustomEndDate('');
  };

  // Format time
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / 3600000);

    if (hours < 24) {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
      });
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      });
    }
  };

  // Format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Active filter count
  const activeFiltersCount = [
    searchQuery !== '',
    messageType !== 'all',
    dateRange !== 'all',
  ].filter(Boolean).length;

  return (
    <div className="space-y-4">
      {/* Filter Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <Filter size={16} />
            <span className="text-sm font-medium">Filters</span>
            {activeFiltersCount > 0 && (
              <span className="px-2 py-0.5 bg-orange-500 text-white text-xs rounded-full">
                {activeFiltersCount}
              </span>
            )}
          </button>

          {activeFiltersCount > 0 && (
            <button
              onClick={clearFilters}
              className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
            >
              <X size={14} />
              <span>Clear</span>
            </button>
          )}
        </div>

        <div className="text-sm text-gray-600">
          {timeline.length} {timeline.length === 1 ? 'item' : 'items'}
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Messages
            </label>
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                size={16}
              />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search in message content..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Message Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message Type
            </label>
            <div className="flex space-x-2">
              {(['all', 'sms', 'calls'] as MessageType[]).map(type => (
                <button
                  key={type}
                  onClick={() => setMessageType(type)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    messageType === type
                      ? 'bg-orange-500 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {type === 'all'
                    ? 'All'
                    : type === 'sms'
                      ? 'SMS Only'
                      : 'Calls Only'}
                </button>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {(['all', 'today', 'week', 'month', 'custom'] as DateRange[]).map(
                range => (
                  <button
                    key={range}
                    onClick={() => setDateRange(range)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      dateRange === range
                        ? 'bg-orange-500 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {range === 'all'
                      ? 'All Time'
                      : range === 'today'
                        ? 'Today'
                        : range === 'week'
                          ? 'Last 7 Days'
                          : range === 'month'
                            ? 'Last 30 Days'
                            : 'Custom Range'}
                  </button>
                )
              )}
            </div>

            {/* Custom Date Inputs */}
            {dateRange === 'custom' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    Start Date
                  </label>
                  <div className="relative">
                    <Calendar
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                      size={14}
                    />
                    <input
                      type="date"
                      value={customStartDate}
                      onChange={e => setCustomStartDate(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    End Date
                  </label>
                  <div className="relative">
                    <Calendar
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                      size={14}
                    />
                    <input
                      type="date"
                      value={customEndDate}
                      onChange={e => setCustomEndDate(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {timeline.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No conversation history found</p>
            {activeFiltersCount > 0 && (
              <button
                onClick={clearFilters}
                className="mt-2 text-sm text-orange-600 hover:text-orange-700"
              >
                Clear filters to see all messages
              </button>
            )}
          </div>
        ) : (
          timeline.map((item, idx) => {
            if (item.type === 'sms') {
              const msg = item.data as HistoryMessage;
              const messageStatus = getMessageStatus({
                timestamp: msg.timestamp,
                delivered_at: msg.delivered_at,
                read_at: msg.read_at,
                failed: msg.failed,
                sending: msg.sending,
              });

              return (
                <div
                  key={`sms-${msg.message_id}-${idx}`}
                  className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-md rounded-lg p-3 ${
                      msg.direction === 'outbound'
                        ? 'bg-orange-100 text-gray-900'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="flex items-start justify-between space-x-2 mb-1">
                      <p className="text-xs font-medium text-gray-600">
                        {msg.direction === 'outbound' ? 'You' : customerName}
                      </p>
                      {msg.source && (
                        <span className="text-xs text-gray-500 flex items-center space-x-1">
                          {msg.source === 'admin_panel' ? (
                            <>
                              <span>💻</span>
                              <span>Panel</span>
                            </>
                          ) : (
                            <>
                              <span>📱</span>
                              <span>RC App</span>
                            </>
                          )}
                        </span>
                      )}
                    </div>
                    <p className="text-sm whitespace-pre-wrap break-words">
                      {searchQuery &&
                      msg.text
                        .toLowerCase()
                        .includes(searchQuery.toLowerCase()) ? (
                        // Highlight search terms
                        <span
                          dangerouslySetInnerHTML={{
                            __html: msg.text.replace(
                              new RegExp(`(${searchQuery})`, 'gi'),
                              '<mark class="bg-yellow-200">$1</mark>'
                            ),
                          }}
                        />
                      ) : (
                        msg.text
                      )}
                    </p>
                    <div className="flex items-center justify-between mt-2 space-x-3">
                      <p className="text-xs text-gray-500">
                        {formatTime(msg.timestamp)}
                      </p>
                      {msg.direction === 'outbound' && (
                        <MessageReadReceipt
                          status={messageStatus}
                          timestamp={msg.timestamp}
                          readAt={msg.read_at}
                          deliveredAt={msg.delivered_at}
                          size="sm"
                        />
                      )}
                    </div>
                  </div>
                </div>
              );
            } else {
              const call = item.data as HistoryCall;
              return (
                <div
                  key={`call-${call.rc_call_id}-${idx}`}
                  className="bg-blue-50 border border-blue-200 rounded-lg p-3"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">📞</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          Phone Call
                        </p>
                        <p className="text-xs text-gray-600">
                          {call.status === 'Completed'
                            ? '✅ Completed'
                            : call.status}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {formatTime(call.started_at)}
                      </p>
                      {call.duration && (
                        <p className="text-xs text-gray-600 font-medium">
                          {formatDuration(call.duration)}
                        </p>
                      )}
                    </div>
                  </div>
                  {call.has_recording && (
                    <div className="mt-2 text-xs text-blue-700 flex items-center space-x-1">
                      <span>🎙️</span>
                      <span>Recording available</span>
                    </div>
                  )}
                </div>
              );
            }
          })
        )}
      </div>
    </div>
  );
}
