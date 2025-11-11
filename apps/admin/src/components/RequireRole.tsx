/**
 * RequireRole Component
 *
 * Conditional rendering component for role-based access control.
 * Shows children only if the user has one of the required roles.
 *
 * @example
 * ```tsx
 * // Show delete button only to admins and customer support
 * <RequireRole roles={['SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT']}>
 *   <button onClick={handleDelete}>Delete Booking</button>
 * </RequireRole>
 *
 * // Show analytics only to super admins
 * <RequireRole roles={['SUPER_ADMIN']}>
 *   <AnalyticsDashboard />
 * </RequireRole>
 *
 * // Show fallback when user doesn't have permission
 * <RequireRole
 *   roles={['ADMIN', 'SUPER_ADMIN']}
 *   fallback={<p>You need admin access to view this content.</p>}
 * >
 *   <AdminPanel />
 * </RequireRole>
 * ```
 */

import React from 'react';

import { usePermissions, UserRole } from '../hooks/usePermissions';

interface RequireRoleProps {
  /** Required roles (at least one must match) */
  roles: UserRole[] | UserRole;

  /** Content to show when user has permission */
  children: React.ReactNode;

  /** Optional content to show when user doesn't have permission */
  fallback?: React.ReactNode;

  /** If true, show nothing instead of fallback when unauthorized (default: false) */
  hideOnUnauthorized?: boolean;
}

/**
 * RequireRole Component
 *
 * Renders children only if the current user has one of the specified roles.
 * Optionally renders a fallback component for unauthorized users.
 */
export const RequireRole: React.FC<RequireRoleProps> = ({
  roles,
  children,
  fallback = null,
  hideOnUnauthorized = false,
}) => {
  const permissions = usePermissions();

  // Normalize roles to array
  const rolesArray = Array.isArray(roles) ? roles : [roles];

  // Check if user has any of the required roles
  const hasRequiredRole = permissions.hasAnyRole(rolesArray);

  // Render based on permission
  if (hasRequiredRole) {
    return <>{children}</>;
  }

  // Show fallback or nothing
  if (hideOnUnauthorized) {
    return null;
  }

  return <>{fallback}</>;
};

export default RequireRole;
