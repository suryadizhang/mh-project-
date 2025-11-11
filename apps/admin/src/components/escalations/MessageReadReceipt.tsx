'use client';

import { Check, CheckCheck, Clock, X } from 'lucide-react';

export type MessageStatus =
  | 'sending'
  | 'sent'
  | 'delivered'
  | 'read'
  | 'failed';

interface MessageReadReceiptProps {
  status: MessageStatus;
  timestamp?: string;
  readAt?: string;
  deliveredAt?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function MessageReadReceipt({
  status,
  timestamp,
  readAt,
  deliveredAt,
  showLabel = false,
  size = 'sm',
}: MessageReadReceiptProps) {
  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 12;
      case 'md':
        return 16;
      case 'lg':
        return 20;
    }
  };

  const getTextSize = () => {
    switch (size) {
      case 'sm':
        return 'text-xs';
      case 'md':
        return 'text-sm';
      case 'lg':
        return 'text-base';
    }
  };

  const formatTimestamp = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const getStatusIcon = () => {
    const iconSize = getIconSize();

    switch (status) {
      case 'sending':
        return (
          <Clock
            size={iconSize}
            className="text-gray-400 animate-pulse"
            aria-label="Sending"
          />
        );

      case 'sent':
        return (
          <Check
            size={iconSize}
            className="text-gray-400"
            aria-label="Sent"
          />
        );

      case 'delivered':
        return (
          <CheckCheck
            size={iconSize}
            className="text-gray-500"
            aria-label="Delivered"
          />
        );

      case 'read':
        return (
          <CheckCheck
            size={iconSize}
            className="text-blue-600"
            aria-label="Read"
          />
        );

      case 'failed':
        return (
          <X size={iconSize} className="text-red-600" aria-label="Failed" />
        );

      default:
        return null;
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case 'sending':
        return 'Sending...';
      case 'sent':
        return 'Sent';
      case 'delivered':
        return deliveredAt
          ? `Delivered ${formatTimestamp(deliveredAt)}`
          : 'Delivered';
      case 'read':
        return readAt ? `Read ${formatTimestamp(readAt)}` : 'Read';
      case 'failed':
        return 'Failed to send';
      default:
        return '';
    }
  };

  const getTooltipText = () => {
    const parts: string[] = [];

    if (timestamp) {
      parts.push(`Sent: ${new Date(timestamp).toLocaleString()}`);
    }

    if (deliveredAt) {
      parts.push(`Delivered: ${new Date(deliveredAt).toLocaleString()}`);
    }

    if (readAt) {
      parts.push(`Read: ${new Date(readAt).toLocaleString()}`);
    }

    if (status === 'failed') {
      parts.push('Message failed to send. Please try again.');
    }

    return parts.join('\n');
  };

  return (
    <div
      className={`flex items-center space-x-1 ${getTextSize()}`}
      title={getTooltipText()}
    >
      {getStatusIcon()}
      {showLabel && (
        <span
          className={`${
            status === 'failed'
              ? 'text-red-600'
              : status === 'read'
                ? 'text-blue-600'
                : 'text-gray-500'
          }`}
        >
          {getStatusLabel()}
        </span>
      )}
      {!showLabel && timestamp && (
        <span className="text-gray-500">{formatTimestamp(timestamp)}</span>
      )}
    </div>
  );
}

// Helper function to determine message status from message data
export function getMessageStatus(message: {
  timestamp: string;
  delivered_at?: string;
  read_at?: string;
  failed?: boolean;
  sending?: boolean;
}): MessageStatus {
  if (message.failed) return 'failed';
  if (message.sending) return 'sending';
  if (message.read_at) return 'read';
  if (message.delivered_at) return 'delivered';
  if (message.timestamp) return 'sent';
  return 'sending';
}
