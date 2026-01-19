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
      name: 'Emails',
      href: '/emails',
      icon: '📧',
      badge: 'count',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT],
      tier: 'daily',
      description: 'Customer support & payment emails',
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
  ],
};

/**
 * TIER 2: Analytics & Planning (Weekly)
 * Insights and reporting
 */
const ANALYTICS_PLANNING: NavSection = {
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
      description: 'Reports and insights',
      showInQuickBar: false,
    },
    {
      name: 'Schedule',
      href: '/schedule',
      icon: '📅',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER],
      tier: 'weekly',
      description: 'Staff and event calendar',
      showInQuickBar: false,
    },
    {
      name: 'Stations',
      href: '/stations',
      icon: '🏢',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER],
      tier: 'weekly',
      description: 'Station management',
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
    {
      name: 'Social Media',
      href: '/social',
      icon: '📱',
      roles: [UserRole.SUPER_ADMIN, UserRole.ADMIN],
      tier: 'monthly',
      description: 'Social media management',
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
  ],
};

/**
 * All navigation sections in order
 */
export const NAVIGATION_SECTIONS: NavSection[] = [
  DAILY_OPERATIONS,
  REVENUE_MANAGEMENT,
  CUSTOMER_MANAGEMENT,
  ANALYTICS_PLANNING,
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
