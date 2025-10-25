// API Response types (simplified for now)
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
  requestId: string;
}

// Legacy page-based pagination (deprecated, use CursorPaginatedResponse)
export interface PaginatedResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Modern cursor-based pagination (MEDIUM #34 Phase 2)
// Provides consistent O(1) performance regardless of page depth
export interface CursorPaginatedResponse<T = unknown> {
  items: T[];
  next_cursor: string | null;
  prev_cursor: string | null;
  has_next: boolean;
  has_prev: boolean;
  count: number;
  total_count?: number; // Optional, expensive operation
}

// Alias for convenience
export type PaginatedData<T> = CursorPaginatedResponse<T>;

// Type-safe API client configuration
export interface ApiClientConfig {
  baseUrl: string;
  timeout?: number;
  retries?: number;
  headers?: Record<string, string>;
}

// Simplified API client using fetch
export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = { ...this.defaultHeaders, ...options.headers as Record<string, string> };

    // Add request ID for tracing
    headers['X-Request-ID'] = crypto.randomUUID();

    // Add auth token if available
    if (typeof localStorage !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    return response.json() as Promise<ApiResponse<T>>;
  }

  async get<T>(
    endpoint: string,
    searchParams?: Record<string, string>
  ): Promise<ApiResponse<T>> {
    const url = searchParams 
      ? `${endpoint}?${new URLSearchParams(searchParams).toString()}`
      : endpoint;
    return this.request<T>(url);
  }

  async post<T, U = unknown>(endpoint: string, json?: U): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(json),
    });
  }

  async put<T, U = unknown>(endpoint: string, json?: U): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(json),
    });
  }

  async patch<T, U = unknown>(endpoint: string, json?: U): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(json),
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  // Paginated endpoints
  async getPaginated<T>(
    endpoint: string,
    params?: { page?: number; pageSize?: number; [key: string]: unknown }
  ): Promise<ApiResponse<PaginatedResponse<T>>> {
    const searchParams = {
      page: params?.page?.toString() ?? '1',
      pageSize: params?.pageSize?.toString() ?? '20',
      ...Object.fromEntries(
        Object.entries(params ?? {})
          .filter(([key]) => !['page', 'pageSize'].includes(key))
          .map(([key, value]) => [key, String(value)])
      ),
    };

    return this.get<PaginatedResponse<T>>(endpoint, searchParams);
  }
}

// Default client instance
export const apiClient = new ApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
});

// Export convenience methods
export const api = {
  get: <T>(url: string, params?: Record<string, string>) =>
    apiClient.get<T>(url, params),
  post: <T, U = unknown>(url: string, data?: U) =>
    apiClient.post<T, U>(url, data),
  put: <T, U = unknown>(url: string, data?: U) =>
    apiClient.put<T, U>(url, data),
  patch: <T, U = unknown>(url: string, data?: U) =>
    apiClient.patch<T, U>(url, data),
  delete: <T>(url: string) => apiClient.delete<T>(url),
  paginated: <T>(
    url: string,
    params?: { page?: number; pageSize?: number; [key: string]: unknown }
  ) => apiClient.getPaginated<T>(url, params),
};

export default apiClient;
