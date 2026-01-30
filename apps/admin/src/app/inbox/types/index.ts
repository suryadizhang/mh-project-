/**
 * Inbox Types Module
 * ==================
 * Centralized type definitions for the unified inbox system.
 *
 * Supports multiple channels: Email, SMS, Facebook, Instagram
 */

import type { LucideIcon } from 'lucide-react';

// ============================================================================
// Channel Types
// ============================================================================

export const CHANNELS = {
  ALL: 'all',
  FACEBOOK: 'facebook',
  INSTAGRAM: 'instagram',
  SMS: 'sms',
  EMAIL: 'email',
} as const;

export type ChannelType = (typeof CHANNELS)[keyof typeof CHANNELS];

export interface ChannelConfig {
  bg: string;
  text: string;
  icon: LucideIcon;
  label: string;
  borderColor: string;
}

// ============================================================================
// Email Tab Types
// ============================================================================

export type InboxTab = 'customer_support' | 'payments';

/**
 * Channel-based tab statistics (unread counts per channel)
 * Used by ChannelTabs component for badge display
 */
export type TabStats = Record<ChannelType | 'all', number>;

// ============================================================================
// Thread & Message Types
// ============================================================================

/**
 * Base thread interface for all channels
 */
export interface BaseThread {
  id: string;
  channel: ChannelType;
  customer_name: string;
  customer_phone?: string;
  customer_email?: string;
  preview: string;
  unread: boolean;
  timestamp: string;
  labels?: Label[];
}

/**
 * SMS Thread
 */
export interface SMSThread extends BaseThread {
  channel: 'sms';
  phone_number: string;
  messages: SMSMessage[];
}

/**
 * Social Thread (Facebook/Instagram)
 */
export interface SocialThread extends BaseThread {
  channel: 'facebook' | 'instagram';
  social_id: string;
  platform_thread_id: string;
  messages: SocialMessage[];
}

/**
 * Email Thread
 */
export interface EmailThread {
  id: string; // Canonical ID for consistency with other thread types
  thread_id: string; // Legacy field, kept for backwards compatibility
  channel: 'email'; // Channel type for consistency with other thread types
  subject: string;
  messages: EmailMessage[];
  is_read: boolean;
  is_starred: boolean;
  is_archived: boolean;
  labels?: Label[];
  last_message_at: string;
  message_count: number;
  participant_count: number;
  first_message_from?: string;
  first_message_from_address?: string;
}

/**
 * Union type for all thread types
 */
export type Thread = SMSThread | SocialThread | EmailThread;

// ============================================================================
// Message Types
// ============================================================================

export interface BaseMessage {
  id: string;
  timestamp: string;
  direction: 'inbound' | 'outbound';
}

export interface SMSMessage extends BaseMessage {
  type: 'sms';
  body: string;
  from_number: string;
  to_number: string;
}

export interface SocialMessage extends BaseMessage {
  type: 'social';
  content: string;
  sender_id: string;
  sender_name: string;
}

export interface EmailMessage {
  message_id: string;
  from_name: string;
  from_address: string;
  to_addresses: string[];
  cc_addresses?: string[];
  bcc_addresses?: string[];
  subject: string;
  html_body: string;
  text_body: string;
  received_at: string;
  attachments?: EmailAttachment[];
}

export interface EmailAttachment {
  filename: string;
  size: number;
  content_type: string;
  url?: string;
}

// ============================================================================
// Label Types
// ============================================================================

export interface Label {
  id: string;
  name: string;
  color: string;
  user_id?: string;
}

// ============================================================================
// Reply Template Types
// ============================================================================

export interface ReplyTemplate {
  id: string;
  name: string;
  text: string;
}

// ============================================================================
// Quick Reply Types
// ============================================================================

export interface QuickReply {
  id: string;
  label: string;
  text: string;
}

// ============================================================================
// Team Member Types (for assignment)
// ============================================================================

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'sales' | 'support' | 'manager';
  avatar?: string;
}

// ============================================================================
// Filter & Sort Types
// ============================================================================

export interface InboxFilters {
  channel: ChannelType;
  tab?: InboxTab;
  showUnreadOnly: boolean;
  showStarredOnly: boolean;
  searchQuery: string;
}

export type SortOrder = 'newest' | 'oldest';

// ============================================================================
// Bulk Action Types
// ============================================================================

export type BulkAction =
  | 'mark_read'
  | 'mark_unread'
  | 'star'
  | 'unstar'
  | 'archive'
  | 'unarchive'
  | 'delete';

// ============================================================================
// State Types
// ============================================================================

export interface InboxState {
  // Channel & Tab
  activeChannel: ChannelType;
  activeTab: InboxTab;

  // Threads
  threads: Thread[];
  selectedThread: Thread | null;
  loading: boolean;

  // Filters
  filters: InboxFilters;

  // Selection (for bulk actions)
  selectedIds: Set<string>;

  // UI States
  showReplyBox: boolean;
  showDeleteModal: boolean;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ThreadsResponse {
  threads: Thread[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface SendMessageResponse {
  success: boolean;
  message_id?: string;
  error?: string;
}

export interface AIReplyResponse {
  success: boolean;
  reply: string;
  confidence: number;
}
