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
 * Aligned with My Hibachi Business Model (CORRECTED):
 *
 * Role Hierarchy:
 * - SUPER_ADMIN: Full system access - manage all stations, admins, settings
 *   Can create/delete: ALL account types
 *
 * - ADMIN: Access ASSIGNED stations (multiple possible, assigned by SUPER_ADMIN)
 *   Full CRUD for bookings, customers, chefs in assigned stations
 *   Can create/delete: STATION_MANAGER and CHEF accounts for assigned stations
 *   CANNOT manage other ADMIN or SUPER_ADMIN accounts
 *
 * - CUSTOMER_SUPPORT: ALL customer-related operations
 *   Can VIEW and EDIT bookings directly (no approval needed for edits)
 *   DELETE bookings requires approval from ADMIN or SUPER_ADMIN
 *   Full access to customer, lead, review, complaint features
 *   No user account management
 *
 * - STATION_MANAGER: View-only access to their assigned station
 *   Schedule internal chefs for their station
 *   Can create/delete: CHEF accounts for their station ONLY
 *   NO booking adjustments
 *
 * - CHEF (Future - Backend ready, UI pending):
 *   View their own schedule, update availability
 */
const PERMISSIONS = {
  // ========== BOOKING PERMISSIONS ==========
  BOOKING_VIEW_ALL: [UserRole.SUPER_ADMIN], // Platform-wide view
  BOOKING_VIEW_ASSIGNED: [UserRole.ADMIN], // Assigned stations only
  BOOKING_VIEW_STATION: [UserRole.CUSTOMER_SUPPORT, UserRole.STATION_MANAGER], // Station-scoped
  BOOKING_CREATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  BOOKING_UPDATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ], // CS can edit directly
  BOOKING_DELETE: [UserRole.SUPER_ADMIN, UserRole.ADMIN], // Direct delete (no approval)
  BOOKING_DELETE_WITH_APPROVAL: [UserRole.CUSTOMER_SUPPORT], // CS needs approval for delete only

  // ========== CUSTOMER PERMISSIONS ==========
  // CUSTOMER_SUPPORT has FULL access to all customer-related features
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
  ], // CS can delete

  // ========== LEAD PERMISSIONS ==========
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
  ], // CS can delete

  // ========== REVIEW PERMISSIONS ==========
  REVIEW_VIEW: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  REVIEW_MANAGE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ], // Respond to reviews
  REVIEW_MODERATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ], // Approve/flag
  REVIEW_DELETE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ], // CS can delete

  // ========== COMPLAINT PERMISSIONS ==========
  COMPLAINT_VIEW: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  COMPLAINT_MANAGE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],
  COMPLAINT_RESOLVE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
  ],

  // ========== CHEF PERMISSIONS ==========
  CHEF_VIEW_ALL: [UserRole.SUPER_ADMIN], // Platform-wide chef view
  CHEF_VIEW_ASSIGNED: [UserRole.ADMIN], // Chefs in assigned stations
  CHEF_VIEW_STATION: [UserRole.STATION_MANAGER], // Own station's chefs only
  CHEF_MANAGE: [UserRole.SUPER_ADMIN, UserRole.ADMIN], // CRUD operations on chefs
  CHEF_ASSIGN: [UserRole.SUPER_ADMIN, UserRole.ADMIN], // Assign chefs to bookings
  CHEF_SCHEDULE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.STATION_MANAGER,
  ], // Schedule chefs
  CHEF_ACCOUNT_CREATE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.STATION_MANAGER,
  ], // Create chef accounts
  CHEF_ACCOUNT_DELETE: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.STATION_MANAGER,
  ], // Delete chef accounts

  // ========== STATION MANAGER ACCOUNT PERMISSIONS ==========
  STATION_MANAGER_VIEW: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  STATION_MANAGER_CREATE: [UserRole.SUPER_ADMIN, UserRole.ADMIN], // ADMIN can create for assigned stations
  STATION_MANAGER_DELETE: [UserRole.SUPER_ADMIN, UserRole.ADMIN], // ADMIN can delete for assigned stations

  // ========== STATION PERMISSIONS ==========
  STATION_VIEW_ALL: [UserRole.SUPER_ADMIN],
  STATION_VIEW_ASSIGNED: [UserRole.ADMIN], // Multiple assigned stations
  STATION_VIEW_OWN: [UserRole.STATION_MANAGER], // Single assigned station
  STATION_CREATE: [UserRole.SUPER_ADMIN], // Only SUPER_ADMIN
  STATION_MANAGE: [UserRole.SUPER_ADMIN], // Create/delete stations
  STATION_MANAGE_ASSIGNED: [UserRole.ADMIN], // Edit assigned station settings
  STATION_DELETE: [UserRole.SUPER_ADMIN], // Only SUPER_ADMIN

  // ========== USER ACCOUNT PERMISSIONS ==========
  // Super Admin account management (SUPER_ADMIN only)
  SUPER_ADMIN_VIEW: [UserRole.SUPER_ADMIN],
  SUPER_ADMIN_CREATE: [UserRole.SUPER_ADMIN],
  SUPER_ADMIN_DELETE: [UserRole.SUPER_ADMIN],

  // Admin account management (SUPER_ADMIN only)
  ADMIN_VIEW: [UserRole.SUPER_ADMIN],
  ADMIN_CREATE: [UserRole.SUPER_ADMIN],
  ADMIN_UPDATE: [UserRole.SUPER_ADMIN],
  ADMIN_DELETE: [UserRole.SUPER_ADMIN],
  ADMIN_ASSIGN_STATIONS: [UserRole.SUPER_ADMIN], // Assign stations to admins

  // Customer Support account management (SUPER_ADMIN only)
  CUSTOMER_SUPPORT_VIEW: [UserRole.SUPER_ADMIN],
  CUSTOMER_SUPPORT_CREATE: [UserRole.SUPER_ADMIN],
  CUSTOMER_SUPPORT_DELETE: [UserRole.SUPER_ADMIN],

  // ========== FINANCIAL PERMISSIONS ==========
  FINANCIAL_VIEW_ALL: [UserRole.SUPER_ADMIN],
  FINANCIAL_VIEW_ASSIGNED: [UserRole.ADMIN], // Assigned stations only
  FINANCIAL_REFUND: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  FINANCIAL_REPORTS: [UserRole.SUPER_ADMIN, UserRole.ADMIN],

  // ========== AUDIT PERMISSIONS ==========
  AUDIT_VIEW_ALL: [UserRole.SUPER_ADMIN],
  AUDIT_VIEW_ASSIGNED: [UserRole.ADMIN], // Assigned stations audit
  AUDIT_VIEW_OWN: [UserRole.CUSTOMER_SUPPORT, UserRole.STATION_MANAGER],
  AUDIT_EXPORT: [UserRole.SUPER_ADMIN, UserRole.ADMIN],

  // ========== SYSTEM PERMISSIONS ==========
  SYSTEM_SETTINGS: [UserRole.SUPER_ADMIN], // Only SUPER_ADMIN for system settings
  SYSTEM_ANALYTICS_ALL: [UserRole.SUPER_ADMIN],
  SYSTEM_ANALYTICS_ASSIGNED: [UserRole.ADMIN], // Assigned stations analytics
  SYSTEM_ANALYTICS_STATION: [UserRole.STATION_MANAGER], // Single station analytics

  // ========== APPROVAL WORKFLOW PERMISSIONS ==========
  APPROVAL_GRANT: [UserRole.SUPER_ADMIN, UserRole.ADMIN], // Can approve/reject delete requests
  APPROVAL_REQUEST: [UserRole.CUSTOMER_SUPPORT], // Can request approval for delete
} as const;

/**
 * Permission flags returned by the hook
 * Aligned with My Hibachi Business Model (CORRECTED)
 */
export interface Permissions {
  // Meta
  role: UserRole | null;
  isAuthenticated: boolean;

  // Booking Permissions
  canViewAllBookings: boolean; // SUPER_ADMIN only
  canViewAssignedBookings: boolean; // ADMIN (assigned stations)
  canViewStationBookings: boolean; // CUSTOMER_SUPPORT, STATION_MANAGER
  canCreateBooking: boolean;
  canUpdateBooking: boolean; // SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT (direct)
  canDeleteBooking: boolean; // SUPER_ADMIN, ADMIN (direct)
  canDeleteBookingWithApproval: boolean; // CUSTOMER_SUPPORT (needs approval for delete only)

  // Customer Permissions (CUSTOMER_SUPPORT has FULL access)
  canViewCustomers: boolean;
  canCreateCustomer: boolean;
  canUpdateCustomer: boolean;
  canDeleteCustomer: boolean; // CS can now delete

  // Lead Permissions (CUSTOMER_SUPPORT has FULL access)
  canViewLeads: boolean;
  canManageLeads: boolean;
  canDeleteLead: boolean; // CS can now delete

  // Review Permissions (CUSTOMER_SUPPORT has FULL access)
  canViewReviews: boolean;
  canManageReviews: boolean; // Respond to reviews
  canModerateReviews: boolean; // Approve/flag reviews
  canDeleteReview: boolean; // CS can now delete

  // Complaint Permissions (CUSTOMER_SUPPORT specialty)
  canViewComplaints: boolean;
  canManageComplaints: boolean;
  canResolveComplaints: boolean;

  // Chef Permissions
  canViewAllChefs: boolean; // SUPER_ADMIN only
  canViewAssignedChefs: boolean; // ADMIN (assigned stations)
  canViewStationChefs: boolean; // STATION_MANAGER
  canManageChefs: boolean; // SUPER_ADMIN, ADMIN
  canAssignChef: boolean; // SUPER_ADMIN, ADMIN
  canScheduleChef: boolean; // SUPER_ADMIN, ADMIN, STATION_MANAGER
  canCreateChefAccount: boolean; // SUPER_ADMIN, ADMIN, STATION_MANAGER
  canDeleteChefAccount: boolean; // SUPER_ADMIN, ADMIN, STATION_MANAGER

  // Station Manager Account Permissions
  canViewStationManagers: boolean; // SUPER_ADMIN, ADMIN
  canCreateStationManager: boolean; // SUPER_ADMIN, ADMIN
  canDeleteStationManager: boolean; // SUPER_ADMIN, ADMIN

  // Station Permissions
  canViewAllStations: boolean; // SUPER_ADMIN only
  canViewAssignedStations: boolean; // ADMIN (multiple assigned)
  canViewOwnStation: boolean; // STATION_MANAGER (single)
  canCreateStation: boolean; // SUPER_ADMIN only
  canManageStations: boolean; // SUPER_ADMIN only
  canManageAssignedStations: boolean; // ADMIN (edit assigned)
  canDeleteStation: boolean; // SUPER_ADMIN only

  // User Account Permissions
  canViewSuperAdmins: boolean;
  canCreateSuperAdmin: boolean;
  canDeleteSuperAdmin: boolean;
  canViewAdmins: boolean;
  canCreateAdmin: boolean;
  canUpdateAdmin: boolean;
  canDeleteAdmin: boolean;
  canAssignStationsToAdmin: boolean;
  canViewCustomerSupport: boolean;
  canCreateCustomerSupport: boolean;
  canDeleteCustomerSupport: boolean;

  // Financial Permissions
  canViewAllFinancials: boolean; // SUPER_ADMIN only
  canViewAssignedFinancials: boolean; // ADMIN (assigned stations)
  canProcessRefund: boolean;
  canAccessFinancialReports: boolean;

  // Audit Permissions
  canViewAllAuditLogs: boolean; // SUPER_ADMIN only
  canViewAssignedAuditLogs: boolean; // ADMIN (assigned stations)
  canViewOwnAuditLogs: boolean; // CUSTOMER_SUPPORT, STATION_MANAGER
  canExportAuditLogs: boolean;

  // System Permissions
  canAccessSystemSettings: boolean; // SUPER_ADMIN only
  canAccessAllAnalytics: boolean; // SUPER_ADMIN only
  canAccessAssignedAnalytics: boolean; // ADMIN (assigned stations)
  canAccessStationAnalytics: boolean; // STATION_MANAGER

  // Approval Workflow Permissions
  canGrantApproval: boolean; // SUPER_ADMIN, ADMIN (approve CS delete requests)
  canRequestApproval: boolean; // CUSTOMER_SUPPORT (request approval for delete)

  // Helper methods
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
  isAdmin: boolean;
  isSuperAdmin: boolean;
  isCustomerSupport: boolean;
  isStationManager: boolean;

  // Business logic helpers
  needsApprovalForBookingDelete: boolean; // True for CUSTOMER_SUPPORT (delete only)
  isAssignmentScoped: boolean; // True for ADMIN (multi-station via assignment)
  isStationScoped: boolean; // True for STATION_MANAGER (single station)
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
      canViewAssignedBookings: hasPermission(
        userRole,
        PERMISSIONS.BOOKING_VIEW_ASSIGNED
      ),
      canViewStationBookings: hasPermission(
        userRole,
        PERMISSIONS.BOOKING_VIEW_STATION
      ),
      canCreateBooking: hasPermission(userRole, PERMISSIONS.BOOKING_CREATE),
      canUpdateBooking: hasPermission(userRole, PERMISSIONS.BOOKING_UPDATE),
      canDeleteBooking: hasPermission(userRole, PERMISSIONS.BOOKING_DELETE),
      canDeleteBookingWithApproval: hasPermission(
        userRole,
        PERMISSIONS.BOOKING_DELETE_WITH_APPROVAL
      ),

      // Customer Permissions (CUSTOMER_SUPPORT has FULL access)
      canViewCustomers: hasPermission(userRole, PERMISSIONS.CUSTOMER_VIEW),
      canCreateCustomer: hasPermission(userRole, PERMISSIONS.CUSTOMER_CREATE),
      canUpdateCustomer: hasPermission(userRole, PERMISSIONS.CUSTOMER_UPDATE),
      canDeleteCustomer: hasPermission(userRole, PERMISSIONS.CUSTOMER_DELETE),

      // Lead Permissions (CUSTOMER_SUPPORT has FULL access)
      canViewLeads: hasPermission(userRole, PERMISSIONS.LEAD_VIEW),
      canManageLeads: hasPermission(userRole, PERMISSIONS.LEAD_MANAGE),
      canDeleteLead: hasPermission(userRole, PERMISSIONS.LEAD_DELETE),

      // Review Permissions (CUSTOMER_SUPPORT has FULL access)
      canViewReviews: hasPermission(userRole, PERMISSIONS.REVIEW_VIEW),
      canManageReviews: hasPermission(userRole, PERMISSIONS.REVIEW_MANAGE),
      canModerateReviews: hasPermission(userRole, PERMISSIONS.REVIEW_MODERATE),
      canDeleteReview: hasPermission(userRole, PERMISSIONS.REVIEW_DELETE),

      // Complaint Permissions (CUSTOMER_SUPPORT specialty)
      canViewComplaints: hasPermission(userRole, PERMISSIONS.COMPLAINT_VIEW),
      canManageComplaints: hasPermission(
        userRole,
        PERMISSIONS.COMPLAINT_MANAGE
      ),
      canResolveComplaints: hasPermission(
        userRole,
        PERMISSIONS.COMPLAINT_RESOLVE
      ),

      // Chef Permissions
      canViewAllChefs: hasPermission(userRole, PERMISSIONS.CHEF_VIEW_ALL),
      canViewAssignedChefs: hasPermission(
        userRole,
        PERMISSIONS.CHEF_VIEW_ASSIGNED
      ),
      canViewStationChefs: hasPermission(
        userRole,
        PERMISSIONS.CHEF_VIEW_STATION
      ),
      canManageChefs: hasPermission(userRole, PERMISSIONS.CHEF_MANAGE),
      canAssignChef: hasPermission(userRole, PERMISSIONS.CHEF_ASSIGN),
      canScheduleChef: hasPermission(userRole, PERMISSIONS.CHEF_SCHEDULE),
      canCreateChefAccount: hasPermission(
        userRole,
        PERMISSIONS.CHEF_ACCOUNT_CREATE
      ),
      canDeleteChefAccount: hasPermission(
        userRole,
        PERMISSIONS.CHEF_ACCOUNT_DELETE
      ),

      // Station Manager Account Permissions
      canViewStationManagers: hasPermission(
        userRole,
        PERMISSIONS.STATION_MANAGER_VIEW
      ),
      canCreateStationManager: hasPermission(
        userRole,
        PERMISSIONS.STATION_MANAGER_CREATE
      ),
      canDeleteStationManager: hasPermission(
        userRole,
        PERMISSIONS.STATION_MANAGER_DELETE
      ),

      // Station Permissions
      canViewAllStations: hasPermission(userRole, PERMISSIONS.STATION_VIEW_ALL),
      canViewAssignedStations: hasPermission(
        userRole,
        PERMISSIONS.STATION_VIEW_ASSIGNED
      ),
      canViewOwnStation: hasPermission(userRole, PERMISSIONS.STATION_VIEW_OWN),
      canCreateStation: hasPermission(userRole, PERMISSIONS.STATION_CREATE),
      canManageStations: hasPermission(userRole, PERMISSIONS.STATION_MANAGE),
      canManageAssignedStations: hasPermission(
        userRole,
        PERMISSIONS.STATION_MANAGE_ASSIGNED
      ),
      canDeleteStation: hasPermission(userRole, PERMISSIONS.STATION_DELETE),

      // User Account Permissions
      canViewSuperAdmins: hasPermission(userRole, PERMISSIONS.SUPER_ADMIN_VIEW),
      canCreateSuperAdmin: hasPermission(
        userRole,
        PERMISSIONS.SUPER_ADMIN_CREATE
      ),
      canDeleteSuperAdmin: hasPermission(
        userRole,
        PERMISSIONS.SUPER_ADMIN_DELETE
      ),
      canViewAdmins: hasPermission(userRole, PERMISSIONS.ADMIN_VIEW),
      canCreateAdmin: hasPermission(userRole, PERMISSIONS.ADMIN_CREATE),
      canUpdateAdmin: hasPermission(userRole, PERMISSIONS.ADMIN_UPDATE),
      canDeleteAdmin: hasPermission(userRole, PERMISSIONS.ADMIN_DELETE),
      canAssignStationsToAdmin: hasPermission(
        userRole,
        PERMISSIONS.ADMIN_ASSIGN_STATIONS
      ),
      canViewCustomerSupport: hasPermission(
        userRole,
        PERMISSIONS.CUSTOMER_SUPPORT_VIEW
      ),
      canCreateCustomerSupport: hasPermission(
        userRole,
        PERMISSIONS.CUSTOMER_SUPPORT_CREATE
      ),
      canDeleteCustomerSupport: hasPermission(
        userRole,
        PERMISSIONS.CUSTOMER_SUPPORT_DELETE
      ),

      // Financial Permissions
      canViewAllFinancials: hasPermission(
        userRole,
        PERMISSIONS.FINANCIAL_VIEW_ALL
      ),
      canViewAssignedFinancials: hasPermission(
        userRole,
        PERMISSIONS.FINANCIAL_VIEW_ASSIGNED
      ),
      canProcessRefund: hasPermission(userRole, PERMISSIONS.FINANCIAL_REFUND),
      canAccessFinancialReports: hasPermission(
        userRole,
        PERMISSIONS.FINANCIAL_REPORTS
      ),

      // Audit Permissions
      canViewAllAuditLogs: hasPermission(userRole, PERMISSIONS.AUDIT_VIEW_ALL),
      canViewAssignedAuditLogs: hasPermission(
        userRole,
        PERMISSIONS.AUDIT_VIEW_ASSIGNED
      ),
      canViewOwnAuditLogs: hasPermission(userRole, PERMISSIONS.AUDIT_VIEW_OWN),
      canExportAuditLogs: hasPermission(userRole, PERMISSIONS.AUDIT_EXPORT),

      // System Permissions
      canAccessSystemSettings: hasPermission(
        userRole,
        PERMISSIONS.SYSTEM_SETTINGS
      ),
      canAccessAllAnalytics: hasPermission(
        userRole,
        PERMISSIONS.SYSTEM_ANALYTICS_ALL
      ),
      canAccessAssignedAnalytics: hasPermission(
        userRole,
        PERMISSIONS.SYSTEM_ANALYTICS_ASSIGNED
      ),
      canAccessStationAnalytics: hasPermission(
        userRole,
        PERMISSIONS.SYSTEM_ANALYTICS_STATION
      ),

      // Approval Workflow Permissions
      canGrantApproval: hasPermission(userRole, PERMISSIONS.APPROVAL_GRANT),
      canRequestApproval: hasPermission(userRole, PERMISSIONS.APPROVAL_REQUEST),

      // Helper methods
      hasRole,
      hasAnyRole,
      isAdmin: userRole === UserRole.ADMIN,
      isSuperAdmin: userRole === UserRole.SUPER_ADMIN,
      isCustomerSupport: userRole === UserRole.CUSTOMER_SUPPORT,
      isStationManager: userRole === UserRole.STATION_MANAGER,

      // Business logic helpers
      needsApprovalForBookingDelete: userRole === UserRole.CUSTOMER_SUPPORT,
      isAssignmentScoped: userRole === UserRole.ADMIN,
      isStationScoped: userRole === UserRole.STATION_MANAGER,
    };
  }, [userRole, isAuthenticated]);

  return permissions;
}

export default usePermissions;
