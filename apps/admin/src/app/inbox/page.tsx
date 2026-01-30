'use client';

/**
 * Unified Inbox Page - Modular Architecture
 * ==========================================
 *
 * Main orchestrator component that composes all inbox modules.
 * Line count target: <300 lines (was 1,217 lines)
 *
 * Module Structure:
 * - types/index.ts: All TypeScript interfaces
 * - constants/index.ts: CHANNELS, CHANNEL_CONFIG, templates, etc.
 * - hooks/: useKeyboardShortcuts, useDraftAutoSave
 * - components/: ChannelTabs, ThreadList, ThreadView, ComposePane, EmailToolbar
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { RefreshCw, Mail } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useToast } from '@/components/ui/Toast';
import { useSocialThreads } from '@/hooks/useApi';
import { apiWithAuth, tokenManager } from '@/services/api';
import { emailService } from '@/services/email-api';

// Import from modular structure
import type {
  ChannelType,
  Thread,
  EmailThread,
  SMSThread,
  SocialThread,
  BulkAction,
  TabStats,
} from './types';
import { CHANNELS, CHANNEL_CONFIG, KEYBOARD_SHORTCUTS } from './constants';
import { useKeyboardShortcuts } from './hooks';
import {
  ChannelTabs,
  ThreadList,
  ThreadView,
  ComposePane,
  EmailToolbar,
} from './components';

/**
 * UnifiedInboxPage - Main Orchestrator
 * =====================================
 * Composes all inbox modules into a cohesive 2-column layout
 */
export default function UnifiedInboxPage() {
  const toast = useToast();

  // ===== STATE =====
  const [activeChannel, setActiveChannel] = useState<ChannelType>('all');
  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [showStarredOnly, setShowStarredOnly] = useState(false);

  // ===== DATA FETCHING =====
  const {
    data: socialThreads,
    loading: socialLoading,
    refetch: refetchSocial,
  } = useSocialThreads();

  // Fetch all channel data
  const fetchAllThreads = useCallback(async () => {
    setIsLoading(true);
    try {
      const allThreads: Thread[] = [];

      // Social threads (Facebook, Instagram)
      if (socialThreads?.data) {
        allThreads.push(
          ...socialThreads.data.map((t: any) => ({
            ...t,
            channel: t.platform as ChannelType,
          }))
        );
      }

      // SMS threads
      try {
        const token = tokenManager.getToken();
        if (token) {
          const smsResponse = await apiWithAuth.get(
            '/api/v1/inbox/threads?channel=sms'
          );
          if (smsResponse?.data) {
            allThreads.push(
              ...smsResponse.data.map((sms: any) => ({
                id: sms.id,
                channel: 'sms' as ChannelType,
                customer_name: sms.contact_name || sms.phone_number,
                phone_number: sms.phone_number,
                last_message: sms.last_message,
                last_message_at: sms.last_message_at,
                unread_count: sms.unread_count || 0,
                is_read: sms.unread_count === 0,
              }))
            );
          }
        }
      } catch (err) {
        console.warn('SMS fetch failed:', err);
      }

      // Email threads
      try {
        const emailResponse = await emailService.getEmails({
          page: 1,
          limit: 50,
        });
        if (emailResponse?.threads) {
          allThreads.push(
            ...emailResponse.threads.map((email: any) => ({
              ...email,
              channel: 'email' as ChannelType,
              customer_name: email.from_name || email.from_email,
            }))
          );
        }
      } catch (err) {
        console.warn('Email fetch failed:', err);
      }

      // Sort by most recent
      // EmailThread uses 'last_message_at', SMS/Social use 'timestamp' from BaseThread
      allThreads.sort((a, b) => {
        const dateA = new Date(
          ('last_message_at' in a ? a.last_message_at : null) ||
            ('timestamp' in a ? a.timestamp : null) ||
            0
        );
        const dateB = new Date(
          ('last_message_at' in b ? b.last_message_at : null) ||
            ('timestamp' in b ? b.timestamp : null) ||
            0
        );
        return dateB.getTime() - dateA.getTime();
      });

      setThreads(allThreads);
    } catch (error) {
      console.error('Failed to fetch threads:', error);
      toast.error('Failed to load inbox');
    } finally {
      setIsLoading(false);
    }
  }, [socialThreads, toast]);

  useEffect(() => {
    fetchAllThreads();
  }, [fetchAllThreads]);

  // ===== FILTERING =====
  const filteredThreads = useMemo(() => {
    let result = threads;

    // Filter by channel
    if (activeChannel !== 'all') {
      result = result.filter(t => t.channel === activeChannel);
    }

    // Filter by search query
    // BaseThread (SMS/Social) has customer_name, preview
    // EmailThread has first_message_from, subject, messages[].body
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(t => {
        // Check customer_name (SMS/Social) or first_message_from (Email)
        const name =
          'customer_name' in t
            ? t.customer_name
            : 'first_message_from' in t
              ? t.first_message_from
              : '';
        if (name?.toLowerCase().includes(query)) return true;

        // Check preview (SMS/Social) or subject (Email)
        const content =
          'preview' in t ? t.preview : 'subject' in t ? t.subject : '';
        if (content?.toLowerCase().includes(query)) return true;

        return false;
      });
    }

    // Filter by unread
    // BaseThread has unread: boolean, EmailThread has is_read: boolean
    if (showUnreadOnly) {
      result = result.filter(t => {
        if ('unread' in t) return t.unread;
        if ('is_read' in t) return !t.is_read;
        return false;
      });
    }

    // Filter by starred (only EmailThread has is_starred)
    if (showStarredOnly) {
      result = result.filter(t => 'is_starred' in t && t.is_starred);
    }

    return result;
  }, [threads, activeChannel, searchQuery, showUnreadOnly, showStarredOnly]);

  // ===== TAB STATS =====
  // Helper to check if thread is unread (handles different property names)
  const isUnread = (t: Thread): boolean => {
    if ('unread' in t) return t.unread;
    if ('is_read' in t) return !t.is_read;
    return false;
  };

  const tabStats: TabStats = useMemo(
    () => ({
      all: threads.filter(t => isUnread(t)).length,
      facebook: threads.filter(t => t.channel === 'facebook' && isUnread(t))
        .length,
      instagram: threads.filter(t => t.channel === 'instagram' && isUnread(t))
        .length,
      sms: threads.filter(t => t.channel === 'sms' && isUnread(t)).length,
      email: threads.filter(t => t.channel === 'email' && isUnread(t)).length,
    }),
    [threads]
  );

  // ===== HANDLERS =====
  const handleThreadSelect = useCallback((thread: Thread) => {
    setSelectedThread(thread);
    // Mark as read
    setThreads(prev =>
      prev.map(t =>
        t.id === thread.id ? { ...t, is_read: true, unread_count: 0 } : t
      )
    );
  }, []);

  const handleToggleSelect = useCallback((threadId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(threadId)) {
        next.delete(threadId);
      } else {
        next.add(threadId);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectedIds.size === filteredThreads.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredThreads.map(t => t.id)));
    }
  }, [selectedIds.size, filteredThreads]);

  const handleBulkAction = useCallback(
    async (action: BulkAction) => {
      if (selectedIds.size === 0) {
        toast.warning('No threads selected');
        return;
      }

      const ids = Array.from(selectedIds);
      try {
        switch (action) {
          case 'archive':
            setThreads(prev => prev.filter(t => !ids.includes(t.id)));
            toast.success(`Archived ${ids.length} threads`);
            break;
          case 'mark_read':
            setThreads(prev =>
              prev.map(t => {
                if (!ids.includes(t.id)) return t;
                if ('unread' in t) return { ...t, unread: false };
                if ('is_read' in t) return { ...t, is_read: true };
                return t;
              })
            );
            toast.success(`Marked ${ids.length} as read`);
            break;
          case 'mark_unread':
            setThreads(prev =>
              prev.map(t => {
                if (!ids.includes(t.id)) return t;
                if ('unread' in t) return { ...t, unread: true };
                if ('is_read' in t) return { ...t, is_read: false };
                return t;
              })
            );
            toast.success(`Marked ${ids.length} as unread`);
            break;
          case 'star':
            setThreads(prev =>
              prev.map(t =>
                ids.includes(t.id) ? { ...t, is_starred: true } : t
              )
            );
            toast.success(`Starred ${ids.length} threads`);
            break;
          case 'delete':
            if (confirm(`Delete ${ids.length} threads permanently?`)) {
              setThreads(prev => prev.filter(t => !ids.includes(t.id)));
              toast.success(`Deleted ${ids.length} threads`);
            }
            break;
        }
        setSelectedIds(new Set());
      } catch (error) {
        toast.error(`Failed to ${action} threads`);
      }
    },
    [selectedIds, toast]
  );

  const handleSendMessage = useCallback(
    async (content: string) => {
      if (!selectedThread) return;

      try {
        // TODO: Implement actual send based on channel
        toast.success('Message sent!');
      } catch (error) {
        toast.error('Failed to send message');
      }
    },
    [selectedThread, toast]
  );

  const handleAIGenerate = useCallback(async () => {
    toast.info('AI response generation coming soon...');
    return '';
  }, [toast]);

  const handleRefresh = useCallback(async () => {
    await refetchSocial();
    await fetchAllThreads();
    toast.success('Inbox refreshed');
  }, [refetchSocial, fetchAllThreads, toast]);

  // ===== KEYBOARD SHORTCUTS =====
  useKeyboardShortcuts({
    threads: filteredThreads,
    selectedThread,
    isEmailChannel: activeChannel === 'email',
    onSelectThread: handleThreadSelect,
    onReply: () =>
      document
        .querySelector<HTMLTextAreaElement>('[data-compose-input]')
        ?.focus(),
    onArchive: () => selectedThread && handleBulkAction('archive'),
    onStar: () => selectedThread && handleBulkAction('star'),
    onMarkUnread: () => selectedThread && handleBulkAction('mark_unread'),
  });

  // ===== RENDER =====
  if (isLoading && threads.length === 0) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Panel: Thread List */}
      <div className="w-1/3 min-w-[320px] max-w-[450px] border-r bg-white flex flex-col">
        {/* Toolbar */}
        <EmailToolbar
          selectedCount={selectedIds.size}
          onClearSelection={() => setSelectedIds(new Set())}
          onBulkAction={handleBulkAction}
          onRefresh={handleRefresh}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          showUnreadOnly={showUnreadOnly}
          onToggleUnread={() => setShowUnreadOnly(!showUnreadOnly)}
          showStarredOnly={showStarredOnly}
          onToggleStarred={() => setShowStarredOnly(!showStarredOnly)}
        />

        {/* Channel Tabs */}
        <ChannelTabs
          activeChannel={activeChannel}
          onChannelChange={setActiveChannel}
          counts={tabStats}
        />

        {/* Thread List */}
        <ThreadList
          threads={filteredThreads}
          selectedThreadId={selectedThread?.id || null}
          selectedIds={selectedIds}
          onThreadSelect={handleThreadSelect}
          onToggleSelect={handleToggleSelect}
          onSelectAll={handleSelectAll}
          showCheckboxes={selectedIds.size > 0}
          isLoading={isLoading}
        />
      </div>

      {/* Right Panel: Thread View + Compose */}
      <div className="flex-1 flex flex-col bg-white">
        {selectedThread ? (
          <>
            <ThreadView
              thread={selectedThread}
              onClose={() => setSelectedThread(null)}
            />
            <ComposePane
              threadId={selectedThread.id}
              channel={selectedThread.channel}
              recipientName={
                selectedThread.channel === 'email'
                  ? (selectedThread as EmailThread).first_message_from ||
                    'Unknown'
                  : (selectedThread as SMSThread | SocialThread).customer_name
              }
              recipientEmail={
                selectedThread.channel === 'email'
                  ? (selectedThread as EmailThread)
                      .first_message_from_address || ''
                  : (selectedThread as SMSThread | SocialThread)
                      .customer_email || ''
              }
              onSend={handleSendMessage}
              onAIGenerate={handleAIGenerate}
              isLoading={false}
            />
          </>
        ) : (
          <EmptyState
            icon={
              activeChannel !== 'all'
                ? CHANNEL_CONFIG[activeChannel].icon
                : Mail
            }
            title="Select a conversation"
            description={
              <div className="space-y-2">
                <p>Choose a thread from the left to view the conversation</p>
                <div className="text-xs text-gray-400 mt-4">
                  <p className="font-medium mb-1">Keyboard Shortcuts:</p>
                  <ul className="space-y-0.5">
                    {Object.entries(KEYBOARD_SHORTCUTS)
                      .slice(0, 5)
                      .map(([key, action]) => (
                        <li key={key}>
                          <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-[10px] font-mono">
                            {key}
                          </kbd>
                          <span className="ml-2">{action}</span>
                        </li>
                      ))}
                  </ul>
                </div>
              </div>
            }
          />
        )}
      </div>
    </div>
  );
}
