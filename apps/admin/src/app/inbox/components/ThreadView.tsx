'use client';

import { format } from 'date-fns';
import {
  User,
  Phone,
  Mail,
  MapPin,
  Calendar,
  ExternalLink,
} from 'lucide-react';
import { CHANNEL_CONFIG } from '../constants';
import type {
  ChannelType,
  SMSThread,
  SocialThread,
  EmailThread,
  BaseMessage,
  SMSMessage,
  SocialMessage,
  EmailMessage,
} from '../types';

// Union type for all message types used in threads
type AnyMessage = SMSMessage | SocialMessage | EmailMessage;

type AnyThread = SMSThread | SocialThread | EmailThread;

interface ThreadViewProps {
  thread: AnyThread | null;
  onClose?: () => void;
}

/**
 * ThreadView - Displays the full conversation thread
 *
 * Features:
 * - Customer info header with contact details
 * - Message bubbles with sender/receiver distinction
 * - Timestamps on each message
 * - Channel-specific styling
 * - Scroll to bottom on new messages
 */
export function ThreadView({ thread, onClose }: ThreadViewProps) {
  if (!thread) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 bg-gray-50">
        <div className="text-center">
          <Mail className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-lg">Select a conversation</p>
          <p className="text-sm">
            Choose a thread from the list to view messages
          </p>
        </div>
      </div>
    );
  }

  const config = CHANNEL_CONFIG[thread.channel as Exclude<ChannelType, 'all'>];
  const Icon = config?.icon;

  return (
    <div className="flex-1 flex flex-col bg-white overflow-hidden">
      {/* Thread Header */}
      <div className="flex-shrink-0 border-b border-gray-200 p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* Channel badge */}
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center ${
                config?.bg || 'bg-gray-100'
              }`}
            >
              {Icon && <Icon className="h-5 w-5 text-white" />}
            </div>

            {/* Customer info */}
            <div>
              <h2 className="font-semibold text-gray-900">
                {getCustomerName(thread)}
              </h2>
              <div className="flex items-center gap-4 text-sm text-gray-500 mt-0.5">
                {getContactInfo(thread)}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {Boolean('bookingId' in thread && thread.bookingId) && (
              <a
                href={`/bookings/${
                  ('bookingId' in thread ? thread.bookingId : '') as string
                }`}
                className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800"
              >
                <ExternalLink className="h-4 w-4" />
                View Booking
              </a>
            )}
          </div>
        </div>

        {/* Subject line for email */}
        {'subject' in thread && (thread as { subject?: string }).subject && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="font-medium text-gray-900">
              {(thread as { subject?: string }).subject}
            </p>
          </div>
        )}
      </div>

      {/* Messages container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {thread.messages.map((message, index) => (
          <MessageBubble
            key={
              'id' in message
                ? message.id
                : (message as { message_id: string }).message_id
            }
            message={message}
            isOutbound={
              'isOutbound' in message
                ? Boolean(message.isOutbound)
                : 'direction' in message
                  ? message.direction === 'outbound'
                  : false
            }
            showTimestamp={shouldShowTimestamp(thread.messages, index)}
            channel={thread.channel}
          />
        ))}
      </div>

      {/* Customer Details Panel (collapsible) */}
      <CustomerDetailsPanel thread={thread} />
    </div>
  );
}

interface MessageBubbleProps {
  message: AnyMessage;
  isOutbound: boolean;
  showTimestamp: boolean;
  channel: string;
}

function MessageBubble({
  message,
  isOutbound,
  showTimestamp,
  channel,
}: MessageBubbleProps) {
  const timestamp = format(
    new Date('timestamp' in message ? message.timestamp : message.received_at),
    'MMM d, h:mm a'
  );

  return (
    <div className={`flex ${isOutbound ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%] ${isOutbound ? 'order-2' : 'order-1'}`}>
        {/* Sender info for inbound messages */}
        {!isOutbound && showTimestamp && (
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-gray-600">
              {'sender_name' in message
                ? message.sender_name
                : 'from_name' in message
                  ? message.from_name
                  : 'from_number' in message
                    ? message.from_number
                    : 'Customer'}
            </span>
          </div>
        )}

        {/* Message bubble */}
        <div
          className={`
            rounded-2xl px-4 py-2 shadow-sm
            ${
              isOutbound
                ? 'bg-indigo-600 text-white rounded-br-md'
                : 'bg-white text-gray-900 rounded-bl-md border border-gray-200'
            }
          `}
        >
          {/* Message content - handle different message types */}
          {'html_body' in message && message.html_body ? (
            <div
              className={`prose prose-sm max-w-none ${
                isOutbound ? 'prose-invert' : ''
              }`}
              dangerouslySetInnerHTML={{ __html: message.html_body }}
            />
          ) : (
            <p className="text-sm whitespace-pre-wrap">
              {'content' in message
                ? message.content
                : 'body' in message
                  ? message.body
                  : 'text_body' in message
                    ? message.text_body
                    : ''}
            </p>
          )}
        </div>

        {/* Timestamp */}
        {showTimestamp && (
          <div
            className={`mt-1 text-xs text-gray-400 ${
              isOutbound ? 'text-right' : 'text-left'
            }`}
          >
            {timestamp}
            {'status' in message &&
              typeof (message as { status?: string }).status === 'string' && (
                <span className="ml-1">
                  {(message as { status?: string }).status === 'delivered' &&
                    '✓✓'}
                  {(message as { status?: string }).status === 'sent' && '✓'}
                  {(message as { status?: string }).status === 'read' && '✓✓'}
                </span>
              )}
          </div>
        )}
      </div>
    </div>
  );
}

interface CustomerDetailsPanelProps {
  thread: AnyThread;
}

function CustomerDetailsPanel({ thread }: CustomerDetailsPanelProps) {
  // Extract customer data from thread
  const customer = extractCustomerData(thread);

  if (!customer.hasData) return null;

  return (
    <div className="flex-shrink-0 border-t border-gray-200 bg-gray-50 px-4 py-3">
      <details className="group">
        <summary className="flex items-center justify-between cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
          <span className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Customer Details
          </span>
          <span className="text-gray-400 group-open:rotate-180 transition-transform">
            ▼
          </span>
        </summary>

        <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
          {customer.phone && (
            <div className="flex items-center gap-2 text-gray-600">
              <Phone className="h-4 w-4 text-gray-400" />
              <a
                href={`tel:${customer.phone}`}
                className="hover:text-indigo-600"
              >
                {customer.phone}
              </a>
            </div>
          )}

          {customer.email && (
            <div className="flex items-center gap-2 text-gray-600">
              <Mail className="h-4 w-4 text-gray-400" />
              <a
                href={`mailto:${customer.email}`}
                className="hover:text-indigo-600"
              >
                {customer.email}
              </a>
            </div>
          )}

          {customer.location && (
            <div className="flex items-center gap-2 text-gray-600">
              <MapPin className="h-4 w-4 text-gray-400" />
              {customer.location}
            </div>
          )}

          {customer.eventDate && (
            <div className="flex items-center gap-2 text-gray-600">
              <Calendar className="h-4 w-4 text-gray-400" />
              {customer.eventDate}
            </div>
          )}
        </div>
      </details>
    </div>
  );
}

// Helper functions
function getCustomerName(thread: AnyThread): string {
  // SMSThread and SocialThread extend BaseThread with customer_name
  if ('customer_name' in thread && thread.customer_name) {
    return thread.customer_name;
  }
  // EmailThread has first_message_from
  if ('first_message_from' in thread && thread.first_message_from) {
    return thread.first_message_from;
  }
  // Fallback: check first message for email threads
  if (thread.channel === 'email' && thread.messages.length > 0) {
    const firstMsg = thread.messages[0] as {
      from_name?: string;
      from_address?: string;
    };
    return firstMsg.from_name || firstMsg.from_address || 'Unknown Customer';
  }
  return 'Unknown Customer';
}

function getContactInfo(thread: AnyThread) {
  const items = [];

  // SMSThread and SocialThread have customer_phone
  if ('customer_phone' in thread && thread.customer_phone) {
    items.push(
      <span key="phone" className="flex items-center gap-1">
        <Phone className="h-3.5 w-3.5" />
        {thread.customer_phone}
      </span>
    );
  }

  // EmailThread has first_message_from_address
  if (
    'first_message_from_address' in thread &&
    thread.first_message_from_address
  ) {
    items.push(
      <span key="email" className="flex items-center gap-1">
        <Mail className="h-3.5 w-3.5" />
        {thread.first_message_from_address}
      </span>
    );
  }

  // SocialThread has channel that indicates platform
  if (thread.channel === 'facebook' || thread.channel === 'instagram') {
    items.push(
      <span key="platform" className="capitalize">
        via {thread.channel}
      </span>
    );
  }

  return items.length > 0 ? items : <span>No contact info</span>;
}

function shouldShowTimestamp(messages: AnyMessage[], index: number): boolean {
  if (index === 0) return true;

  const currentMsg = messages[index];
  const previousMsg = messages[index - 1];
  const current = new Date(
    'timestamp' in currentMsg ? currentMsg.timestamp : currentMsg.received_at
  );
  const previous = new Date(
    'timestamp' in previousMsg ? previousMsg.timestamp : previousMsg.received_at
  );

  // Show timestamp if more than 5 minutes apart
  return current.getTime() - previous.getTime() > 5 * 60 * 1000;
}

function extractCustomerData(thread: AnyThread) {
  const data: {
    hasData: boolean;
    phone?: string;
    email?: string;
    location?: string;
    eventDate?: string;
  } = { hasData: false };

  // SMS and Social threads have customer_phone (snake_case)
  if ('customer_phone' in thread && thread.customer_phone) {
    data.phone = thread.customer_phone;
    data.hasData = true;
  }

  // Email threads have first_message_from_address
  if (
    'first_message_from_address' in thread &&
    thread.first_message_from_address
  ) {
    data.email = thread.first_message_from_address;
    data.hasData = true;
  }

  // Check for customer_email on BaseThread types
  if ('customer_email' in thread && thread.customer_email) {
    data.email = thread.customer_email;
    data.hasData = true;
  }

  // Event location and date may be present on some threads
  // Use type assertions for optional properties that may exist
  const threadWithExtras = thread as {
    event_location?: string;
    event_date?: string;
  };
  if (threadWithExtras.event_location) {
    data.location = threadWithExtras.event_location;
    data.hasData = true;
  }

  if (threadWithExtras.event_date) {
    data.eventDate = format(
      new Date(threadWithExtras.event_date),
      'MMM d, yyyy'
    );
    data.hasData = true;
  }

  return data;
}

export default ThreadView;
