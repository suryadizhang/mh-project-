/**
 * AI API Service for Admin Panel
 * Handles communication with the AI API backend for chat functionality
 */

import { logger } from '@/lib/logger';

const AI_API_BASE_URL =
  process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8002';

export interface ChatMessage {
  message_id: string;
  conversation_id: string;
  content: string;
  timestamp: string;
  channel: string;
  confidence?: number;
  suggestions?: string[];
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  channel?: string;
  user_id?: string;
  user_role?: 'customer' | 'admin' | 'staff' | 'super_admin';
  context?: Record<string, any>;
}

export interface AdminChatRequest {
  message: string;
  test_mode?: boolean;
  channel?: string;
  user_role?: 'admin' | 'staff' | 'super_admin';
  context?: Record<string, any>;
}

export interface AdminChatResponse {
  message_id: string;
  conversation_id: string;
  content: string;
  timestamp: string;
  debug_info?: {
    ai_pipeline_version: string;
    confidence_score: number;
    knowledge_base_hits: number;
    fallback_used: boolean;
    processing_steps: string[];
  };
  processing_time_ms?: number;
}

export interface SystemHealth {
  chat_service: string;
  knowledge_base: string;
  ai_pipeline: string;
  database: string;
  uptime_seconds: number;
  last_error?: string;
}

export interface ChatAnalytics {
  total_conversations: number;
  total_messages: number;
  conversations_today: number;
  messages_today: number;
  avg_messages_per_conversation: number;
  channels: Record<string, number>;
  hourly_activity: Array<{ hour: number; messages: number }>;
}

class AIApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = AI_API_BASE_URL;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    const response = await fetch(url, { ...defaultOptions, ...options });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * Send a chat message and get AI response
   */
  async sendChatMessage(request: ChatRequest): Promise<ChatMessage> {
    return this.makeRequest<ChatMessage>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        message: request.message,
        conversation_id: request.conversation_id,
        channel: request.channel || 'admin',
        user_id: request.user_id,
        user_role: request.user_role || 'admin',
        context: request.context || {},
      }),
    });
  }

  /**
   * Test admin chat functionality with debug information
   */
  async testAdminChat(request: AdminChatRequest): Promise<AdminChatResponse> {
    return this.makeRequest<AdminChatResponse>('/api/admin/chat/test', {
      method: 'POST',
      body: JSON.stringify({
        message: request.message,
        test_mode: request.test_mode ?? true,
        channel: request.channel || 'admin',
        user_role: request.user_role || 'admin',
        context: request.context || {},
      }),
    });
  }

  /**
   * Get chat analytics and usage statistics
   */
  async getChatAnalytics(days: number = 7): Promise<ChatAnalytics> {
    return this.makeRequest<ChatAnalytics>(`/api/admin/analytics?days=${days}`);
  }

  /**
   * Get system health status
   */
  async getSystemHealth(): Promise<SystemHealth> {
    return this.makeRequest<SystemHealth>('/api/admin/system/health');
  }

  /**
   * Get conversations for admin review
   */
  async getAdminConversations(
    limit: number = 50,
    offset: number = 0
  ): Promise<any[]> {
    return this.makeRequest<any[]>(
      `/api/admin/conversations?limit=${limit}&offset=${offset}`
    );
  }

  /**
   * Get conversation messages
   */
  async getConversationMessages(
    conversationId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<any[]> {
    return this.makeRequest<any[]>(
      `/api/conversations/${conversationId}/messages?limit=${limit}&offset=${offset}`
    );
  }

  /**
   * Health check for AI API
   */
  async healthCheck(): Promise<{
    status: string;
    service: string;
    version: string;
  }> {
    return this.makeRequest<{
      status: string;
      service: string;
      version: string;
    }>('/api/health');
  }

  /**
   * Check if AI API is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch (error) {
      logger.warn('AI API not available', {
        error: error instanceof Error ? error.message : String(error),
      });
      return false;
    }
  }
}

// Create singleton instance
export const aiApiService = new AIApiService();

// Export for easier imports
export default aiApiService;
