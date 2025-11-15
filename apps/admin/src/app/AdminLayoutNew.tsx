'use client';

import {
  ChevronDown,
  ChevronRight,
  LogOut,
  Menu,
  Settings,
  X,
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useEffect, useState } from 'react';

import ChatBot from '@/components/ChatBot';
import {
  DEFAULT_QUICK_ACTIONS,
  getNavigationForRole,
  getQuickActions,
  getRoleDisplayName,
  UserRole,
} from '@/config/navigation.config';
import { useAuth } from '@/contexts/AuthContext';
import { useEscalationWebSocket } from '@/hooks/useEscalationWebSocket';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayoutNew({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const [imageError, setImageError] = useState(false);
  const { logout, stationContext, isSuperAdmin } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(
    new Set()
  );
  const [quickActions, setQuickActions] = useState<string[]>(
    DEFAULT_QUICK_ACTIONS
  );
  const [isQuickBarCustomizing, setIsQuickBarCustomizing] = useState(false);

  // Get user role from auth context and map to navigation UserRole enum
  const getUserRole = (): UserRole => {
    if (!stationContext) return UserRole.ADMIN;
    if (isSuperAdmin()) return UserRole.SUPER_ADMIN;

    // Map backend role strings to navigation UserRole enum
    const roleMap: Record<string, UserRole> = {
      super_admin: UserRole.SUPER_ADMIN,
      admin: UserRole.ADMIN,
      customer_support: UserRole.CUSTOMER_SUPPORT,
      station_manager: UserRole.STATION_MANAGER,
    };

    return roleMap[stationContext.role.toLowerCase()] || UserRole.ADMIN;
  };

  const userRole = getUserRole();

  // WebSocket connection for real-time escalation counts
  const { stats: escalationStats } = useEscalationWebSocket();

  // Detect mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
      if (window.innerWidth >= 1024) {
        setIsSidebarOpen(false); // Close sidebar on desktop
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Load user preferences from localStorage
  useEffect(() => {
    const savedQuickActions = localStorage.getItem('quickActions');
    if (savedQuickActions) {
      setQuickActions(JSON.parse(savedQuickActions));
    }

    const savedCollapsed = localStorage.getItem('collapsedSections');
    if (savedCollapsed) {
      setCollapsedSections(new Set(JSON.parse(savedCollapsed)));
    }
  }, []);

  // Close mobile menu when route changes
  useEffect(() => {
    setIsSidebarOpen(false);
  }, [pathname]);

  const toggleSection = (sectionTitle: string) => {
    const newCollapsed = new Set(collapsedSections);
    if (newCollapsed.has(sectionTitle)) {
      newCollapsed.delete(sectionTitle);
    } else {
      newCollapsed.add(sectionTitle);
    }
    setCollapsedSections(newCollapsed);
    localStorage.setItem(
      'collapsedSections',
      JSON.stringify(Array.from(newCollapsed))
    );
  };

  // Get navigation filtered by role
  const navigationSections = getNavigationForRole(userRole);
  const quickActionItems = getQuickActions(quickActions);

  // Don't render the admin layout on the login page
  if (pathname === '/login') {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Header - Always Visible */}
      <header className="sticky top-0 z-50 bg-white shadow-sm border-b border-gray-200">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left: Logo + Menu Button */}
            <div className="flex items-center space-x-4">
              {/* Mobile Menu Toggle */}
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                aria-label="Toggle menu"
              >
                {isSidebarOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>

              {/* Brand */}
              <Link href="/" className="flex items-center">
                <div className="relative w-10 h-10">
                  <Image
                    src={
                      imageError
                        ? '/images/myhibachi-logo.svg'
                        : '/images/myhibachi-logo.png'
                    }
                    alt="MyHibachi Logo"
                    fill
                    className="object-contain"
                    onError={() => setImageError(true)}
                  />
                </div>
                <div className="ml-3 hidden sm:block">
                  <h1 className="text-xl font-bold text-gray-900">
                    MyHibachi Admin
                  </h1>
                  <p className="text-xs text-gray-500">
                    {getRoleDisplayName(userRole)}
                  </p>
                </div>
              </Link>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center space-x-2 sm:space-x-4">
              {/* View Site Link - Hidden on small mobile */}
              <Link
                href={
                  process.env.NEXT_PUBLIC_CUSTOMER_URL ||
                  'http://localhost:3000'
                }
                className="hidden sm:flex text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                🌐 View Site
              </Link>

              {/* User Menu */}
              <div className="flex items-center space-x-2 sm:space-x-3">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    A
                  </div>
                  <span className="ml-2 text-sm font-medium text-gray-700 hidden sm:inline">
                    Admin User
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar - Desktop */}
        <aside className="hidden lg:block w-64 bg-white shadow-sm border-r border-gray-200 min-h-[calc(100vh-4rem)] sticky top-16 overflow-y-auto">
          <nav className="p-4">
            {navigationSections.map(section => {
              const isCollapsed = collapsedSections.has(section.title);
              return (
                <div key={section.title} className="mb-6">
                  {/* Section Header */}
                  <button
                    onClick={() =>
                      section.collapsible && toggleSection(section.title)
                    }
                    className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide hover:bg-gray-50 rounded-md transition-colors"
                  >
                    <span>{section.title}</span>
                    {section.collapsible &&
                      (isCollapsed ? (
                        <ChevronRight className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </button>

                  {/* Section Items */}
                  {!isCollapsed && (
                    <div className="mt-2 space-y-1">
                      {section.items.map(item => {
                        const isActive = pathname === item.href;
                        let badgeCount = 0;

                        if (
                          item.badge === 'live' &&
                          item.href === '/escalations'
                        ) {
                          badgeCount = escalationStats.total_active;
                        }

                        return (
                          <Link
                            key={item.href}
                            href={item.href}
                            className={`
                              flex items-center justify-between px-4 py-3 text-sm font-medium rounded-lg transition-all
                              ${
                                isActive
                                  ? 'bg-red-50 text-red-700 border-l-4 border-red-600 pl-3'
                                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                              }
                            `}
                            title={item.description}
                          >
                            <div className="flex items-center">
                              <span className="text-lg mr-3">{item.icon}</span>
                              {item.name}
                            </div>

                            {/* Badge */}
                            {item.badge === 'live' && badgeCount > 0 && (
                              <span className="inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold leading-none text-white bg-red-600 rounded-full animate-pulse">
                                {badgeCount}
                              </span>
                            )}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </aside>

        {/* Mobile Sidebar Overlay */}
        {isMobile && isSidebarOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black bg-opacity-50 z-40"
              onClick={() => setIsSidebarOpen(false)}
            />

            {/* Sidebar */}
            <aside className="fixed top-16 left-0 bottom-0 w-80 bg-white shadow-xl z-50 overflow-y-auto">
              <nav className="p-4">
                {navigationSections.map(section => {
                  const isCollapsed = collapsedSections.has(section.title);

                  return (
                    <div key={section.title} className="mb-6">
                      {/* Section Header */}
                      <button
                        onClick={() =>
                          section.collapsible && toggleSection(section.title)
                        }
                        className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide hover:bg-gray-50 rounded-md transition-colors"
                      >
                        <span>{section.title}</span>
                        {section.collapsible &&
                          (isCollapsed ? (
                            <ChevronRight className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          ))}
                      </button>

                      {/* Section Items */}
                      {!isCollapsed && (
                        <div className="mt-2 space-y-1">
                          {section.items.map(item => {
                            const isActive = pathname === item.href;
                            let badgeCount = 0;

                            if (
                              item.badge === 'live' &&
                              item.href === '/escalations'
                            ) {
                              badgeCount = escalationStats.total_active;
                            }

                            return (
                              <Link
                                key={item.href}
                                href={item.href}
                                className={`
                                  flex items-center justify-between px-4 py-4 text-base font-medium rounded-lg transition-all
                                  ${
                                    isActive
                                      ? 'bg-red-50 text-red-700 border-l-4 border-red-600 pl-3'
                                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 active:bg-gray-100'
                                  }
                                `}
                                title={item.description}
                              >
                                <div className="flex items-center">
                                  <span className="text-xl mr-3">
                                    {item.icon}
                                  </span>
                                  {item.name}
                                </div>

                                {/* Badge */}
                                {item.badge === 'live' && badgeCount > 0 && (
                                  <span className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-600 rounded-full animate-pulse">
                                    {badgeCount}
                                  </span>
                                )}
                              </Link>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </nav>
            </aside>
          </>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-auto pb-20 lg:pb-0">{children}</main>
      </div>

      {/* Quick Action Bar - Bottom (Mobile & Tablet) */}
      {isMobile && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-40">
          <div className="flex items-center justify-around px-2 py-2">
            {quickActionItems.slice(0, 5).map(item => {
              const isActive = pathname === item.href;
              let badgeCount = 0;

              if (item.badge === 'live' && item.href === '/escalations') {
                badgeCount = escalationStats.total_active;
              }

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    relative flex flex-col items-center justify-center min-w-[60px] p-2 rounded-lg transition-all
                    ${
                      isActive
                        ? 'bg-red-50 text-red-700'
                        : 'text-gray-600 hover:text-gray-900 active:bg-gray-100'
                    }
                  `}
                >
                  <span className="text-xl mb-1">{item.icon}</span>
                  <span className="text-[10px] font-medium text-center leading-tight">
                    {item.name.split(' ')[0]}
                  </span>

                  {/* Badge */}
                  {item.badge === 'live' && badgeCount > 0 && (
                    <span className="absolute top-1 right-1 inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold text-white bg-red-600 rounded-full animate-pulse">
                      {badgeCount}
                    </span>
                  )}
                </Link>
              );
            })}

            {/* Customize Button */}
            <button
              onClick={() => setIsQuickBarCustomizing(!isQuickBarCustomizing)}
              className="flex flex-col items-center justify-center min-w-[60px] p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-50 active:bg-gray-100 transition-all"
            >
              <Settings className="w-5 h-5 mb-1" />
              <span className="text-[10px] font-medium">More</span>
            </button>
          </div>
        </div>
      )}

      {/* AI ChatBot Widget */}
      <ChatBot defaultMinimized={true} showDebugInfo={true} className="z-50" />
    </div>
  );
}
