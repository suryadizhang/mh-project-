/**
 * Email and Label type definitions
 * Used for customer support email management with Gmail-style labels
 */

export interface EmailAddress {
  email: string;
  name?: string;
}

export interface Email {
  message_id: string;
  thread_id: string;
  imap_uid?: number;
  inbox: string;
  folder: string;
  subject?: string;
  from_address: string;
  from_name?: string;
  to_addresses?: string[];
  cc_addresses?: string[];
  reply_to?: string;
  text_body?: string;
  html_body?: string;
  received_at: string;
  sent_at?: string;
  is_read: boolean;
  is_starred: boolean;
  is_archived: boolean;
  is_spam: boolean;
  has_attachments: boolean;
  attachments?: EmailAttachment[];
  labels: string[]; // Array of label slugs
  created_at: string;
  updated_at: string;
}

export interface EmailAttachment {
  filename: string;
  size_bytes: number;
  content_type: string;
}

export interface EmailThread {
  thread_id: string;
  inbox: string;
  subject?: string;
  participants: EmailAddress[];
  messages: Email[];
  message_count: number;
  unread_count: number;
  first_message_at?: string;
  last_message_at?: string;
  is_read: boolean;
  is_starred: boolean;
  is_archived: boolean;
  has_attachments: boolean;
  labels: string[];
  created_at: string;
  updated_at: string;
}

export interface EmailListResponse {
  threads: EmailThread[];
  total_count: number;
  page: number;
  limit: number;
  unread_count: number;
  starred_count: number;
  archived_count: number;
}

export interface Label {
  id: string;
  name: string;
  slug: string;
  description?: string;
  color: string;
  icon?: string;
  is_system: boolean;
  is_archived: boolean;
  email_count: number;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface LabelCreate {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  sort_order?: number;
}

export interface LabelUpdate {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  sort_order?: number;
}

export interface BulkEmailUpdate {
  message_ids: string[];
  action?:
    | 'mark_read'
    | 'mark_unread'
    | 'star'
    | 'unstar'
    | 'archive'
    | 'unarchive'
    | 'delete'
    | 'apply_label'
    | 'remove_label';
  label_slug?: string;
  is_read?: boolean;
  is_starred?: boolean;
  is_archived?: boolean;
}

export interface BulkUpdateResponse {
  success: boolean;
  total_requested: number;
  success_count: number;
  failed_count: number;
  errors?: Array<{
    message_id: string;
    error: string;
  }>;
  action: string;
}

export interface EmailListParams {
  page?: number;
  limit?: number;
  unread_only?: boolean;
  starred_only?: boolean;
  archived?: boolean;
  search?: string;
  label?: string;
}

export interface EmailStats {
  total_emails: number;
  unread_emails: number;
  starred_emails: number;
  archived_emails: number;
  today_count: number;
}
