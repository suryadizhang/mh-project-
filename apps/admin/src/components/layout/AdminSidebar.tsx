'use client';

import {
  BarChart3,
  Building2,
  Calendar,
  ChefHat,
  ChevronDown,
  ChevronRight,
  Clock,
  CreditCard,
  FileText,
  Headphones,
  Home,
  Inbox,
  LogOut,
  Mail,
  MessageSquare,
  Percent,
  Receipt,
  Settings,
  Sparkles,
  Target,
  Users,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

// Role-based visibility types
type UserRole =
  | 'SUPER_ADMIN'
  | 'ADMIN'
  | 'STATION_MANAGER'
  | 'CHEF'
  | 'CUSTOMER_SUPPORT';

interface SidebarItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: UserRole[]; // If undefined, visible to all authenticated users
  children?: SidebarItem[];
}

// Define sidebar items with role-based visibility
const sidebarItems: SidebarItem[] = [
  {
    title: 'Dashboard',
    href: '/admin',
    icon: Home,
    // Visible to all roles
  },
  {
    title: 'Bookings',
    href: '/admin/booking',
    icon: Calendar,
    // Visible to all roles
  },
  {
    title: 'Station Management',
    href: '/admin/stations',
    icon: Building2,
    roles: ['SUPER_ADMIN', 'ADMIN', 'STATION_MANAGER'],
    children: [
      {
        title: 'Stations',
        href: '/admin/stations',
        icon: Building2,
        roles: ['SUPER_ADMIN', 'ADMIN'],
      },
      {
        title: 'Chef Availability',
        href: '/admin/schedule',
        icon: Clock,
        roles: ['SUPER_ADMIN', 'ADMIN', 'STATION_MANAGER'],
      },
    ],
  },
  {
    title: 'My Availability',
    href: '/admin/schedule',
    icon: Clock,
    roles: ['CHEF'], // Only chefs see this as top-level
  },
  {
    title: 'Leads',
    href: '/admin/leads',
    icon: Target,
    roles: ['SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT'],
  },
  {
    title: 'Customers',
    href: '/admin/customers',
    icon: Users,
    roles: ['SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER'],
  },
  {
    title: 'Payments',
    href: '/admin/payments',
    icon: CreditCard,
    roles: ['SUPER_ADMIN', 'ADMIN', 'STATION_MANAGER', 'CHEF'],
  },
  {
    title: 'Invoices',
    href: '/admin/invoices',
    icon: Receipt,
    roles: ['SUPER_ADMIN', 'ADMIN', 'STATION_MANAGER'],
  },
  {
    title: 'Discounts',
    href: '/admin/discounts',
    icon: Percent,
    roles: ['SUPER_ADMIN', 'ADMIN'],
  },
  {
    title: 'Inbox',
    href: '/admin/inbox',
    icon: Inbox,
    roles: ['SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT'],
  },
  {
    title: 'Reviews',
    href: '/admin/reviews',
    icon: MessageSquare,
    roles: ['SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT'],
  },
  {
    title: 'Newsletter',
    href: '/admin/newsletter',
    icon: Mail,
    roles: ['SUPER_ADMIN', 'ADMIN'],
  },
  {
    title: 'Analytics',
    href: '/admin/analytics',
    icon: BarChart3,
    roles: ['SUPER_ADMIN', 'ADMIN'],
  },
  {
    title: 'AI Learning',
    href: '/admin/ai-learning',
    icon: Sparkles,
    roles: ['SUPER_ADMIN', 'ADMIN'],
  },
  {
    title: 'Escalations',
    href: '/admin/escalations',
    icon: Headphones,
    roles: ['SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT'],
  },
  {
    title: 'Logs',
    href: '/admin/logs',
    icon: FileText,
    roles: ['SUPER_ADMIN', 'ADMIN'],
  },
  {
    title: 'Super Admin',
    href: '/admin/superadmin',
    icon: Settings,
    roles: ['SUPER_ADMIN'],
  },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const { stationContext, logout, isSuperAdmin } = useAuth();
  const [expandedMenus, setExpandedMenus] = useState<string[]>([]);

  // Get user role from station context
  const userRole = stationContext?.role as UserRole | undefined;

  // Check if user can see a menu item
  const canSeeItem = (item: SidebarItem): boolean => {
    // If no roles specified, visible to all
    if (!item.roles) return true;

    // Super admin sees everything
    if (isSuperAdmin()) return true;

    // Check if user's role is in allowed roles
    return userRole ? item.roles.includes(userRole) : false;
  };

  // Toggle dropdown menu
  const toggleMenu = (title: string) => {
    setExpandedMenus(prev =>
      prev.includes(title) ? prev.filter(t => t !== title) : [...prev, title]
    );
  };

  // Check if a menu or any of its children is active
  const isMenuActive = (item: SidebarItem): boolean => {
    if (pathname === item.href) return true;
    if (item.children) {
      return item.children.some(child => pathname === child.href);
    }
    return false;
  };

  // Auto-expand menu if child is active
  const isExpanded = (item: SidebarItem): boolean => {
    if (expandedMenus.includes(item.title)) return true;
    if (item.children) {
      return item.children.some(child => pathname === child.href);
    }
    return false;
  };

  // Render a single menu item
  const renderMenuItem = (item: SidebarItem, isChild = false) => {
    const Icon = item.icon;
    const isActive = pathname === item.href;
    const hasChildren = item.children && item.children.length > 0;
    const menuExpanded = isExpanded(item);
    const visibleChildren = hasChildren
      ? item.children!.filter(canSeeItem)
      : [];

    // If item has children, render as dropdown
    if (hasChildren && visibleChildren.length > 0) {
      return (
        <div key={item.title}>
          <button
            onClick={() => toggleMenu(item.title)}
            className={cn(
              'flex w-full items-center justify-between rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              isMenuActive(item)
                ? 'bg-gray-800 text-white'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            )}
          >
            <div className="flex items-center">
              <Icon className="mr-3 h-5 w-5" />
              {item.title}
            </div>
            {menuExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
          {menuExpanded && (
            <div className="ml-4 mt-1 space-y-1">
              {visibleChildren.map(child => renderMenuItem(child, true))}
            </div>
          )}
        </div>
      );
    }

    // Regular menu item (no children)
    return (
      <Link
        key={item.href}
        href={item.href}
        className={cn(
          'flex items-center rounded-lg px-4 py-2 text-sm font-medium transition-colors',
          isChild && 'ml-2 text-xs',
          isActive
            ? 'bg-gray-800 text-white'
            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
        )}
      >
        <Icon className={cn('mr-3', isChild ? 'h-4 w-4' : 'h-5 w-5')} />
        {item.title}
      </Link>
    );
  };

  return (
    <div className="flex h-screen w-64 flex-col bg-gray-900 text-white">
      <div className="flex h-16 items-center justify-center border-b border-gray-700">
        <h1 className="text-xl font-bold">MyHibachi Admin</h1>
      </div>

      {/* User Info */}
      {stationContext && (
        <div className="border-b border-gray-700 px-4 py-3">
          <p className="text-xs text-gray-400">Logged in as</p>
          <p className="text-sm font-medium truncate">
            {stationContext.role?.replace('_', ' ') || 'User'}
          </p>
          {(stationContext.station_count ?? 0) > 0 && (
            <p className="text-xs text-gray-400 mt-1">
              {stationContext.station_count} station(s)
            </p>
          )}
        </div>
      )}

      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
        {sidebarItems.filter(canSeeItem).map(item => renderMenuItem(item))}
      </nav>

      <div className="border-t border-gray-700 p-4">
        <button
          onClick={logout}
          className="flex w-full items-center rounded-lg px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-700 hover:text-white"
        >
          <LogOut className="mr-3 h-5 w-5" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
