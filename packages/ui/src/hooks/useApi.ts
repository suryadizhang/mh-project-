import { useState, useCallback } from 'react';

export interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
}

export interface ApiState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
}

export const useApi = <T = any>() => {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    isLoading: false,
  });

  const request = useCallback(async (url: string, options: ApiOptions = {}) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const { method = 'GET', headers = {}, body } = options;

      const config: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
      };

      if (body && method !== 'GET') {
        config.body = JSON.stringify(body);
      }

      const response = await fetch(url, config);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      setState({
        data,
        error: null,
        isLoading: false,
      });

      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'An error occurred';
      setState({
        data: null,
        error: errorMessage,
        isLoading: false,
      });
      throw error;
    }
  }, []);

  const get = useCallback(
    (url: string, headers?: Record<string, string>) =>
      request(url, { method: 'GET', headers }),
    [request]
  );

  const post = useCallback(
    (url: string, body?: any, headers?: Record<string, string>) =>
      request(url, { method: 'POST', body, headers }),
    [request]
  );

  const put = useCallback(
    (url: string, body?: any, headers?: Record<string, string>) =>
      request(url, { method: 'PUT', body, headers }),
    [request]
  );

  const del = useCallback(
    (url: string, headers?: Record<string, string>) =>
      request(url, { method: 'DELETE', headers }),
    [request]
  );

  return {
    ...state,
    request,
    get,
    post,
    put,
    delete: del,
  };
};
