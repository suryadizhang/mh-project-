/**
 * Knowledge Sync API Service
 * Client for interacting with backend knowledge sync endpoints
 * Base URL: /api/v1/knowledge/sync
 */

import axios, { AxiosError, AxiosInstance } from 'axios';

import {
  SyncApiError,
  SyncDiff,
  SyncHealthResponse,
  SyncHistoryResponse,
  SyncOperationResponse,
  SyncRequest,
  SyncSource,
  SyncStatusResponse,
} from '@/types/knowledge-sync.types';

/**
 * Knowledge Sync Service Class
 */
export class KnowledgeSyncService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor(baseURL?: string) {
    this.baseURL =
      baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    this.api = axios.create({
      baseURL: `${this.baseURL}/api/v1/ai/knowledge/sync`,
      timeout: 30000, // 30 seconds timeout for sync operations
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for authentication
    this.api.interceptors.request.use(config => {
      const token = this.getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      response => response,
      (error: AxiosError<SyncApiError>) => {
        return Promise.reject(this.handleError(error));
      }
    );
  }

  /**
   * Get authentication token from storage
   */
  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return (
      localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
    );
  }

  /**
   * Handle API errors with proper formatting
   */
  private handleError(error: AxiosError<SyncApiError>): Error {
    if (error.response) {
      // Server responded with error
      const message = error.response.data?.error || error.message;
      const detail = error.response.data?.detail || '';
      return new Error(`${message}${detail ? `: ${detail}` : ''}`);
    } else if (error.request) {
      // Request made but no response
      return new Error(
        'No response from server. Please check your connection.'
      );
    } else {
      // Something else happened
      return new Error(error.message);
    }
  }

  /**
   * Get current sync status for all sources
   * GET /status
   */
  async getSyncStatus(): Promise<SyncStatusResponse> {
    const response = await this.api.get<SyncStatusResponse>('/status');
    return response.data;
  }

  /**
   * Get differences between TypeScript files and database
   * GET /diff?sources=faqs,packages
   */
  async getDiff(sources?: SyncSource[]): Promise<SyncDiff> {
    const params = sources ? { sources: sources.join(',') } : {};
    const response = await this.api.get<SyncDiff>('/diff', { params });
    return response.data;
  }

  /**
   * Trigger automatic sync (only sync if changes detected)
   * POST /auto
   */
  async triggerAutoSync(request?: SyncRequest): Promise<SyncOperationResponse> {
    const response = await this.api.post<SyncOperationResponse>(
      '/auto',
      request || {}
    );
    return response.data;
  }

  /**
   * Force sync all sources (override manual changes)
   * POST /force
   */
  async triggerForceSync(
    request?: SyncRequest
  ): Promise<SyncOperationResponse> {
    const response = await this.api.post<SyncOperationResponse>(
      '/force',
      request || {}
    );
    return response.data;
  }

  /**
   * Get sync history with pagination
   * GET /history?page=1&per_page=20&source=faqs&sync_type=auto
   */
  async getSyncHistory(params?: {
    page?: number;
    per_page?: number;
    source?: SyncSource;
    sync_type?: 'auto' | 'manual';
  }): Promise<SyncHistoryResponse> {
    const response = await this.api.get<SyncHistoryResponse>('/history', {
      params,
    });
    return response.data;
  }

  /**
   * Check sync system health
   * GET /health
   */
  async getHealth(): Promise<SyncHealthResponse> {
    const response = await this.api.get<SyncHealthResponse>('/health');
    return response.data;
  }

  /**
   * Dry run - detect changes without applying them
   */
  async dryRun(sources?: SyncSource[]): Promise<SyncOperationResponse> {
    return this.triggerAutoSync({
      sources,
      dry_run: true,
    });
  }
}

/**
 * Singleton instance
 */
export const knowledgeSyncService = new KnowledgeSyncService();

/**
 * Hook-friendly wrapper for React components
 */
export const useKnowledgeSyncService = () => knowledgeSyncService;
