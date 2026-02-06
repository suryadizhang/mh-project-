const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  baseURL: API_BASE_URL,

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json() as Promise<T>;
  },

  get<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
    const requestHeaders = headers || {};
    return this.request<T>(endpoint, {
      method: 'GET',
      headers: requestHeaders,
    });
  },

  post<T>(
    endpoint: string,
    data?: any,
    headers?: Record<string, string>
  ): Promise<T> {
    const requestHeaders = headers || {};
    const requestOptions: RequestInit = {
      method: 'POST',
      headers: requestHeaders,
    };

    if (data) {
      requestOptions.body = JSON.stringify(data);
    }

    return this.request<T>(endpoint, requestOptions);
  },

  put<T>(
    endpoint: string,
    data?: any,
    headers?: Record<string, string>
  ): Promise<T> {
    const requestHeaders = headers || {};
    const requestOptions: RequestInit = {
      method: 'PUT',
      headers: requestHeaders,
    };

    if (data) {
      requestOptions.body = JSON.stringify(data);
    }

    return this.request<T>(endpoint, requestOptions);
  },

  delete<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
    const requestHeaders = headers || {};
    return this.request<T>(endpoint, {
      method: 'DELETE',
      headers: requestHeaders,
    });
  },
};
