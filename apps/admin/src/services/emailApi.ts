/**
 * Email API Service
 * Handles communication with backend email management API
 * Supports 2 inboxes: cs@myhibachichef.com + myhibachichef@gmail.com
 */

import { api } from '@/lib/api';

// ============================================================================
// TYPES
// ============================================================================

export interface EmailAddress {
  email: string;
  name?: string;
}

export interface EmailAttachment {
  filename: string;
  content_type: string;
  size_bytes: number;
}

export interface Email {
  message_id: string;
  thread_id?: string;
  from_address: string;
  from_name?: string;
  to_address: string;
  to_name?: string;
  cc?: EmailAddress[];
  bcc?: EmailAddress[];
  subject: string;
  text_body?: string;
  html_body?: string;
  received_at: string;
  is_read: boolean;
  is_starred: boolean;
  is_archived: boolean;
  has_attachments: boolean;
  attachments?: EmailAttachment[];
  labels?: string[];
}

export interface EmailThread {
  thread_id: string;
  subject: string;
  participants: EmailAddress[];
  messages: Email[];
  message_count: number;
  unread_count: number;
  last_message_at: string;
  is_read: boolean;
  is_starred: boolean;
  is_archived: boolean;
  labels?: string[];
  has_attachments?: boolean;
}

export interface EmailListResponse {
  inbox: string;
  threads: EmailThread[];
  total_count: number;
  unread_count: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface EmailStats {
  inbox: string;
  total_emails: number;
  unread_emails: number;
  starred_emails: number;
  archived_emails: number;
  today_count: number;
  week_count: number;
}

export interface SendEmailRequest {
  to: EmailAddress[];
  cc?: EmailAddress[];
  bcc?: EmailAddress[];
  subject: string;
  text_body: string;
  html_body?: string;
  in_reply_to?: string;
  thread_id?: string;
}

export interface UpdateEmailRequest {
  is_read?: boolean;
  is_starred?: boolean;
  is_archived?: boolean;
  labels?: string[];
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Get email statistics for both inboxes
 */
export async function getEmailStats(): Promise<{
  customer_support: EmailStats;
  payments: EmailStats;
}> {
  const response = await api.get<{
    customer_support: EmailStats;
    payments: EmailStats;
  }>('/admin/emails/stats');
  return response.data!;
}

/**
 * Get customer support emails (cs@myhibachichef.com)
 * READ/WRITE inbox - Can reply, mark as read, star, archive
 */
export async function getCustomerSupportEmails(params?: {
  page?: number;
  limit?: number;
  unread_only?: boolean;
  starred_only?: boolean;
  archived?: boolean;
  search?: string;
}): Promise<EmailListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set('page', params.page.toString());
  if (params?.limit) queryParams.set('limit', params.limit.toString());
  if (params?.unread_only) queryParams.set('unread_only', 'true');
  if (params?.starred_only) queryParams.set('starred_only', 'true');
  if (params?.archived !== undefined)
    queryParams.set('archived', params.archived.toString());
  if (params?.search) queryParams.set('search', params.search);

  const queryString = queryParams.toString();
  const url = queryString
    ? `/admin/emails/customer-support?${queryString}`
    : '/admin/emails/customer-support';

  const response = await api.get<EmailListResponse>(url);
  return response.data!;
}

/**
 * Get payment emails (myhibachichef@gmail.com)
 * READ-ONLY inbox - For manual payment verification
 */
export async function getPaymentEmails(params?: {
  page?: number;
  limit?: number;
  unread_only?: boolean;
  search?: string;
}): Promise<EmailListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set('page', params.page.toString());
  if (params?.limit) queryParams.set('limit', params.limit.toString());
  if (params?.unread_only) queryParams.set('unread_only', 'true');
  if (params?.search) queryParams.set('search', params.search);

  const queryString = queryParams.toString();
  const url = queryString
    ? `/admin/emails/payments?${queryString}`
    : '/admin/emails/payments';

  const response = await api.get<EmailListResponse>(url);
  return response.data!;
}

/**
 * Get a specific email thread from customer support inbox
 */
export async function getCustomerSupportThread(
  thread_id: string
): Promise<EmailThread> {
  const response = await api.get<EmailThread>(
    `/admin/emails/customer-support/${thread_id}`
  );
  return response.data!;
}

/**
 * Send or reply to customer support email
 */
export async function sendCustomerSupportEmail(
  request: SendEmailRequest
): Promise<{ success: boolean; message_id: string; recipient: string }> {
  const response = await api.post<{
    success: boolean;
    message_id: string;
    recipient: string;
  }>(
    '/admin/emails/customer-support/send',
    request as unknown as Record<string, unknown>
  );
  return response.data!;
}

/**
 * Update customer support email (mark as read, star, archive)
 */
export async function updateCustomerSupportEmail(
  message_id: string,
  update: UpdateEmailRequest
): Promise<{
  success: boolean;
  message_id: string;
  updated_fields: UpdateEmailRequest;
}> {
  const response = await api.patch<{
    success: boolean;
    message_id: string;
    updated_fields: UpdateEmailRequest;
  }>(
    `/admin/emails/customer-support/${message_id}`,
    update as unknown as Record<string, unknown>
  );
  return response.data!;
}

/**
 * Bulk update customer support emails (mark read/unread, star/unstar, archive/unarchive, delete)
 * Supports actions: mark_read, mark_unread, star, unstar, archive, unarchive, delete
 */
export async function bulkUpdateCustomerSupportEmails(
  message_ids: string[],
  action:
    | 'mark_read'
    | 'mark_unread'
    | 'star'
    | 'unstar'
    | 'archive'
    | 'unarchive'
    | 'delete'
): Promise<{
  success: boolean;
  total_requested: number;
  success_count: number;
  failed_count: number;
  errors: Array<{ message_id: string; error: string }>;
}> {
  const response = await api.post<{
    success: boolean;
    total_requested: number;
    success_count: number;
    failed_count: number;
    errors: Array<{ message_id: string; error: string }>;
  }>('/admin/emails/customer-support/bulk', {
    message_ids,
    action,
  } as unknown as Record<string, unknown>);
  return response.data!;
}

/**
 * Delete (archive) customer support email
 */
export async function deleteCustomerSupportEmail(
  message_id: string
): Promise<{ success: boolean; message_id: string; action: string }> {
  const response = await api.delete<{
    success: boolean;
    message_id: string;
    action: string;
  }>(`/admin/emails/customer-support/${message_id}`);
  return response.data!;
}

/**
 * Delete payment email
 */
export async function deletePaymentEmail(
  message_id: string
): Promise<{ success: boolean; message_id: string; action: string }> {
  const response = await api.delete<{
    success: boolean;
    message_id: string;
    action: string;
  }>(`/admin/emails/payments/${message_id}`);
  return response.data!;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Format email address for display
 */
export function formatEmailAddress(email: EmailAddress): string {
  return email.name ? `${email.name} <${email.email}>` : email.email;
}

/**
 * Format date/time relative (Gmail style)
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) {
    return 'Just now';
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    // Show date (e.g., "Nov 24")
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
}

/**
 * Get email preview text (first 100 chars)
 */
export function getEmailPreview(email: Email): string {
  const text = email.text_body || email.html_body || '';
  const preview = text.replace(/<[^>]+>/g, '').trim(); // Strip HTML tags
  return preview.length > 100 ? preview.substring(0, 100) + '...' : preview;
}

/**
 * Get initials from name for avatar
 */
export function getInitials(name?: string, email?: string): string {
  if (name) {
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }
  if (email) {
    return email.substring(0, 2).toUpperCase();
  }
  return 'U';
}

/**
 * Group emails by date (Today, Yesterday, This Week, etc.)
 */
export function groupThreadsByDate(
  threads: EmailThread[]
): Record<string, EmailThread[]> {
  const groups: Record<string, EmailThread[]> = {
    Today: [],
    Yesterday: [],
    'This Week': [],
    'This Month': [],
    Older: [],
  };

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const thisWeek = new Date(today);
  thisWeek.setDate(thisWeek.getDate() - 7);
  const thisMonth = new Date(today);
  thisMonth.setMonth(thisMonth.getMonth() - 1);

  threads.forEach(thread => {
    const threadDate = new Date(thread.last_message_at);

    if (threadDate >= today) {
      groups.Today.push(thread);
    } else if (threadDate >= yesterday) {
      groups.Yesterday.push(thread);
    } else if (threadDate >= thisWeek) {
      groups['This Week'].push(thread);
    } else if (threadDate >= thisMonth) {
      groups['This Month'].push(thread);
    } else {
      groups.Older.push(thread);
    }
  });

  // Remove empty groups
  Object.keys(groups).forEach(key => {
    if (groups[key].length === 0) {
      delete groups[key];
    }
  });

  return groups;
}
