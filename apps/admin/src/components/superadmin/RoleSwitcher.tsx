'use client';

import { ChevronDown, RefreshCw, Shield, User } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { apiFetch } from '@/lib/api';
import { tokenManager } from '@/services/api';

interface AvailableRole {
  role: string;
  name: string;
  description: string;
}

interface CurrentRoleResponse {
  current_role: string;
  is_switched: boolean;
  original_role?: string;
  expires_at?: string;
  time_remaining_minutes?: number;
}

interface AvailableRolesResponse {
  available_roles: AvailableRole[];
  current_role: string;
}

/**
 * RoleSwitcher - Super Admin role switching dropdown
 *
 * Allows SUPER_ADMIN users to temporarily switch to other roles
 * to test and experience the UI as that role would see it.
 *
 * DEV MODE ONLY - Backend validates this.
 * Only makes API calls when NEXT_PUBLIC_DEV_MODE is enabled.
 */
export default function RoleSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [availableRoles, setAvailableRoles] = useState<AvailableRole[]>([]);
  const [currentRoleInfo, setCurrentRoleInfo] =
    useState<CurrentRoleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Check if dev mode is enabled (skip API calls in production)
  const isDevModeEnabled = process.env.NEXT_PUBLIC_DEV_MODE === 'true';

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch available roles and current role status on mount (only in dev mode)
  useEffect(() => {
    if (isDevModeEnabled) {
      fetchRoleInfo();
    }
  }, [isDevModeEnabled]);

  // Don't render anything if dev mode is disabled
  if (!isDevModeEnabled) {
    return null;
  }

  const fetchRoleInfo = async () => {
    try {
      const token = tokenManager.getToken();
      if (!token) return;

      const [rolesRes, currentRes] = await Promise.all([
        apiFetch<AvailableRolesResponse>('/api/v1/dev/available-roles', {
          headers: { Authorization: `Bearer ${token}` },
        }),
        apiFetch<CurrentRoleResponse>('/api/v1/dev/current-role', {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (rolesRes.success && rolesRes.data) {
        setAvailableRoles(rolesRes.data.available_roles || []);
      }

      if (currentRes.success && currentRes.data) {
        setCurrentRoleInfo(currentRes.data);
      }
    } catch (err) {
      console.log('Role switching not available (likely production mode)');
    }
  };

  const handleSwitchRole = async (targetRole: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const token = tokenManager.getToken();
      if (!token) throw new Error('Not authenticated');

      const response = await apiFetch<{ success: boolean; message: string }>(
        '/api/v1/dev/switch-role',
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            target_role: targetRole,
            duration_minutes: 60,
          }),
        }
      );

      if (response.success) {
        // Refresh role info
        await fetchRoleInfo();
        setIsOpen(false);
        // Reload the page to apply new role context
        window.location.reload();
      } else {
        setError(response.error || 'Failed to switch role');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch role');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestoreRole = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = tokenManager.getToken();
      if (!token) throw new Error('Not authenticated');

      const response = await apiFetch<{ success: boolean; message: string }>(
        '/api/v1/dev/restore-role',
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.success) {
        await fetchRoleInfo();
        setIsOpen(false);
        // Reload the page to apply restored role
        window.location.reload();
      } else {
        setError(response.error || 'Failed to restore role');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restore role');
    } finally {
      setIsLoading(false);
    }
  };

  // Don't render if no roles available (production mode or not super admin)
  if (availableRoles.length === 0) {
    return null;
  }

  const isSwitched = currentRoleInfo?.is_switched;
  const timeRemaining = currentRoleInfo?.time_remaining_minutes;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors
          ${
            isSwitched
              ? 'bg-amber-100 text-amber-800 border border-amber-300'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }
        `}
        title={
          isSwitched
            ? `Viewing as ${currentRoleInfo?.current_role}`
            : 'Switch Role (Dev Mode)'
        }
      >
        {isSwitched ? (
          <>
            <User className="w-4 h-4" />
            <span className="hidden sm:inline">
              {currentRoleInfo?.current_role?.replace('_', ' ')}
            </span>
            {timeRemaining && (
              <span className="text-xs text-amber-600">({timeRemaining}m)</span>
            )}
          </>
        ) : (
          <>
            <Shield className="w-4 h-4" />
            <span className="hidden sm:inline">Switch Role</span>
          </>
        )}
        <ChevronDown
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
            <p className="text-sm font-semibold text-gray-900">
              🛠️ Role Switcher (Dev Mode)
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Temporarily view the admin panel as a different role
            </p>
          </div>

          {error && (
            <div className="px-4 py-2 bg-red-50 text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Restore Button (if switched) */}
          {isSwitched && (
            <button
              onClick={handleRestoreRole}
              disabled={isLoading}
              className="w-full flex items-center px-4 py-3 text-sm text-green-700 bg-green-50 hover:bg-green-100 border-b border-green-100 transition-colors"
            >
              <RefreshCw
                className={`w-4 h-4 mr-3 ${isLoading ? 'animate-spin' : ''}`}
              />
              <div className="text-left">
                <div className="font-medium">Restore Super Admin</div>
                <div className="text-xs text-green-600">
                  Return to your original role
                </div>
              </div>
            </button>
          )}

          {/* Available Roles */}
          <div className="py-2">
            {availableRoles.map(role => (
              <button
                key={role.role}
                onClick={() => handleSwitchRole(role.role)}
                disabled={
                  isLoading || currentRoleInfo?.current_role === role.role
                }
                className={`
                  w-full flex items-center px-4 py-3 text-sm transition-colors text-left
                  ${
                    currentRoleInfo?.current_role === role.role
                      ? 'bg-blue-50 text-blue-700 cursor-default'
                      : 'text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <User className="w-4 h-4 mr-3 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="font-medium flex items-center">
                    {role.name}
                    {currentRoleInfo?.current_role === role.role && (
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                        Current
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {role.description}
                  </div>
                </div>
              </button>
            ))}
          </div>

          <div className="px-4 py-2 border-t border-gray-100 bg-gray-50">
            <p className="text-xs text-gray-400 text-center">
              ⚠️ Development feature only
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
