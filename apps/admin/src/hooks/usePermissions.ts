/**
 * usePermissions Hook
 *
 * Custom React hook for checking user permissions based on role.
 * Provides boolean flags for all 24 granular permissions across the system.
 *
 * @example
 * ```tsx
 * function BookingManagement() {
 *   const permissions = usePermissions();
 *
 *   return (
 *     <div>
 *       {permissions.canViewBookings && <BookingList />}
 *       {permissions.canDeleteBooking && <DeleteButton />}
 *       {permissions.canAccessFinancialReports && <ReportsLink />}
 *     </div>
 *   );
 * }
 * ```
 */

import { useMemo } from 'react';

import { useAuth } from '../contexts/AuthContext'; // Adjust import path as needed

/**
 * User roles in the system (matches backend UserRole enum)
 */
export enum UserRole {
  SUPER_ADMIN = 'SUPER_ADMIN',
  ADMIN = 'ADMIN',
  CUSTOMER_SUPPORT = 'CUSTOMER_SUPPORT',
  STATION_MANAGER = 'STATION_MANAGER',
}

/**
 * Permission definitions matching backend Permission class
 * Each permission maps to the roles that have access
 */
const PERMISSIONS = {
  // Booking Permissions (5)
  BOOKING_VIEW_ALL: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  BOOKING_CREATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  BOOKING_UPDATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  BOOKING_DELETE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  BOOKING_VIEW_STATION: [UserRole.STATION_MANAGER],

  // Customer Permissions (4)
  CUSTOMER_VIEW: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  CUSTOMER_CREATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  CUSTOMER_UPDATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  CUSTOMER_DELETE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],

  // Lead Permissions (3)
  LEAD_VIEW: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
  LEAD_MANAGE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  LEAD_DELETE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],

  // Review Permissions (3)
  REVIEW_VIEW: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  REVIEW_MODERATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  REVIEW_DELETE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],

  // Chef Permissions (4)
  CHEF_VIEW_ALL: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  CHEF_VIEW_STATION: [UserRole.STATION_MANAGER],
  CHEF_ASSIGN: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER],
  CHEF_SCHEDULE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.STATION_MANAGER,
  ],

  // Station Permissions (5)
  STATION_VIEW_ALL: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  STATION_VIEW_OWN: [UserRole.STATION_MANAGER],
  STATION_MANAGE: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  STATION_MANAGE_OWN: [UserRole.STATION_MANAGER],
  STATION_DELETE: [UserRole.SUPER_ADMIN],

  // Admin Permissions (5)
  ADMIN_VIEW: [UserRole.SUPER_ADMIN],
  ADMIN_CREATE: [UserRole.SUPER_ADMIN],
  ADMIN_UPDATE: [UserRole.SUPER_ADMIN],
  ADMIN_DELETE: [UserRole.SUPER_ADMIN],
  ADMIN_ASSIGN_ROLES: [UserRole.SUPER_ADMIN],

  // Financial Permissions (3)
  FINANCIAL_VIEW: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  FINANCIAL_REFUND: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  FINANCIAL_REPORTS: [UserRole.SUPER_ADMIN, UserRole.ADMIN],

  // Audit Permissions (3)
  AUDIT_VIEW_ALL: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  AUDIT_VIEW_OWN: [UserRole.CUSTOMER_SUPPORT, UserRole.STATION_MANAGER],
  AUDIT_EXPORT: [UserRole.SUPER_ADMIN, UserRole.ADMIN],

  // System Permissions (3)
  SYSTEM_SETTINGS: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  SYSTEM_ANALYTICS: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  SYSTEM_ANALYTICS_STATION: [UserRole.STATION_MANAGER],
} as const;

/**
 * Permission flags returned by the hook
 */
export interface Permissions {
  // Meta
  role: UserRole | null;
  isAuthenticated: boolean;

  // Booking Permissions
  canViewAllBookings: boolean;
  canCreateBooking: boolean;
  canUpdateBooking: boolean;
  canDeleteBooking: boolean;
  canViewStationBookings: boolean;

  // Customer Permissions
  canViewCustomers: boolean;
  canCreateCustomer: boolean;
  canUpdateCustomer: boolean;
  canDeleteCustomer: boolean;

  // Lead Permissions
  canViewLeads: boolean;
  canManageLeads: boolean;
  canDeleteLead: boolean;

  // Review Permissions
  canViewReviews: boolean;
  canModerateReviews: boolean;
  canDeleteReview: boolean;

  // Chef Permissions
  canViewAllChefs: boolean;
  canViewStationChefs: boolean;
  canAssignChef: boolean;
  canScheduleChef: boolean;

  // Station Permissions
  canViewAllStations: boolean;
  canViewOwnStation: boolean;
  canManageStations: boolean;
  canManageOwnStation: boolean;
  canDeleteStation: boolean;

  // Admin Permissions
  canViewAdmins: boolean;
  canCreateAdmin: boolean;
  canUpdateAdmin: boolean;
  canDeleteAdmin: boolean;
  canAssignRoles: boolean;

  // Financial Permissions
  canViewFinancials: boolean;
  canProcessRefund: boolean;
  canAccessFinancialReports: boolean;

  // Audit Permissions
  canViewAllAuditLogs: boolean;
  canViewOwnAuditLogs: boolean;
  canExportAuditLogs: boolean;

  // System Permissions
  canAccessSystemSettings: boolean;
  canAccessSystemAnalytics: boolean;
  canAccessStationAnalytics: boolean;

  // Helper methods
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
  isAdmin: boolean;
  isSuperAdmin: boolean;
  isCustomerSupport: boolean;
  isStationManager: boolean;
}

/**
 * Check if user role has a specific permission
 */
function hasPermission(
  userRole: UserRole | null,
  allowedRoles: readonly UserRole[]
): boolean {
  if (!userRole) return false;
  return allowedRoles.includes(userRole);
}

/**
 * Map legacy role strings to UserRole enum
 */
function normalizeRole(role: string | null | undefined): UserRole | null {
  if (!role) return null;

  // Handle legacy role names
  const roleMap: Record<string, UserRole> = {
    superadmin: UserRole.SUPER_ADMIN,
    admin: UserRole.ADMIN,
    staff: UserRole.CUSTOMER_SUPPORT,
    support: UserRole.CUSTOMER_SUPPORT,
    manager: UserRole.STATION_MANAGER,
    // New role names (already uppercase)
    SUPER_ADMIN: UserRole.SUPER_ADMIN,
    ADMIN: UserRole.ADMIN,
    CUSTOMER_SUPPORT: UserRole.CUSTOMER_SUPPORT,
    STATION_MANAGER: UserRole.STATION_MANAGER,
  };

  return roleMap[role] || null;
}

/**
 * usePermissions Hook
 *
 * Returns an object with all permission flags based on the current user's role.
 * Automatically updates when user logs in/out or role changes.
 *
 * @returns {Permissions} Object with permission flags and helper methods
 */
export function usePermissions(): Permissions {
  // Get current user from auth context
  const { stationContext, isAuthenticated } = useAuth();

  // Extract role from stationContext
  // @ts-expect-error - stationContext may have role property
  const rawRole = stationContext?.role || stationContext?.user_role || null;

  // Normalize role from stationContext
  const userRole = useMemo(() => {
    return normalizeRole(rawRole);
  }, [rawRole]);

  // Compute all permissions
  const permissions = useMemo<Permissions>(() => {
    // Helper methods
    const hasRole = (role: UserRole): boolean => userRole === role;
    const hasAnyRole = (roles: UserRole[]): boolean =>
      userRole ? roles.includes(userRole) : false;

    return {
      // Meta
      role: userRole,
      isAuthenticated: isAuthenticated && userRole !== null,

      // Booking Permissions
      canViewAllBookings: hasPermission(userRole, PERMISSIONS.BOOKING_VIEW_ALL),
      canCreateBooking: hasPermission(userRole, PERMISSIONS.BOOKING_CREATE),
      canUpdateBooking: hasPermission(userRole, PERMISSIONS.BOOKING_UPDATE),
      canDeleteBooking: hasPermission(userRole, PERMISSIONS.BOOKING_DELETE),
      canViewStationBookings: hasPermission(
        userRole,
        PERMISSIONS.BOOKING_VIEW_STATION
      ),

      // Customer Permissions
      canViewCustomers: hasPermission(userRole, PERMISSIONS.CUSTOMER_VIEW),
      canCreateCustomer: hasPermission(userRole, PERMISSIONS.CUSTOMER_CREATE),
      canUpdateCustomer: hasPermission(userRole, PERMISSIONS.CUSTOMER_UPDATE),
      canDeleteCustomer: hasPermission(userRole, PERMISSIONS.CUSTOMER_DELETE),

      // Lead Permissions
      canViewLeads: hasPermission(userRole, PERMISSIONS.LEAD_VIEW),
      canManageLeads: hasPermission(userRole, PERMISSIONS.LEAD_MANAGE),
      canDeleteLead: hasPermission(userRole, PERMISSIONS.LEAD_DELETE),

      // Review Permissions
      canViewReviews: hasPermission(userRole, PERMISSIONS.REVIEW_VIEW),
      canModerateReviews: hasPermission(userRole, PERMISSIONS.REVIEW_MODERATE),
      canDeleteReview: hasPermission(userRole, PERMISSIONS.REVIEW_DELETE),

      // Chef Permissions
      canViewAllChefs: hasPermission(userRole, PERMISSIONS.CHEF_VIEW_ALL),
      canViewStationChefs: hasPermission(
        userRole,
        PERMISSIONS.CHEF_VIEW_STATION
      ),
      canAssignChef: hasPermission(userRole, PERMISSIONS.CHEF_ASSIGN),
      canScheduleChef: hasPermission(userRole, PERMISSIONS.CHEF_SCHEDULE),

      // Station Permissions
      canViewAllStations: hasPermission(userRole, PERMISSIONS.STATION_VIEW_ALL),
      canViewOwnStation: hasPermission(userRole, PERMISSIONS.STATION_VIEW_OWN),
      canManageStations: hasPermission(userRole, PERMISSIONS.STATION_MANAGE),
      canManageOwnStation: hasPermission(
        userRole,
        PERMISSIONS.STATION_MANAGE_OWN
      ),
      canDeleteStation: hasPermission(userRole, PERMISSIONS.STATION_DELETE),

      // Admin Permissions
      canViewAdmins: hasPermission(userRole, PERMISSIONS.ADMIN_VIEW),
      canCreateAdmin: hasPermission(userRole, PERMISSIONS.ADMIN_CREATE),
      canUpdateAdmin: hasPermission(userRole, PERMISSIONS.ADMIN_UPDATE),
      canDeleteAdmin: hasPermission(userRole, PERMISSIONS.ADMIN_DELETE),
      canAssignRoles: hasPermission(userRole, PERMISSIONS.ADMIN_ASSIGN_ROLES),

      // Financial Permissions
      canViewFinancials: hasPermission(userRole, PERMISSIONS.FINANCIAL_VIEW),
      canProcessRefund: hasPermission(userRole, PERMISSIONS.FINANCIAL_REFUND),
      canAccessFinancialReports: hasPermission(
        userRole,
        PERMISSIONS.FINANCIAL_REPORTS
      ),

      // Audit Permissions
      canViewAllAuditLogs: hasPermission(userRole, PERMISSIONS.AUDIT_VIEW_ALL),
      canViewOwnAuditLogs: hasPermission(userRole, PERMISSIONS.AUDIT_VIEW_OWN),
      canExportAuditLogs: hasPermission(userRole, PERMISSIONS.AUDIT_EXPORT),

      // System Permissions
      canAccessSystemSettings: hasPermission(
        userRole,
        PERMISSIONS.SYSTEM_SETTINGS
      ),
      canAccessSystemAnalytics: hasPermission(
        userRole,
        PERMISSIONS.SYSTEM_ANALYTICS
      ),
      canAccessStationAnalytics: hasPermission(
        userRole,
        PERMISSIONS.SYSTEM_ANALYTICS_STATION
      ),

      // Helper methods
      hasRole,
      hasAnyRole,
      isAdmin: userRole === UserRole.ADMIN,
      isSuperAdmin: userRole === UserRole.SUPER_ADMIN,
      isCustomerSupport: userRole === UserRole.CUSTOMER_SUPPORT,
      isStationManager: userRole === UserRole.STATION_MANAGER,
    };
  }, [userRole, isAuthenticated]);

  return permissions;
}

export default usePermissions;
