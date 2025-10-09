const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const api = {
    baseURL: API_BASE_URL,
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const defaultHeaders = {
            'Content-Type': 'application/json',
        };
        const config = {
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
        return response.json();
    },
    get(endpoint, headers) {
        const requestHeaders = headers || {};
        return this.request(endpoint, { method: 'GET', headers: requestHeaders });
    },
    post(endpoint, data, headers) {
        const requestHeaders = headers || {};
        const requestOptions = {
            method: 'POST',
            headers: requestHeaders,
        };
        if (data) {
            requestOptions.body = JSON.stringify(data);
        }
        return this.request(endpoint, requestOptions);
    },
    put(endpoint, data, headers) {
        const requestHeaders = headers || {};
        const requestOptions = {
            method: 'PUT',
            headers: requestHeaders,
        };
        if (data) {
            requestOptions.body = JSON.stringify(data);
        }
        return this.request(endpoint, requestOptions);
    },
    delete(endpoint, headers) {
        const requestHeaders = headers || {};
        return this.request(endpoint, { method: 'DELETE', headers: requestHeaders });
    },
};
//# sourceMappingURL=api.js.map