"""
Permission definitions for the My Hibachi RBAC system.

Defines granular permissions for each role aligned with business model.
"""

from .roles import UserRole


class Permission:
    """
    Granular permission definitions for each role aligned with My Hibachi business model.

    ROLE-SPECIFIC PAGE VIEWS (CRITICAL UX REQUIREMENT):
    ===================================================
    Each role has a DEDICATED page/view - they ONLY see options for their job tasks.
    No role can access pages/features outside their scope.

    Role Hierarchy (My Hibachi Business Model - UPDATED 2025-12-30):

    SUPER_ADMIN (Platform Owner):
        - Full admin dashboard with ALL menu options
        - Full system access across ALL stations
        - Manage all admin accounts and their station assignments
        - Create/delete stations and system settings
        - Only role that can create ADMIN, CUSTOMER_SUPPORT accounts

    ADMIN (Station Admin - Multi-Station via Assignment):
        - Admin dashboard scoped to ASSIGNED stations
        - Full CRUD for bookings, customers, chefs in assigned stations
        - Can CREATE/DELETE: STATION_MANAGER and CHEF accounts for assigned stations
        - CANNOT manage other ADMIN or SUPER_ADMIN accounts
        - CANNOT create/delete stations (only SUPER_ADMIN)

    CUSTOMER_SUPPORT:
        - Customer-focused dashboard (bookings, reviews, leads, complaints)
        - View ALL bookings across all stations (main job is customer service)
        - Create, update bookings directly (no approval needed)
        - DELETE bookings/customers requires approval from ADMIN or SUPER_ADMIN
        - Full access to customer, lead, review features
        - Can leave notes for STATION_MANAGER (cannot assign chefs)
        - No access to financial, system settings, or chef assignment

    STATION_MANAGER:
        - Station dashboard (chef scheduling, station bookings)
        - View booking changes for their station (created, updated, deleted, canceled)
        - Assign chefs to parties (primary responsibility)
        - Can ALSO work as chef (station manager = head chef)
        - Manage chefs for their station (availability, time-off)
        - Can CREATE/DELETE: CHEF accounts for their station ONLY
        - Cannot modify bookings (leave that to customer support + admin)

    CHEF:
        - Dedicated chef portal (completely different view from staff pages)
        - View own schedule and assigned events ONLY
        - View assigned event details: customer info, venue address, orders, menu
        - View payment info for assigned events (chef collects payments)
        - Update own availability (per-slot or full day)
        - Submit time-off requests
        - Report incidents for assigned events
        - Cannot modify bookings, access other chefs, or financial reports
    """

    # ========== BOOKING PERMISSIONS ==========
    # SUPER_ADMIN: All bookings across all stations
    # ADMIN: Full CRUD for assigned station(s) bookings
    # CUSTOMER_SUPPORT: View ALL (main job), Create/Update directly, Delete WITH approval
    # STATION_MANAGER: View their station's bookings + changes (created, updated, deleted, canceled)
    # CHEF: View own assigned events only (with payment info for collection)
    BOOKING_VIEW_ALL = [UserRole.SUPER_ADMIN, UserRole.CUSTOMER_SUPPORT]  # CS sees ALL bookings
    BOOKING_VIEW_ASSIGNED = [UserRole.ADMIN]  # Assigned stations only
    BOOKING_VIEW_STATION = [UserRole.STATION_MANAGER]  # Station-scoped (all changes visible)
    BOOKING_VIEW_ASSIGNED_EVENT = [UserRole.CHEF]  # Chef sees only their assigned events
    BOOKING_CREATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    BOOKING_UPDATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # CS can edit directly
    BOOKING_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # Direct delete (no approval)
    BOOKING_DELETE_WITH_APPROVAL = [UserRole.CUSTOMER_SUPPORT]  # CS needs approval for delete only
    BOOKING_LEAVE_NOTE = [
        UserRole.CUSTOMER_SUPPORT,  # CS can leave notes for station manager
    ]

    # ========== CUSTOMER PERMISSIONS ==========
    # CUSTOMER_SUPPORT has FULL access to all customer-related features
    CUSTOMER_VIEW = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    CUSTOMER_CREATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    CUSTOMER_UPDATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    CUSTOMER_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # Direct delete (no approval)
    CUSTOMER_DELETE_WITH_APPROVAL = [
        UserRole.CUSTOMER_SUPPORT,
    ]  # CS needs approval to delete customers

    # ========== LEAD PERMISSIONS ==========
    # CUSTOMER_SUPPORT handles all leads
    LEAD_VIEW = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    LEAD_MANAGE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    LEAD_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # CS can delete leads

    # ========== REVIEW PERMISSIONS ==========
    # CUSTOMER_SUPPORT handles all reviews and complaints
    REVIEW_VIEW = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    REVIEW_MANAGE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # Respond to reviews
    REVIEW_MODERATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # Approve/flag reviews
    REVIEW_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # CS can delete reviews

    # ========== COMPLAINT PERMISSIONS (Customer Support specialty) ==========
    COMPLAINT_VIEW = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    COMPLAINT_MANAGE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    COMPLAINT_RESOLVE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]

    # ========== CHEF PERMISSIONS ==========
    # ADMIN: Manage chefs for assigned stations
    # STATION_MANAGER: View + schedule + ASSIGN chefs (primary responsibility)
    # CHEF: View own schedule, update availability, see assigned event details
    CHEF_VIEW_ALL = [UserRole.SUPER_ADMIN]  # Platform-wide chef view
    CHEF_VIEW_ASSIGNED = [UserRole.ADMIN]  # Chefs in assigned stations
    CHEF_VIEW_STATION = [UserRole.STATION_MANAGER]  # Own station's chefs only
    CHEF_VIEW_OWN = [UserRole.CHEF]  # Chef can view own profile/schedule
    CHEF_MANAGE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # CRUD operations on chefs
    CHEF_ASSIGN = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.STATION_MANAGER,  # Station manager can assign chefs to parties
    ]  # Assign chefs to bookings
    CHEF_SCHEDULE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.STATION_MANAGER,
    ]  # Schedule chefs
    CHEF_ACCOUNT_CREATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.STATION_MANAGER,
    ]  # Create chef accounts
    CHEF_ACCOUNT_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.STATION_MANAGER,
    ]  # Delete chef accounts
    CHEF_UPDATE_OWN_AVAILABILITY = [UserRole.CHEF]  # Chef can update own availability
    CHEF_REQUEST_TIMEOFF = [UserRole.CHEF]  # Chef can submit time-off requests
    CHEF_VIEW_ASSIGNED_EVENT = [
        UserRole.CHEF
    ]  # View assigned event details (customer, venue, orders, payment)
    CHEF_REPORT_INCIDENT = [UserRole.CHEF]  # Report incidents for assigned events

    # ========== STATION MANAGER ACCOUNT PERMISSIONS ==========
    # ADMIN can create/delete STATION_MANAGER accounts for their assigned stations
    STATION_MANAGER_VIEW = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    STATION_MANAGER_CREATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # ADMIN can create for assigned stations
    STATION_MANAGER_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # ADMIN can delete for assigned stations

    # ========== STATION PERMISSIONS ==========
    # SUPER_ADMIN: All stations
    # ADMIN: Only their assigned stations (can be multiple)
    # STATION_MANAGER: View only their station (no edits)
    STATION_VIEW_ALL = [UserRole.SUPER_ADMIN]
    STATION_VIEW_ASSIGNED = [UserRole.ADMIN]  # Multiple assigned stations
    STATION_VIEW_OWN = [UserRole.STATION_MANAGER]  # Single assigned station
    STATION_CREATE = [UserRole.SUPER_ADMIN]  # Only SUPER_ADMIN
    STATION_MANAGE = [UserRole.SUPER_ADMIN]  # Create/delete stations
    STATION_MANAGE_ASSIGNED = [UserRole.ADMIN]  # Edit assigned station settings
    STATION_DELETE = [UserRole.SUPER_ADMIN]  # Only SUPER_ADMIN

    # ========== USER ACCOUNT PERMISSIONS ==========
    # SUPER_ADMIN: Can manage all account types
    # ADMIN: Can create STATION_MANAGER and CHEF for assigned stations
    # STATION_MANAGER: Can create CHEF for their station only

    # Super Admin account management (SUPER_ADMIN only)
    SUPER_ADMIN_VIEW = [UserRole.SUPER_ADMIN]
    SUPER_ADMIN_CREATE = [UserRole.SUPER_ADMIN]
    SUPER_ADMIN_DELETE = [UserRole.SUPER_ADMIN]

    # Admin account management (SUPER_ADMIN only)
    ADMIN_VIEW = [UserRole.SUPER_ADMIN]
    ADMIN_CREATE = [UserRole.SUPER_ADMIN]
    ADMIN_UPDATE = [UserRole.SUPER_ADMIN]
    ADMIN_DELETE = [UserRole.SUPER_ADMIN]
    ADMIN_ASSIGN_STATIONS = [UserRole.SUPER_ADMIN]  # Assign stations to admins

    # Customer Support account management (SUPER_ADMIN only)
    CUSTOMER_SUPPORT_VIEW = [UserRole.SUPER_ADMIN]
    CUSTOMER_SUPPORT_CREATE = [UserRole.SUPER_ADMIN]
    CUSTOMER_SUPPORT_DELETE = [UserRole.SUPER_ADMIN]

    # ========== FINANCIAL PERMISSIONS ==========
    # ADMIN: Financial reports for their assigned stations
    FINANCIAL_VIEW_ALL = [UserRole.SUPER_ADMIN]
    FINANCIAL_VIEW_ASSIGNED = [UserRole.ADMIN]  # Assigned stations only
    FINANCIAL_REFUND = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    FINANCIAL_REPORTS = [UserRole.SUPER_ADMIN, UserRole.ADMIN]

    # ========== AUDIT PERMISSIONS ==========
    AUDIT_VIEW_ALL = [UserRole.SUPER_ADMIN]
    AUDIT_VIEW_ASSIGNED = [UserRole.ADMIN]  # Assigned stations audit
    AUDIT_VIEW_OWN = [UserRole.CUSTOMER_SUPPORT, UserRole.STATION_MANAGER]
    AUDIT_EXPORT = [UserRole.SUPER_ADMIN, UserRole.ADMIN]

    # ========== SYSTEM PERMISSIONS ==========
    SYSTEM_SETTINGS = [UserRole.SUPER_ADMIN]  # Only SUPER_ADMIN for system settings
    SYSTEM_ANALYTICS_ALL = [UserRole.SUPER_ADMIN]
    SYSTEM_ANALYTICS_ASSIGNED = [UserRole.ADMIN]  # Assigned stations analytics
    SYSTEM_ANALYTICS_STATION = [UserRole.STATION_MANAGER]  # Single station analytics

    # ========== APPROVAL WORKFLOW PERMISSIONS ==========
    # For customer_support booking DELETE requiring approval
    APPROVAL_GRANT = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # Can approve/reject delete requests
    APPROVAL_REQUEST = [UserRole.CUSTOMER_SUPPORT]  # Can request approval for delete
