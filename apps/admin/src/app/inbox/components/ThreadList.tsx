'use client';

import { formatDistanceToNow } from 'date-fns';
import { Star, Paperclip } from 'lucide-react';
import { CHANNEL_CONFIG } from '../constants';
import type {
  ChannelType,
  BaseThread,
  SMSThread,
  SocialThread,
  EmailThread,
} from '../types';

type AnyThread = SMSThread | SocialThread | EmailThread;

interface ThreadListProps {
  threads: AnyThread[];
  selectedThreadId: string | null;
  selectedIds: Set<string>;
  onThreadSelect: (thread: AnyThread) => void;
  onToggleSelect: (threadId: string) => void;
  onSelectAll: () => void;
  showCheckboxes?: boolean;
  isLoading?: boolean;
}

/**
 * ThreadList - Displays list of message threads
 *
 * Features:
 * - Channel-specific icons and colors
 * - Unread/starred indicators
 * - Bulk selection checkboxes
 * - Relative timestamps
 * - Attachment indicators
 */
export function ThreadList({
  threads,
  selectedThreadId,
  selectedIds,
  onThreadSelect,
  onToggleSelect,
  onSelectAll,
  showCheckboxes = false,
  isLoading = false,
}: ThreadListProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (threads.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium">No messages</p>
          <p className="text-sm">All caught up! 🎉</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Select all header (when checkboxes visible) */}
      {showCheckboxes && threads.length > 0 && (
        <div className="sticky top-0 z-10 flex items-center gap-3 px-4 py-2 bg-gray-50 border-b border-gray-200">
          <input
            type="checkbox"
            checked={selectedIds.size === threads.length && threads.length > 0}
            onChange={onSelectAll}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          <span className="text-sm text-gray-600">
            {selectedIds.size > 0
              ? `${selectedIds.size} selected`
              : 'Select all'}
          </span>
        </div>
      )}

      {/* Thread items */}
      <ul className="divide-y divide-gray-200">
        {threads.map(thread => (
          <ThreadItem
            key={thread.id}
            thread={thread}
            isSelected={selectedThreadId === thread.id}
            isChecked={selectedIds.has(thread.id)}
            showCheckbox={showCheckboxes}
            onSelect={() => onThreadSelect(thread)}
            onToggleCheck={() => onToggleSelect(thread.id)}
          />
        ))}
      </ul>
    </div>
  );
}

interface ThreadItemProps {
  thread: AnyThread;
  isSelected: boolean;
  isChecked: boolean;
  showCheckbox: boolean;
  onSelect: () => void;
  onToggleCheck: () => void;
}

function ThreadItem({
  thread,
  isSelected,
  isChecked,
  showCheckbox,
  onSelect,
  onToggleCheck,
}: ThreadItemProps) {
  const config = CHANNEL_CONFIG[thread.channel as Exclude<ChannelType, 'all'>];
  const Icon = config?.icon;
  // Handle different unread properties: SMSThread/SocialThread use 'unread', EmailThread uses 'is_read' (inverted)
  const isUnread: boolean =
    'unread' in thread
      ? Boolean(thread.unread)
      : 'is_read' in thread
        ? !thread.is_read
        : false;
  const isStarred: boolean = 'starred' in thread && Boolean(thread.starred);
  const hasAttachments: boolean =
    'hasAttachments' in thread && Boolean(thread.hasAttachments);

  // Get display name based on thread type
  const displayName = getDisplayName(thread);
  const preview = getPreview(thread);
  // Handle different timestamp properties: BaseThread (SMS/Social) uses 'timestamp', EmailThread uses 'last_message_at'
  const messageTimestamp: string =
    'timestamp' in thread
      ? (thread.timestamp as string)
      : 'last_message_at' in thread
        ? (thread.last_message_at as string)
        : new Date().toISOString();
  const timestamp = formatDistanceToNow(new Date(messageTimestamp), {
    addSuffix: true,
  });

  return (
    <li
      className={`
        relative cursor-pointer transition-colors
        ${
          isSelected
            ? 'bg-indigo-50 border-l-4 border-l-indigo-600'
            : isUnread
              ? 'bg-blue-50/50 hover:bg-gray-50'
              : 'bg-white hover:bg-gray-50'
        }
      `}
    >
      <div
        className="flex items-start gap-3 px-4 py-3"
        onClick={onSelect}
        role="button"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && onSelect()}
      >
        {/* Checkbox (for bulk selection) */}
        {showCheckbox && (
          <div
            className="pt-1"
            onClick={e => {
              e.stopPropagation();
              onToggleCheck();
            }}
          >
            <input
              type="checkbox"
              checked={isChecked}
              onChange={() => {}}
              className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
          </div>
        )}

        {/* Channel icon */}
        <div
          className={`
            flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
            ${config?.bg || 'bg-gray-100'}
          `}
        >
          {Icon && <Icon className="h-5 w-5 text-white" />}
        </div>

        {/* Thread content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            {/* Sender name */}
            <span
              className={`
                text-sm truncate
                ${
                  isUnread
                    ? 'font-semibold text-gray-900'
                    : 'font-medium text-gray-700'
                }
              `}
            >
              {displayName}
            </span>

            {/* Timestamp */}
            <span className="flex-shrink-0 text-xs text-gray-500">
              {timestamp}
            </span>
          </div>

          {/* Subject line (for email) */}
          {'subject' in thread && thread.subject && (
            <p
              className={`
                text-sm truncate mt-0.5
                ${isUnread ? 'font-medium text-gray-900' : 'text-gray-600'}
              `}
            >
              {thread.subject}
            </p>
          )}

          {/* Message preview */}
          <p className="text-sm text-gray-500 truncate mt-0.5">{preview}</p>

          {/* Tags row */}
          <div className="flex items-center gap-2 mt-1">
            {/* Starred indicator */}
            {isStarred && (
              <Star className="h-3.5 w-3.5 text-yellow-400 fill-yellow-400" />
            )}

            {/* Attachment indicator */}
            {hasAttachments && (
              <Paperclip className="h-3.5 w-3.5 text-gray-400" />
            )}

            {/* Labels */}
            {'labels' in thread &&
              thread.labels &&
              thread.labels.length > 0 && (
                <div className="flex gap-1">
                  {thread.labels.slice(0, 2).map(label => (
                    <span
                      key={label.id}
                      className="px-1.5 py-0.5 text-xs rounded-full"
                      style={{
                        backgroundColor: label.color + '20',
                        color: label.color,
                      }}
                    >
                      {label.name}
                    </span>
                  ))}
                  {thread.labels.length > 2 && (
                    <span className="text-xs text-gray-400">
                      +{thread.labels.length - 2}
                    </span>
                  )}
                </div>
              )}
          </div>
        </div>

        {/* Unread indicator dot */}
        {isUnread && !showCheckbox && (
          <div className="absolute left-1.5 top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-600 rounded-full" />
        )}
      </div>
    </li>
  );
}

// Helper functions
function getDisplayName(thread: AnyThread): string {
  // BaseThread (SMS/Social) uses customer_name
  if ('customer_name' in thread && thread.customer_name) {
    return thread.customer_name as string;
  }
  // EmailThread uses first_message_from
  if ('first_message_from' in thread && thread.first_message_from) {
    return thread.first_message_from as string;
  }
  // Fallback to email address if available
  if (
    'first_message_from_address' in thread &&
    thread.first_message_from_address
  ) {
    return thread.first_message_from_address as string;
  }
  return 'Unknown';
}

function getPreview(thread: AnyThread): string {
  if (!thread.messages || thread.messages.length === 0) return '';
  const lastMessage = thread.messages[thread.messages.length - 1];

  // Handle different message content properties by channel type
  if ('html_body' in lastMessage && lastMessage.html_body) {
    // EmailMessage - strip HTML and return preview
    return (lastMessage.html_body as string)
      .replace(/<[^>]*>/g, '')
      .slice(0, 100);
  }
  if ('text_body' in lastMessage && lastMessage.text_body) {
    // EmailMessage text fallback
    return (lastMessage.text_body as string).slice(0, 100);
  }
  if ('body' in lastMessage && lastMessage.body) {
    // SMSMessage
    return (lastMessage.body as string).slice(0, 100);
  }
  if ('content' in lastMessage && lastMessage.content) {
    // SocialMessage
    return (lastMessage.content as string).slice(0, 100);
  }

  return '';
}

export default ThreadList;
