export const auth = {
    getToken() {
        if (typeof window === 'undefined')
            return null;
        return localStorage.getItem('auth_token');
    },
    setToken(token) {
        if (typeof window === 'undefined')
            return;
        localStorage.setItem('auth_token', token);
    },
    removeToken() {
        if (typeof window === 'undefined')
            return;
        localStorage.removeItem('auth_token');
    },
    isAuthenticated() {
        return !!this.getToken();
    },
    getAuthHeaders() {
        const token = this.getToken();
        return token ? { Authorization: `Bearer ${token}` } : {};
    },
};
//# sourceMappingURL=auth.js.map