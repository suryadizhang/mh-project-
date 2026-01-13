'use client';

import {
  Mail,
  Inbox,
  Star,
  Send,
  Archive,
  Trash2,
  Search,
  RefreshCw,
  X,
  FileText,
  Save,
  Reply,
  ReplyAll,
  Forward,
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/contexts/AuthContext';
import { RichTextEditor } from '@/components/ui/RichTextEditor';
import DeleteConfirmationModal from '@/components/DeleteConfirmationModal';
import {
  getEmailStats,
  getCustomerSupportEmails,
  getPaymentEmails,
  sendCustomerSupportEmail,
  updateCustomerSupportEmail,
  bulkUpdateCustomerSupportEmails,
  deleteCustomerSupportEmail,
  deletePaymentEmail,
  formatRelativeTime,
  getEmailPreview,
  getInitials,
  type EmailThread,
  type EmailStats as EmailStatsType,
  type SendEmailRequest,
} from '@/services/emailApi';

// Tab types
type InboxTab = 'customer_support' | 'payments';

// Email signature
const EMAIL_SIGNATURE = `\n\n---\nBest regards,\nMy Hibachi Chef Team\n\n📧 cs@myhibachichef.com\n📞 (916) 740-8768\n🌐 www.myhibachichef.com`;

// Quick reply templates
const REPLY_TEMPLATES = [
  {
    id: 'thank_you',
    name: 'Thank You',
    text: `Thank you for contacting My Hibachi Chef!\n\nWe've received your inquiry and our team will get back to you within 24 hours.`,
  },
  {
    id: 'booking_confirmed',
    name: 'Booking Confirmed',
    text: `Great news! Your hibachi experience is confirmed.\n\nEvent Date: {event_date}\nChef: {chef_name}\nGuests: {guest_count}\n\nWe look forward to serving you!`,
  },
  {
    id: 'apology',
    name: 'Apology',
    text: `We sincerely apologize for the inconvenience you've experienced.\n\nYour satisfaction is our top priority, and we're committed to making this right. Please let us know how we can help resolve this issue.`,
  },
  {
    id: 'refund_processed',
    name: 'Refund Processed',
    text: `Your refund has been processed successfully.\n\nAmount: {refund_amount}\nMethod: {payment_method}\n\nYou should see the funds in your account within 5-7 business days.`,
  },
  {
    id: 'more_info',
    name: 'Need More Info',
    text: `Thank you for reaching out!\n\nTo better assist you, could you please provide the following information:\n\n- Event date and time\n- Number of guests\n- Location (address)\n- Any dietary restrictions\n\nOnce we have these details, we'll send you a custom quote.`,
  },
];

export default function EmailsPage() {
  const toast = useToast();
  const { isSuperAdmin } = useAuth();

  // State
  const [activeTab, setActiveTab] = useState<InboxTab>('customer_support');
  const [stats, setStats] = useState<{
    customer_support: EmailStatsType;
    payments: EmailStatsType;
  } | null>(null);
  const [threads, setThreads] = useState<EmailThread[]>([]);
  const [selectedThread, setSelectedThread] = useState<EmailThread | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [replyText, setReplyText] = useState('');
  const [draftSaved, setDraftSaved] = useState<Date | null>(null);
  const [showTemplateMenu, setShowTemplateMenu] = useState(false);
  const [showReplyBox, setShowReplyBox] = useState(false);

  // Filters
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [showStarredOnly, setShowStarredOnly] = useState(false);

  // Bulk selection
  const [selectedEmails, setSelectedEmails] = useState<Set<string>>(new Set());
  const [bulkProcessing, setBulkProcessing] = useState(false);

  // Delete confirmation modal
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [pendingDeleteIds, setPendingDeleteIds] = useState<string[]>([]);

  // Load email stats
  const loadStats = async () => {
    try {
      const statsData = await getEmailStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load email stats:', error);
    }
  };

  // Load threads for active tab
  const loadThreads = async () => {
    setLoading(true);
    try {
      let response;
      if (activeTab === 'customer_support') {
        response = await getCustomerSupportEmails({
          page: 1,
          limit: 100,
          unread_only: showUnreadOnly,
          starred_only: showStarredOnly,
          search: searchQuery || undefined,
        });
      } else {
        response = await getPaymentEmails({
          page: 1,
          limit: 100,
          unread_only: showUnreadOnly,
          search: searchQuery || undefined,
        });
      }
      setThreads(response.threads);
    } catch (error) {
      console.error('Failed to load threads:', error);
      toast.error('Failed to load emails', 'Please try again');
    } finally {
      setLoading(false);
    }
  };

  // Load data on mount and when filters change
  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    loadThreads();
    setSelectedThread(null); // Clear selection when changing tabs/filters
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, showUnreadOnly, showStarredOnly, searchQuery]);

  // Draft saving: Restore draft when thread is selected
  useEffect(() => {
    if (selectedThread && activeTab === 'customer_support') {
      const draftKey = `email-draft-${selectedThread.thread_id}`;
      const savedDraft = localStorage.getItem(draftKey);
      if (savedDraft) {
        setReplyText(savedDraft);
        toast.info('Draft restored', 'Your previous reply was restored');
      } else {
        setReplyText('');
      }
    }
  }, [selectedThread, activeTab, toast]);

  // Draft saving: Auto-save draft every 3 seconds
  useEffect(() => {
    if (!replyText || !selectedThread || activeTab !== 'customer_support') {
      return;
    }

    const timeoutId = setTimeout(() => {
      const draftKey = `email-draft-${selectedThread.thread_id}`;
      localStorage.setItem(draftKey, replyText);
      setDraftSaved(new Date());
    }, 3000); // 3 second debounce

    return () => clearTimeout(timeoutId);
  }, [replyText, selectedThread, activeTab]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input fields
      if (
        (e.target as HTMLElement).tagName === 'TEXTAREA' ||
        (e.target as HTMLElement).tagName === 'INPUT'
      ) {
        // Allow Esc to close/unfocus
        if (e.key === 'Escape') {
          (e.target as HTMLElement).blur();
        }
        return;
      }

      // j/k navigation
      if (e.key === 'j' || e.key === 'k') {
        e.preventDefault();
        const currentIndex = threads.findIndex(
          t => t.thread_id === selectedThread?.thread_id
        );
        if (e.key === 'j' && currentIndex < threads.length - 1) {
          handleThreadClick(threads[currentIndex + 1]);
        } else if (e.key === 'k' && currentIndex > 0) {
          handleThreadClick(threads[currentIndex - 1]);
        }
      }

      // r - Reply (focus is handled by rich text editor)
      if (e.key === 'r' && selectedThread && activeTab === 'customer_support') {
        e.preventDefault();
        // Rich text editor auto-focuses when reply section is visible
      }

      // e - Archive
      if (e.key === 'e' && selectedThread && activeTab === 'customer_support') {
        e.preventDefault();
        handleArchive(selectedThread);
      }

      // s - Star
      if (e.key === 's' && selectedThread && activeTab === 'customer_support') {
        e.preventDefault();
        handleStarToggle(selectedThread);
      }

      // u - Mark as unread
      if (e.key === 'u' && selectedThread && activeTab === 'customer_support') {
        e.preventDefault();
        handleMarkAsUnread(selectedThread);
      }

      // / - Focus search
      if (e.key === '/') {
        e.preventDefault();
        document.querySelector<HTMLInputElement>('input[type="text"]')?.focus();
      }

      // Ctrl+A or Cmd+A - Select all (when not in input field)
      if (
        (e.ctrlKey || e.metaKey) &&
        e.key === 'a' &&
        activeTab === 'customer_support'
      ) {
        const target = e.target as HTMLElement;
        if (
          target.tagName !== 'INPUT' &&
          target.tagName !== 'TEXTAREA' &&
          !target.isContentEditable
        ) {
          e.preventDefault();
          handleSelectAll();
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threads, selectedThread, activeTab]);

  // Handle thread selection
  const handleThreadClick = async (thread: EmailThread) => {
    setSelectedThread(thread);

    // Mark as read if unread
    if (!thread.is_read && activeTab === 'customer_support') {
      try {
        // Mark first message as read
        const firstMessage = thread.messages[0];
        if (firstMessage) {
          await updateCustomerSupportEmail(firstMessage.message_id, {
            is_read: true,
          });
          // Reload threads to reflect updated status
          loadThreads();
          loadStats();
        }
      } catch (error) {
        console.error('Failed to mark as read:', error);
      }
    }
  };

  // Handle send reply
  const handleSendReply = async () => {
    if (!selectedThread || !replyText.trim()) return;

    setSending(true);
    try {
      const firstMessage = selectedThread.messages[0];
      const toEmail = firstMessage.from_address;
      const toName = firstMessage.from_name;

      // Append signature
      const emailBody = replyText + EMAIL_SIGNATURE;

      const request: SendEmailRequest = {
        to: [{ email: toEmail, name: toName }],
        subject: `Re: ${selectedThread.subject}`,
        text_body: emailBody,
        in_reply_to: firstMessage.message_id,
        thread_id: selectedThread.thread_id,
      };

      await sendCustomerSupportEmail(request);

      toast.success('Email sent!', `Reply sent to ${toEmail}`);

      // Clear draft from localStorage
      const draftKey = `email-draft-${selectedThread.thread_id}`;
      localStorage.removeItem(draftKey);

      setReplyText('');
      setDraftSaved(null);
      loadThreads();
      loadStats();
    } catch (error) {
      console.error('Failed to send reply:', error);
      toast.error('Failed to send email', 'Please try again');
    } finally {
      setSending(false);
    }
  };

  // Insert template into reply text
  const insertTemplate = (template: (typeof REPLY_TEMPLATES)[0]) => {
    const currentContent = replyText || '';
    const newContent = currentContent
      ? `${currentContent}<br/><br/>${template.text}`
      : template.text;
    setReplyText(newContent);
    setShowTemplateMenu(false);
  };

  // Handle mark as unread
  const handleMarkAsUnread = async (thread: EmailThread) => {
    if (activeTab !== 'customer_support') return;

    try {
      const firstMessage = thread.messages[0];
      if (firstMessage) {
        await updateCustomerSupportEmail(firstMessage.message_id, {
          is_read: false,
        });
        loadThreads();
        loadStats();
      }
    } catch (error) {
      console.error('Failed to mark as unread:', error);
    }
  };

  // Handle star toggle
  const handleStarToggle = async (thread: EmailThread) => {
    if (activeTab !== 'customer_support') return;

    try {
      const firstMessage = thread.messages[0];
      if (firstMessage) {
        await updateCustomerSupportEmail(firstMessage.message_id, {
          is_starred: !thread.is_starred,
        });
        loadThreads();
        loadStats();
      }
    } catch (error) {
      console.error('Failed to toggle star:', error);
    }
  };

  // Handle archive
  const handleArchive = async (thread: EmailThread) => {
    if (activeTab !== 'customer_support') return;

    try {
      const firstMessage = thread.messages[0];
      if (firstMessage) {
        await updateCustomerSupportEmail(firstMessage.message_id, {
          is_archived: true,
        });
        toast.success('Archived', 'Email moved to archive');
        loadThreads();
        loadStats();
        setSelectedThread(null);
      }
    } catch (error) {
      console.error('Failed to archive:', error);
    }
  };

  const handleDelete = async (thread: EmailThread) => {
    // Only super admins can delete emails
    if (!isSuperAdmin()) {
      toast.error('Permission Denied', 'Only super admins can delete emails');
      return;
    }

    // Confirm deletion
    if (
      !confirm(
        'Are you sure you want to permanently delete this email? This action cannot be undone.'
      )
    ) {
      return;
    }

    try {
      const firstMessage = thread.messages[0];
      if (firstMessage) {
        // Use correct delete function based on active tab
        if (activeTab === 'customer_support') {
          await deleteCustomerSupportEmail(firstMessage.message_id);
        } else {
          await deletePaymentEmail(firstMessage.message_id);
        }
        toast.success('Deleted', 'Email permanently deleted');
        loadThreads();
        loadStats();
        setSelectedThread(null);
      }
    } catch (error) {
      console.error('Failed to delete:', error);
      toast.error('Delete Failed', 'Could not delete email');
    }
  };

  // Bulk operations
  const handleSelectAll = () => {
    if (selectedEmails.size === threads.length) {
      // Deselect all
      setSelectedEmails(new Set());
    } else {
      // Select all visible threads
      const allThreadIds = threads.map(t => t.thread_id);
      setSelectedEmails(new Set(allThreadIds));
    }
  };

  const handleSelectEmail = (threadId: string) => {
    const newSelection = new Set(selectedEmails);
    if (newSelection.has(threadId)) {
      newSelection.delete(threadId);
    } else {
      newSelection.add(threadId);
    }
    setSelectedEmails(newSelection);
  };

  // Execute the actual bulk delete after modal confirmation
  const executeBulkDelete = useCallback(async (reason: string) => {
    if (pendingDeleteIds.length === 0) return;

    setBulkProcessing(true);
    try {
      const result = await bulkUpdateCustomerSupportEmails(pendingDeleteIds, 'delete');

      if (result.success_count > 0) {
        toast.success(
          'Emails deleted',
          `${result.success_count} email(s) permanently deleted. Reason: "${reason.substring(0, 50)}${reason.length > 50 ? '...' : ''}"`
        );
        // Log to console for audit trail (backend already logs this)
        console.info(`[AUDIT] Bulk email delete by super admin. Count: ${result.success_count}. Reason: ${reason}`);
      }

      if (result.failed_count > 0) {
        toast.error(
          'Some deletions failed',
          `${result.failed_count} email(s) could not be deleted`
        );
      }

      // Clear selection and refresh
      setSelectedEmails(new Set());
      setPendingDeleteIds([]);
      loadThreads();
      loadStats();
      setSelectedThread(null);
    } catch (error) {
      console.error('Bulk delete failed:', error);
      toast.error('Delete failed', 'Could not complete bulk delete operation');
    } finally {
      setBulkProcessing(false);
      setShowDeleteModal(false);
    }
  }, [pendingDeleteIds, toast]);

  const handleBulkAction = async (
    action:
      | 'mark_read'
      | 'mark_unread'
      | 'star'
      | 'unstar'
      | 'archive'
      | 'unarchive'
      | 'delete'
  ) => {
    if (selectedEmails.size === 0) {
      toast.error(
        'No emails selected',
        'Please select emails to perform bulk actions'
      );
      return;
    }

    if (activeTab !== 'customer_support') {
      toast.error(
        'Not supported',
        'Bulk actions only available for customer support emails'
      );
      return;
    }

    // Get message IDs from selected threads
    const messageIds = threads
      .filter(t => selectedEmails.has(t.thread_id))
      .map(t => t.messages[0]?.message_id)
      .filter(Boolean) as string[];

    // Handle delete action with modal confirmation
    if (action === 'delete') {
      if (!isSuperAdmin()) {
        toast.error('Permission Denied', 'Only super admins can delete emails');
        return;
      }
      // Store the IDs and show the modal
      setPendingDeleteIds(messageIds);
      setShowDeleteModal(true);
      return;
    }

    // For non-delete actions, proceed immediately
    setBulkProcessing(true);
    try {
      const result = await bulkUpdateCustomerSupportEmails(messageIds, action);

      if (result.success_count > 0) {
        const actionText = action.replace('_', ' ');
        toast.success(
          'Bulk action completed',
          `${result.success_count} email(s) updated successfully`
        );
      }

      if (result.failed_count > 0) {
        toast.error(
          'Some actions failed',
          `${result.failed_count} email(s) could not be updated`
        );
      }

      // Clear selection and refresh
      setSelectedEmails(new Set());
      loadThreads();
      loadStats();
      setSelectedThread(null);
    } catch (error) {
      console.error('Bulk action failed:', error);
      toast.error('Bulk action failed', 'Could not complete bulk operation');
    } finally {
      setBulkProcessing(false);
    }
  };

  const clearSelection = () => {
    setSelectedEmails(new Set());
  };

  // Get current inbox stats
  const currentStats =
    activeTab === 'customer_support'
      ? stats?.customer_support
      : stats?.payments;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Mail className="w-7 h-7 text-red-600" />
              Email Management
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Manage customer support and payment emails
            </p>
          </div>
          <Button onClick={loadThreads} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6">
          <div className="flex space-x-1">
            {/* Customer Support Tab */}
            <button
              onClick={() => setActiveTab('customer_support')}
              className={`px-6 py-3 text-sm font-medium transition-colors relative ${activeTab === 'customer_support'
                  ? 'text-red-600 border-b-2 border-red-600'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              <div className="flex items-center gap-2">
                <Inbox className="w-4 h-4" />
                Customer Support
                {stats?.customer_support?.unread_emails !== undefined &&
                  stats.customer_support.unread_emails > 0 && (
                    <span className="bg-red-600 text-white text-xs px-2 py-0.5 rounded-full">
                      {stats.customer_support.unread_emails}
                    </span>
                  )}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                cs@myhibachichef.com
              </div>
            </button>

            {/* Payments Tab */}
            <button
              onClick={() => setActiveTab('payments')}
              className={`px-6 py-3 text-sm font-medium transition-colors relative ${activeTab === 'payments'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                Payment Monitoring
                {stats?.payments?.unread_emails !== undefined &&
                  stats.payments.unread_emails > 0 && (
                    <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                      {stats.payments.unread_emails}
                    </span>
                  )}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                myhibachichef@gmail.com (Read Only)
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      {currentStats && (
        <div className="bg-white border-b border-gray-200 px-6 py-3">
          <div className="flex items-center gap-6 text-sm text-gray-600">
            <div>
              <span className="font-medium">{currentStats.total_emails}</span>{' '}
              total
            </div>
            <div>
              <span className="font-medium text-red-600">
                {currentStats.unread_emails}
              </span>{' '}
              unread
            </div>
            <div>
              <span className="font-medium text-yellow-600">
                {currentStats.starred_emails}
              </span>{' '}
              starred
            </div>
            <div>
              <span className="font-medium">{currentStats.today_count}</span>{' '}
              today
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Thread List Sidebar */}
        <div className="w-96 bg-white border-r border-gray-200 flex flex-col">
          {/* Search & Filters */}
          <div className="p-4 border-b border-gray-200 space-y-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search emails..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent text-sm"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Filters */}
            <div className="flex gap-2">
              <button
                onClick={() => setShowUnreadOnly(!showUnreadOnly)}
                className={`px-3 py-1.5 text-xs rounded-full transition-colors ${showUnreadOnly
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
              >
                Unread Only
              </button>
              {activeTab === 'customer_support' && (
                <button
                  onClick={() => setShowStarredOnly(!showStarredOnly)}
                  className={`px-3 py-1.5 text-xs rounded-full transition-colors ${showStarredOnly
                      ? 'bg-yellow-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                  Starred Only
                </button>
              )}
            </div>
          </div>

          {/* Thread List */}
          <div className="flex-1 overflow-y-auto">
            {/* Bulk Actions Toolbar */}
            {activeTab === 'customer_support' && selectedEmails.size > 0 && (
              <div className="sticky top-0 z-10 bg-blue-50 border-b border-blue-200 p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-blue-900">
                    {selectedEmails.size} selected
                  </span>
                  <button
                    onClick={clearSelection}
                    className="text-sm text-blue-700 hover:text-blue-900 underline"
                  >
                    Clear selection
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => handleBulkAction('mark_read')}
                    disabled={bulkProcessing}
                    size="sm"
                    variant="secondary"
                  >
                    Mark Read
                  </Button>
                  <Button
                    onClick={() => handleBulkAction('mark_unread')}
                    disabled={bulkProcessing}
                    size="sm"
                    variant="secondary"
                  >
                    Mark Unread
                  </Button>
                  <Button
                    onClick={() => handleBulkAction('star')}
                    disabled={bulkProcessing}
                    size="sm"
                    variant="secondary"
                  >
                    <Star className="w-4 h-4 mr-1" />
                    Star
                  </Button>
                  <Button
                    onClick={() => handleBulkAction('unstar')}
                    disabled={bulkProcessing}
                    size="sm"
                    variant="secondary"
                  >
                    <Star className="w-4 h-4 mr-1" />
                    Unstar
                  </Button>
                  <Button
                    onClick={() => handleBulkAction('archive')}
                    disabled={bulkProcessing}
                    size="sm"
                    variant="secondary"
                  >
                    <Archive className="w-4 h-4 mr-1" />
                    Archive
                  </Button>
                  {isSuperAdmin() && (
                    <Button
                      onClick={() => handleBulkAction('delete')}
                      disabled={bulkProcessing}
                      size="sm"
                      variant="destructive"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Delete
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Select All Checkbox */}
            {activeTab === 'customer_support' &&
              threads.length > 0 &&
              !loading && (
                <div className="sticky top-0 z-10 bg-white border-b border-gray-200 p-3 flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={
                      selectedEmails.size === threads.length &&
                      threads.length > 0
                    }
                    onChange={handleSelectAll}
                    className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                  />
                  <span className="text-sm text-gray-600">
                    {selectedEmails.size === threads.length &&
                      threads.length > 0
                      ? 'Deselect all'
                      : 'Select all'}
                  </span>
                </div>
              )}

            {loading ? (
              <div className="p-8">
                <LoadingSpinner message="Loading emails..." />
              </div>
            ) : threads.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Inbox className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">No emails found</p>
                <p className="text-sm mt-1">
                  {searchQuery || showUnreadOnly || showStarredOnly
                    ? 'Try adjusting your filters'
                    : 'Your inbox is empty'}
                </p>
              </div>
            ) : (
              threads.map(thread => {
                const isSelected =
                  selectedThread?.thread_id === thread.thread_id;
                const isChecked = selectedEmails.has(thread.thread_id);
                const firstMessage = thread.messages[0];

                return (
                  <div
                    key={thread.thread_id}
                    className={`p-4 border-b border-gray-200 transition-colors ${isSelected
                        ? 'bg-red-50 border-l-4 border-l-red-600'
                        : thread.is_read
                          ? 'hover:bg-gray-50'
                          : 'bg-blue-50 bg-opacity-30 hover:bg-blue-50 hover:bg-opacity-50'
                      }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Checkbox (Customer Support only) */}
                      {activeTab === 'customer_support' && (
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={e => {
                            e.stopPropagation();
                            handleSelectEmail(thread.thread_id);
                          }}
                          onClick={e => e.stopPropagation()}
                          className="mt-1 w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500 flex-shrink-0"
                        />
                      )}

                      {/* Thread Content (clickable) */}
                      <div
                        onClick={() => handleThreadClick(thread)}
                        className="flex-1 min-w-0 cursor-pointer"
                      >
                        {/* Header */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            {/* Avatar */}
                            <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                              {getInitials(
                                firstMessage?.from_name,
                                firstMessage?.from_address
                              )}
                            </div>

                            {/* Sender */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`font-medium truncate ${thread.is_read ? 'text-gray-700' : 'text-gray-900'}`}
                                >
                                  {firstMessage?.from_name ||
                                    firstMessage?.from_address ||
                                    'Unknown'}
                                </span>
                                {!thread.is_read && (
                                  <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0" />
                                )}
                              </div>
                              <div className="text-xs text-gray-500 truncate">
                                {firstMessage?.from_address}
                              </div>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-1 ml-2">
                            {activeTab === 'customer_support' && (
                              <button
                                onClick={e => {
                                  e.stopPropagation();
                                  handleStarToggle(thread);
                                }}
                                className="p-1 hover:bg-gray-200 rounded"
                              >
                                <Star
                                  className={`w-4 h-4 ${thread.is_starred ? 'fill-yellow-500 text-yellow-500' : 'text-gray-400'}`}
                                />
                              </button>
                            )}
                            <span className="text-xs text-gray-500">
                              {formatRelativeTime(thread.last_message_at)}
                            </span>
                          </div>
                        </div>

                        {/* Subject */}
                        <div
                          className={`text-sm mb-1 truncate ${thread.is_read ? 'font-normal text-gray-700' : 'font-semibold text-gray-900'}`}
                        >
                          {thread.subject || '(No subject)'}
                        </div>

                        {/* Preview */}
                        <div className="text-sm text-gray-600 line-clamp-2">
                          {getEmailPreview(firstMessage)}
                        </div>

                        {/* Metadata */}
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                          {thread.message_count > 1 && (
                            <span>{thread.message_count} messages</span>
                          )}
                          {thread.has_attachments && (
                            <span className="flex items-center gap-1">
                              📎 Attachment
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Email View (Right Side) */}
        <div className="flex-1 flex flex-col bg-white">
          {selectedThread ? (
            <>
              {/* Thread Header */}
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">
                      {selectedThread.subject || '(No subject)'}
                    </h2>
                    <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
                      <span>
                        {selectedThread.message_count}{' '}
                        {selectedThread.message_count === 1
                          ? 'message'
                          : 'messages'}
                      </span>
                      <span>•</span>
                      <span>
                        {selectedThread.participants.length} participant
                        {selectedThread.participants.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  {activeTab === 'customer_support' && (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleArchive(selectedThread)}
                      >
                        <Archive className="w-4 h-4 mr-1" />
                        Archive
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStarToggle(selectedThread)}
                      >
                        <Star
                          className={`w-4 h-4 mr-1 ${selectedThread.is_starred ? 'fill-yellow-500 text-yellow-500' : ''}`}
                        />
                        {selectedThread.is_starred ? 'Unstar' : 'Star'}
                      </Button>
                      {isSuperAdmin() && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDelete(selectedThread)}
                          className="text-red-600 hover:bg-red-50 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete
                        </Button>
                      )}
                    </div>
                  )}
                  {/* Actions for payments tab */}
                  {activeTab === 'payments' && isSuperAdmin() && (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDelete(selectedThread)}
                        className="text-red-600 hover:bg-red-50 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  )}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {selectedThread.messages.map((message, idx) => (
                  <div
                    key={message.message_id}
                    className="bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                  >
                    <div className="p-4 space-y-3">
                      {/* Message Header */}
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                          {getInitials(message.from_name, message.from_address)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-baseline gap-2">
                            <span className="font-medium text-gray-900">
                              {message.from_name || message.from_address}
                            </span>
                            <span className="text-xs text-gray-500">
                              {formatRelativeTime(message.received_at)}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600">
                            {message.from_address}
                          </div>
                          {/* To: line (Gmail-style) */}
                          <div className="text-xs text-gray-500 mt-1">
                            to me
                          </div>
                        </div>
                      </div>

                      {/* Message Body */}
                      <div className="prose prose-sm max-w-none">
                        <div
                          dangerouslySetInnerHTML={{
                            __html:
                              message.html_body ||
                              `<p>${message.text_body || '(No content)'}</p>`,
                          }}
                        />
                      </div>

                      {/* Attachments */}
                      {message.has_attachments &&
                        message.attachments &&
                        message.attachments.length > 0 && (
                          <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
                            {message.attachments.map((attachment, i) => (
                              <div
                                key={i}
                                className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-sm"
                              >
                                <span>📎</span>
                                <span className="font-medium">
                                  {attachment.filename}
                                </span>
                                <span className="text-gray-500">
                                  ({(attachment.size_bytes / 1024).toFixed(1)}{' '}
                                  KB)
                                </span>
                              </div>
                            ))}
                          </div>
                        )}

                      {/* Reply/Forward Actions (Gmail-style) - Only on last message */}
                      {activeTab === 'customer_support' &&
                        idx === selectedThread.messages.length - 1 && (
                          <div className="flex items-center gap-1 pt-2 border-t border-gray-100">
                            <Button
                              onClick={() => setShowReplyBox(!showReplyBox)}
                              variant="ghost"
                              size="sm"
                              className="text-gray-600 hover:bg-gray-100"
                              type="button"
                            >
                              <Reply className="w-4 h-4 mr-1" />
                              Reply
                            </Button>
                            <Button
                              onClick={() => setShowReplyBox(!showReplyBox)}
                              variant="ghost"
                              size="sm"
                              className="text-gray-600 hover:bg-gray-100"
                              type="button"
                            >
                              <ReplyAll className="w-4 h-4 mr-1" />
                              Reply All
                            </Button>
                            <Button
                              onClick={() => setShowReplyBox(!showReplyBox)}
                              variant="ghost"
                              size="sm"
                              className="text-gray-600 hover:bg-gray-100"
                              type="button"
                            >
                              <Forward className="w-4 h-4 mr-1" />
                              Forward
                            </Button>
                          </div>
                        )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Reply Box (Customer Support Only - Collapsible) */}
              {activeTab === 'customer_support' && showReplyBox && (
                <div className="border-t border-gray-200 p-6 bg-gray-50 animate-in slide-in-from-bottom duration-300">
                  <div className="bg-white rounded-lg border border-gray-300 shadow-sm">
                    {/* Reply Header (Gmail-style) */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
                      <div className="flex items-center gap-2">
                        <Reply className="w-4 h-4 text-gray-500" />
                        <span className="text-sm font-medium text-gray-700">
                          Reply to{' '}
                          {selectedThread.messages[0]?.from_name || 'Customer'}
                        </span>
                      </div>
                      <Button
                        onClick={() => setShowReplyBox(false)}
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-gray-600 -mr-2"
                        type="button"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>

                    <div className="p-4 space-y-3">
                      {/* Template Dropdown */}
                      <div className="relative">
                        <Button
                          onClick={() => setShowTemplateMenu(!showTemplateMenu)}
                          variant="outline"
                          size="sm"
                          type="button"
                        >
                          <FileText className="w-4 h-4 mr-2" />
                          Quick Templates
                        </Button>
                        {showTemplateMenu && (
                          <div className="absolute z-10 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg">
                            {REPLY_TEMPLATES.map(template => (
                              <button
                                key={template.id}
                                onClick={() => insertTemplate(template)}
                                className="w-full text-left px-4 py-2 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
                              >
                                <div className="font-medium text-sm text-gray-900">
                                  {template.name}
                                </div>
                                <div className="text-xs text-gray-500 line-clamp-1">
                                  {template.text.substring(0, 50)}...
                                </div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>

                      <RichTextEditor
                        content={replyText}
                        onChange={setReplyText}
                        placeholder="Type your reply... (Signature will be appended automatically)"
                      />
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-4">
                          <span className="text-xs text-gray-500">
                            Replying as cs@myhibachichef.com
                          </span>
                          {draftSaved && (
                            <span className="text-xs text-green-600 flex items-center gap-1">
                              <Save className="w-3 h-3" />
                              Draft saved{' '}
                              {formatRelativeTime(draftSaved.toISOString())}
                            </span>
                          )}
                        </div>
                        <Button
                          onClick={handleSendReply}
                          disabled={!replyText.trim() || sending}
                        >
                          <Send className="w-4 h-4 mr-2" />
                          {sending ? 'Sending...' : 'Send Reply'}
                        </Button>
                      </div>
                      <div className="text-xs text-gray-400">
                        💡 Keyboard shortcuts:{' '}
                        <kbd className="px-1 bg-gray-200 rounded">r</kbd> reply,{' '}
                        <kbd className="px-1 bg-gray-200 rounded">j/k</kbd>{' '}
                        navigate,{' '}
                        <kbd className="px-1 bg-gray-200 rounded">s</kbd> star,{' '}
                        <kbd className="px-1 bg-gray-200 rounded">e</kbd>{' '}
                        archive
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Read-Only Notice (Payments) */}
              {activeTab === 'payments' && (
                <div className="border-t border-gray-200 p-6 bg-yellow-50">
                  <div className="text-center text-sm text-gray-700">
                    <p className="font-medium">Read-Only Inbox</p>
                    <p className="mt-1">
                      This inbox is for manual payment verification only. Cannot
                      reply from this address.
                    </p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <Mail className="w-20 h-20 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">Select an email to view</p>
                <p className="text-sm text-gray-400 mt-2">
                  Choose a conversation from the list to read and reply
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal - Enterprise-grade with audit trail */}
      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setPendingDeleteIds([]);
        }}
        onConfirm={executeBulkDelete}
        resourceType="email"
        resourceName={`${pendingDeleteIds.length} customer support email${pendingDeleteIds.length !== 1 ? 's' : ''}`}
        warningMessage="These emails will be PERMANENTLY DELETED from the database. This action cannot be undone. A security audit log will be created."
      />
    </div>
  );
}
