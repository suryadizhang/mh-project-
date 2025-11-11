export declare const api: {
    baseURL: string;
    request<T>(endpoint: string, options?: RequestInit): Promise<T>;
    get<T>(endpoint: string, headers?: Record<string, string>): Promise<T>;
    post<T>(endpoint: string, data?: any, headers?: Record<string, string>): Promise<T>;
    put<T>(endpoint: string, data?: any, headers?: Record<string, string>): Promise<T>;
    delete<T>(endpoint: string, headers?: Record<string, string>): Promise<T>;
};
//# sourceMappingURL=api.d.ts.map