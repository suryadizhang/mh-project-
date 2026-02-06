/**
 * Navigation Configuration
 * Role-based, 3-tier navigation structure optimized for MyHibachi business model
 *
 * Roles (matching backend):
 * - SUPER_ADMIN: Full system access
 * - ADMIN: Administrative access
 * - CUSTOMER_SUPPORT: Customer service operations
 * - STATION_MANAGER: Station-specific operations
 */

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  CUSTOMER_SUPPORT = 'customer_support',
  STATION_MANAGER = 'station_manager',
  CHEF = 'chef',
}

export interface NavItem {
  name: string;
  href: string;
  icon: string;
  badge?: 'live' | 'count'; // Live badge for real-time updates
  roles: UserRole[]; // Which roles can see this
  tier: 'daily' | 'weekly' | 'monthly'; // Usage frequency
  description?: string;
  showInQuickBar?: boolean; // Default quick action bar
}

export interface NavSection {
  title: string;
  items: NavItem[];
  collapsible: boolean;
  defaultExpanded: boolean;
  roles: UserRole[];
}

/**
 * TIER 1: Daily Operations (Most Used)
 * These features are accessed multiple times per day
 */
const DAILY_OPERATIONS: NavSection = {
  title: '📋 Daily Operations',
  collapsible: true,
  defaultExpanded: true,
  roles: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CUSTOMER_SUPPORT,
    UserRole.STATION_MANAGER,
  ],
  items: [
    {
      name: 'Dashboard',
      href: '/',
      icon: '🏠',
      roles: [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
        UserRole.STATION_MANAGER,
      ],
      tier: 'daily',
      description: 'Overview and quick stats',
      showInQuickBar: true,
    },
    {
      name: 'Bookings',
      href: '/booking',
      icon: '📅',
      badge: 'count',
      roles: [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
        UserRole.STATION_MANAGER,
      ],
      tier: 'daily',
      description: 'Event bookings and reservations',
      showInQuickBar: true,
    },
    {
      name: 'Escalations',
      href: '/escalations',
      icon: '🆘',
      badge: 'live',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'daily',
      description: 'Urgent customer issues',
      showInQuickBar: true,
    },
    {
      name: 'Inbox',
      href: '/inbox',
      icon: '💬',
      badge: 'count',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'daily',
      description: 'Unified communications (SMS, Social)',
      showInQuickBar: true,
    },
    {
      name: 'Leads',
      href: '/leads',
      icon: '🎯',
      badge: 'count',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'daily',
      description: 'New inquiries and quotes',
      showInQuickBar: true,
    },
    {
      name: 'Booking Calendar',
      href: '/booking/calendar',
      icon: '📆',
      roles: [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
        UserRole.STATION_MANAGER,
      ],
      tier: 'daily',
      description: 'Calendar view of all bookings',
      showInQuickBar: false,
    },
    {
      name: 'Agreements',
      href: '/agreements',
      icon: '📝',
      roles: [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
      ],
      tier: 'daily',
      description: 'Customer agreements and signing links',
      showInQuickBar: false,
    },
  ],
};

/**
 * TIER 2: Revenue Management (Weekly)
 * Financial operations accessed regularly
 */
const REVENUE_MANAGEMENT: NavSection = {
  title: '💰 Revenue',
  collapsible: true,
  defaultExpanded: true,
  roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
  items: [
    {
      name: 'Payments',
      href: '/payments',
      icon: '💳',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'daily',
      description: 'Payment processing and history',
      showInQuickBar: false,
    },
    {
      name: 'Payment History',
      href: '/payments/history',
      icon: '📜',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'weekly',
      description: 'Historical payment records and reports',
      showInQuickBar: false,
    },
    {
      name: 'Invoices',
      href: '/invoices',
      icon: '🧾',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'weekly',
      description: 'Invoice generation and management',
      showInQuickBar: false,
    },
    {
      name: 'Discounts',
      href: '/discounts',
      icon: '💰',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'weekly',
      description: 'Coupon and discount management',
      showInQuickBar: false,
    },
    // NOTE: Chef Earnings moved to Station Management section
  ],
};

/**
 * TIER 2: Customer Management (Weekly)
 * Customer relationship and engagement
 */
const CUSTOMER_MANAGEMENT: NavSection = {
  title: '👥 Customers',
  collapsible: true,
  defaultExpanded: true,
  roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
  items: [
    {
      name: 'Customers',
      href: '/customers',
      icon: '👥',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'daily',
      description: 'Customer database',
      showInQuickBar: false,
    },
    {
      name: 'Reviews',
      href: '/reviews',
      icon: '⭐',
      badge: 'count',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'weekly',
      description: 'Review moderation and responses',
      showInQuickBar: false,
    },
    {
      name: 'Newsletter',
      href: '/newsletter',
      icon: '📧',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'weekly',
      description: 'Email and SMS campaigns',
      showInQuickBar: false,
    },
    {
      name: 'Subscribers',
      href: '/newsletter/subscribers',
      icon: '👤',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'weekly',
      description: 'Manage newsletter subscribers',
      showInQuickBar: false,
    },
    {
      name: 'Campaigns',
      href: '/newsletter/campaigns',
      icon: '📨',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'weekly',
      description: 'Create and manage email campaigns',
      showInQuickBar: false,
    },
    {
      name: 'Email Analytics',
      href: '/newsletter/analytics',
      icon: '📈',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
      tier: 'weekly',
      description: 'Email campaign performance',
      showInQuickBar: false,
    },
  ],
};

/**
 * TIER 2: Analytics & Reporting (Weekly)
 * Business insights and reports only - Schedule/Stations moved to Station Management
 */
const ANALYTICS_REPORTING: NavSection = {
  title: '📊 Analytics',
  collapsible: true,
  defaultExpanded: false,
  roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  items: [
    {
      name: 'Analytics',
      href: '/analytics',
      icon: '📊',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
      tier: 'weekly',
      description: 'Reports and business insights',
      showInQuickBar: false,
    },
  ],
};

/**
 * TIER 3: Marketing Tools (Monthly)
 * Marketing automation and campaigns
 */
const MARKETING_TOOLS: NavSection = {
  title: '🚀 Marketing',
  collapsible: true,
  defaultExpanded: false,
  roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
  items: [
    {
      name: 'QR Codes',
      href: '/qr',
      icon: '📍',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
      tier: 'monthly',
      description: 'QR code campaigns',
      showInQuickBar: false,
    },
    {
      name: 'SEO Automation',
      href: '/automation',
      icon: '🚀',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
      tier: 'monthly',
      description: 'SEO and content automation',
      showInQuickBar: false,
    },
  ],
};

/**
 * STATION MANAGEMENT SYSTEM
 * ================================================================
 * 🔄 Restructured 2025-01-30 - Combined Station Ops + Chef Portal
 *
 * MULTI-STATION ACCESS:
 * - SUPER_ADMIN: Full access to ALL stations + can intervene
 * - ADMIN: Access to ASSIGNED stations (can be multiple)
 * - STATION_MANAGER: Access to OWN station(s) + manage chefs
 * - CHEF: Self-service portal only (own schedule, availability, earnings)
 *
 * This section is the unified hub for station operations:
 * - Station configuration (SUPER_ADMIN, ADMIN, STATION_MANAGER)
 * - Chef roster management (SUPER_ADMIN, ADMIN, STATION_MANAGER)
 * - Scheduling and assignments (SUPER_ADMIN, ADMIN, STATION_MANAGER)
 * - Chef self-service portal (CHEF only)
 * ================================================================
 */
const STATION_MANAGEMENT: NavSection = {
  title: '🏢 Station Management',
  collapsible: true,
  defaultExpanded: true,
  roles: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.STATION_MANAGER,
    UserRole.CHEF,
  ],
  items: [
    // ================================
    // STATION OPERATIONS (Staff Only)
    // ================================
    {
      name: 'Stations',
      href: '/stations',
      icon: '🏢',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER],
      tier: 'weekly',
      description: 'Manage station(s) - SA: All, ADMIN: Assigned, SM: Own',
      showInQuickBar: false,
    },
    {
      name: 'Master Schedule',
      href: '/schedule',
      icon: '📅',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER],
      tier: 'daily',
      description: 'Station calendar and chef scheduling',
      showInQuickBar: false,
    },
    {
      name: 'Chef Roster',
      href: '/stations/chefs',
      icon: '👥',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER],
      tier: 'weekly',
      description: '🟡 NEW - Manage station chefs (availability, assignments)',
      showInQuickBar: false,
    },
    {
      name: 'Chef Assignments',
      href: '/stations/assignments',
      icon: '📋',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER],
      tier: 'daily',
      description: '🟡 NEW - Assign chefs to bookings',
      showInQuickBar: false,
    },
    {
      name: 'Chef Earnings',
      href: '/chef-earnings',
      icon: '💰',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER],
      tier: 'weekly',
      description: 'Chef pay rates, earnings, and performance',
      showInQuickBar: false,
    },
    // ================================
    // CHEF SELF-SERVICE PORTAL
    // (CHEF role sees ONLY these items)
    // ================================
    {
      name: 'My Schedule',
      href: '/chef/schedule',
      icon: '📅',
      roles: [UserRole.CHEF],
      tier: 'daily',
      description: '🟡 Batch 2-3 - Your assigned events and schedule',
      showInQuickBar: true,
    },
    {
      name: 'My Availability',
      href: '/chef/availability',
      icon: '🗓️',
      roles: [UserRole.CHEF],
      tier: 'daily',
      description: '🟡 Batch 2-3 - Update availability and time-off requests',
      showInQuickBar: true,
    },
    {
      name: 'My Events',
      href: '/chef/events',
      icon: '📋',
      roles: [UserRole.CHEF],
      tier: 'daily',
      description:
        '🟡 Batch 2-3 - Assigned event details (customer, venue, menu)',
      showInQuickBar: false,
    },
    {
      name: 'My Earnings',
      href: '/chef/earnings',
      icon: '💵',
      roles: [UserRole.CHEF],
      tier: 'weekly',
      description: '🟡 Batch 2-3 - Your earnings and payment history',
      showInQuickBar: false,
    },
  ],
};

/**
 * TIER 3: Advanced Features (Rare/Admin Only)
 * System administration and technical features
 */
const ADVANCED_FEATURES: NavSection = {
  title: '⚙️ Advanced',
  collapsible: true,
  defaultExpanded: false,
  roles: [UserRole.SUPER_ADMIN],
  items: [
    {
      name: 'AI Learning',
      href: '/ai-learning',
      icon: '🤖',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description: 'AI training and knowledge',
      showInQuickBar: false,
    },
    {
      name: 'Super Admin',
      href: '/superadmin',
      icon: '⚡',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description: 'System configuration',
      showInQuickBar: false,
    },
    {
      name: 'Audit Logs',
      href: '/superadmin/audit-logs',
      icon: '📋',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description: 'Security audit trail and user activity',
      showInQuickBar: false,
    },
    {
      name: 'System Logs',
      href: '/logs',
      icon: '📝',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description: 'System monitoring and logs',
      showInQuickBar: false,
    },
    {
      name: 'VPS Security',
      href: '/superadmin/vps-security',
      icon: '🛡️',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description: 'VPS security monitoring and fail2ban management',
      showInQuickBar: false,
    },
    // ================================================================
    // 🔴 CRITICAL MISSING ROUTES - Added 2025-01-30
    // These pages exist but were NOT in navigation. Now added!
    // ================================================================
    {
      name: 'User Management',
      href: '/superadmin/users',
      icon: '👥',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description: '🔴 CRITICAL - Manage system users (was MISSING from nav)',
      showInQuickBar: false,
    },
    {
      name: 'Role Management',
      href: '/superadmin/roles',
      icon: '🎭',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description:
        '🔴 CRITICAL - Manage user roles and permissions (was MISSING from nav)',
      showInQuickBar: false,
    },
    {
      name: 'Pricing Config',
      href: '/superadmin/pricing',
      icon: '💰',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description:
        '🔴 CRITICAL - SSoT pricing configuration (was MISSING from nav)',
      showInQuickBar: false,
    },
    {
      name: 'Dynamic Variables',
      href: '/superadmin/variables',
      icon: '🔧',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description:
        '🔴 CRITICAL - SSoT business variables (was MISSING from nav)',
      showInQuickBar: false,
    },
    {
      name: 'Knowledge Sync',
      href: '/superadmin/knowledge-sync',
      icon: '🧠',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description: '🟡 Batch 3 - AI knowledge base sync (was MISSING from nav)',
      showInQuickBar: false,
    },
    {
      name: 'Scaling Config',
      href: '/superadmin/scaling',
      icon: '📈',
      roles: [UserRole.SUPER_ADMIN],
      tier: 'monthly',
      description:
        '🟢 Batch 6 - Multi-station scaling settings (was MISSING from nav)',
      showInQuickBar: false,
    },
  ],
};

/**
 * All navigation sections in order
 */
export const NAVIGATION_SECTIONS: NavSection[] = [
  DAILY_OPERATIONS,
  REVENUE_MANAGEMENT,
  CUSTOMER_MANAGEMENT,
  STATION_MANAGEMENT, // 🏢 Combined: Station Ops + Chef Portal with role filtering
  ANALYTICS_REPORTING,
  MARKETING_TOOLS,
  ADVANCED_FEATURES,
];

/**
 * Default quick action bar items (user can customize)
 * Based on highest usage frequency in hibachi catering business
 */
export const DEFAULT_QUICK_ACTIONS: string[] = [
  '/', // Dashboard
  '/booking', // Bookings (most used)
  '/escalations', // Urgent issues
  '/inbox', // Communications
  '/leads', // New inquiries
];

/**
 * Filter navigation by user role
 */
export function getNavigationForRole(role: UserRole): NavSection[] {
  return NAVIGATION_SECTIONS.map(section => ({
    ...section,
    items: section.items.filter(item => item.roles.includes(role)),
  })).filter(
    section => section.roles.includes(role) && section.items.length > 0
  );
}

/**
 * Get all navigation items (flat list)
 */
export function getAllNavItems(): NavItem[] {
  return NAVIGATION_SECTIONS.flatMap(section => section.items);
}

/**
 * Get quick action items by user preference
 */
export function getQuickActions(userPreferences?: string[]): NavItem[] {
  const allItems = getAllNavItems();
  const preferenceHrefs = userPreferences || DEFAULT_QUICK_ACTIONS;

  return preferenceHrefs
    .map(href => allItems.find(item => item.href === href))
    .filter((item): item is NavItem => item !== undefined);
}

/**
 * Role hierarchy (for permission checking)
 */
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  [UserRole.SUPER_ADMIN]: 4,
  [UserRole.ADMIN]: 3,
  [UserRole.CUSTOMER_SUPPORT]: 2,
  [UserRole.STATION_MANAGER]: 1,
  [UserRole.CHEF]: 0,
};

/**
 * Check if user has permission
 */
export function hasPermission(
  userRole: UserRole,
  requiredRole: UserRole
): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

/**
 * Get role display name
 */
export function getRoleDisplayName(role: UserRole): string {
  const names: Record<UserRole, string> = {
    [UserRole.SUPER_ADMIN]: 'Super Admin',
    [UserRole.ADMIN]: 'Admin',
    [UserRole.CUSTOMER_SUPPORT]: 'Customer Support',
    [UserRole.STATION_MANAGER]: 'Station Manager',
    [UserRole.CHEF]: 'Chef',
  };
  return names[role];
}
