/**
 * Email API Service
 * Handles email inbox and label management endpoints
 */

import { api, type ApiResponse } from '@/lib/api';
import type {
  Email,
  EmailThread,
  EmailListResponse,
  EmailListParams,
  Label,
  LabelCreate,
  LabelUpdate,
  BulkEmailUpdate,
  BulkUpdateResponse,
  EmailStats,
} from '@/types/email';

// Helper to safely extract data from API response
function extractData<T>(response: ApiResponse<T>): T {
  console.log('[extractData] Received response:', {
    success: response.success,
    hasData: !!response.data,
    hasError: !!response.error,
    error: response.error,
  });

  if (!response || typeof response !== 'object') {
    console.error(
      '[extractData] Invalid response type:',
      typeof response,
      response
    );
    throw new Error('Invalid API response format');
  }

  if (!response.success) {
    const errorMsg = response.error || 'API request failed';
    console.error('[extractData] API returned error:', errorMsg);
    throw new Error(errorMsg);
  }

  if (!response.data) {
    console.error('[extractData] API success but no data:', response);
    throw new Error('API returned success but no data');
  }

  return response.data;
}

/**
 * Email Endpoints
 */
export const emailService = {
  /**
   * Get customer support emails (inbox: customer_support)
   */
  getEmails: async (
    params: EmailListParams = {}
  ): Promise<EmailListResponse> => {
    // Build query string from params
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.set('page', params.page.toString());
    if (params.limit) queryParams.set('limit', params.limit.toString());
    if (params.label) queryParams.set('label', params.label);
    if (params.search) queryParams.set('search', params.search);
    if (params.unread_only) queryParams.set('unread_only', 'true');
    if (params.starred_only) queryParams.set('starred_only', 'true');

    const queryString = queryParams.toString();
    const path = `/api/v1/admin/emails/customer-support${queryString ? `?${queryString}` : ''}`;

    console.log('Calling API:', path);
    const response = await api.get<EmailListResponse>(path);
    console.log('Raw API response:', response);
    console.log('Response.success:', response.success);
    console.log('Response.data:', response.data);
    console.log('Response.error:', response.error);
    return extractData(response);
  },

  /**
   * Get specific email thread
   */
  getEmailThread: async (threadId: string): Promise<EmailThread> => {
    const response = await api.get<EmailThread>(
      `/api/v1/admin/emails/thread/${threadId}`
    );
    return extractData(response);
  },

  /**
   * Update email (mark read, star, etc.)
   */
  updateEmail: async (
    messageId: string,
    data: Partial<Email>
  ): Promise<Email> => {
    const response = await api.patch<Email>(
      `/api/v1/admin/emails/${messageId}`,
      data as Record<string, unknown>
    );
    return extractData(response);
  },

  /**
   * Delete email
   */
  deleteEmail: async (messageId: string): Promise<{ success: boolean }> => {
    const response = await api.delete<{ success: boolean }>(
      `/api/v1/admin/emails/${messageId}`
    );
    return extractData(response);
  },

  /**
   * Bulk update emails (mark read/unread, star, archive, labels)
   */
  bulkUpdate: async (data: BulkEmailUpdate): Promise<BulkUpdateResponse> => {
    const response = await api.post<BulkUpdateResponse>(
      '/api/v1/admin/emails/bulk',
      data as unknown as Record<string, unknown>
    );
    return extractData(response);
  },

  /**
   * Get email stats
   */
  getStats: async (inbox: string = 'customer_support'): Promise<EmailStats> => {
    const response = await api.get<EmailStats>(
      `/api/v1/admin/emails/stats?inbox=${inbox}`
    );
    return extractData(response);
  },
};

/**
 * Label Endpoints
 * Backend route: /api/v1/admin/emails/labels
 */
export const labelService = {
  /**
   * Get all labels
   */
  getLabels: async (includeArchived: boolean = false): Promise<Label[]> => {
    const response = await api.get<Label[]>(
      `/api/v1/admin/emails/labels?include_archived=${includeArchived}`
    );
    return extractData(response);
  },

  /**
   * Create new label
   */
  createLabel: async (data: LabelCreate): Promise<Label> => {
    const response = await api.post<Label>(
      '/api/v1/admin/emails/labels',
      data as unknown as Record<string, unknown>
    );
    return extractData(response);
  },

  /**
   * Update label
   */
  updateLabel: async (labelId: number, data: LabelUpdate): Promise<Label> => {
    const response = await api.patch<Label>(
      `/api/v1/admin/emails/labels/${labelId}`,
      data as Record<string, unknown>
    );
    return extractData(response);
  },

  /**
   * Delete (archive) label
   */
  deleteLabel: async (labelId: number): Promise<{ success: boolean }> => {
    const response = await api.delete<{ success: boolean }>(
      `/api/v1/admin/emails/labels/${labelId}`
    );
    return extractData(response);
  },
};

/**
 * Utility functions
 */
export const emailUtils = {
  /**
   * Format email date (e.g., "2h ago", "Yesterday", "Dec 25")
   */
  formatDate: (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) {
      const diffMins = Math.floor(diffMs / (1000 * 60));
      return diffMins < 1 ? 'Just now' : `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    }
  },

  /**
   * Extract preview text from email body (first 100 chars)
   */
  getPreviewText: (email: Email): string => {
    const body = email.text_body || email.html_body || '';
    const plainText = body.replace(/<[^>]*>/g, ''); // Strip HTML tags
    return plainText.slice(0, 100) + (plainText.length > 100 ? '...' : '');
  },

  /**
   * Get sender display name
   */
  getSenderName: (email: Email): string => {
    return email.from_name || email.from_address.split('@')[0];
  },
};
