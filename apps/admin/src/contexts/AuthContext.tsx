'use client';

import { usePathname, useRouter } from 'next/navigation';
import { createContext, useContext, useEffect, useState } from 'react';

import type { StationContext } from '@/services/api';
import { tokenManager } from '@/services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  stationContext: StationContext | null;
  login: (
    token: string,
    stationContext?: StationContext,
    refreshToken?: string
  ) => void;
  logout: () => void;
  loading: boolean;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  isSuperAdmin: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [stationContext, setStationContext] = useState<StationContext | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Check for token and station context in localStorage on component mount
    const storedToken = tokenManager.getToken();
    const storedStationContext = tokenManager.getStationContext();

    if (storedToken) {
      setToken(storedToken);
      setStationContext(storedStationContext);
      setIsAuthenticated(true);
    } else if (pathname !== '/login' && !pathname.startsWith('/auth/')) {
      // Redirect to login if no token and not already on login or auth callback page
      // Note: /auth/callback handles OAuth token from URL params before storing to localStorage
      router.push('/login');
    }

    setLoading(false);
  }, [pathname, router]);

  const login = (
    newToken: string,
    newStationContext?: StationContext,
    refreshToken?: string
  ) => {
    tokenManager.setToken(newToken);
    setToken(newToken);
    setIsAuthenticated(true);

    // Store refresh token if provided (critical for token refresh to work)
    if (refreshToken) {
      tokenManager.setRefreshToken(refreshToken);
      console.log('[AuthContext] Refresh token stored');
    }

    if (newStationContext) {
      tokenManager.setStationContext(newStationContext);
      setStationContext(newStationContext);
    }
  };

  const logout = () => {
    tokenManager.removeToken();
    tokenManager.removeStationContext();
    setToken(null);
    setStationContext(null);
    setIsAuthenticated(false);
    router.push('/login');
  };

  const hasPermission = (permission: string): boolean => {
    if (!stationContext) return false;

    // Super admin has all permissions
    if (stationContext.is_super_admin) return true;

    return stationContext.permissions.includes(permission);
  };

  const hasRole = (role: string): boolean => {
    if (!stationContext) return false;
    return stationContext.role === role;
  };

  const isSuperAdmin = (): boolean => {
    return stationContext?.is_super_admin || false;
  };

  // Allow access to login page and auth callback pages without authentication
  // These pages handle their own auth flow (login form, OAuth callback)
  const isPublicAuthPage =
    pathname === '/login' || pathname.startsWith('/auth/');

  // Show loading spinner while checking authentication (skip for public auth pages)
  if (loading && !isPublicAuthPage) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Allow access to login and auth callback pages without authentication
  if (isPublicAuthPage) {
    return (
      <AuthContext.Provider
        value={{
          isAuthenticated,
          token,
          stationContext,
          login,
          logout,
          loading,
          hasPermission,
          hasRole,
          isSuperAdmin,
        }}
      >
        {children}
      </AuthContext.Provider>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        token,
        stationContext,
        login,
        logout,
        loading,
        hasPermission,
        hasRole,
        isSuperAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
