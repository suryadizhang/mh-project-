'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useState } from 'react';
import { LogOut } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import ChatBot from '@/components/ChatBot';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayoutComponent({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const [imageError, setImageError] = useState(false);
  const { logout } = useAuth();

  // Don't render the admin layout on the login page
  if (pathname === '/login') {
    return <>{children}</>;
  }

  const navigation = [
    { name: 'Dashboard', href: '/', icon: '🏠' },
    { name: 'Bookings', href: '/booking', icon: '📅' },
    { name: 'Invoices', href: '/invoices', icon: '🧾' },
    { name: 'Discounts & Promos', href: '/discounts', icon: '💰' },
    { name: 'Payments', href: '/payments', icon: '💳' },
    { name: 'Customers', href: '/customers', icon: '👥' },
    { name: 'SEO Automation', href: '/automation', icon: '🚀' },
    { name: 'AI Learning', href: '/ai-learning', icon: '🤖' },
    { name: 'Newsletter', href: '/newsletter', icon: '📧' },
    { name: 'Schedule', href: '/schedule', icon: '📅' },
    { name: 'Super Admin', href: '/superadmin', icon: '⚡' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
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
                <div className="ml-3">
                  <h1 className="text-xl font-bold text-gray-900">
                    MyHibachi Admin
                  </h1>
                  <p className="text-sm text-gray-500">Management Dashboard</p>
                </div>
              </Link>
            </div>

            <div className="flex items-center space-x-4">
              <Link
                href={
                  process.env.NEXT_PUBLIC_CUSTOMER_URL ||
                  'http://localhost:3000'
                }
                className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                🌐 View Site
              </Link>
              <div className="h-8 w-px bg-gray-200"></div>
              <div className="flex items-center space-x-3">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    A
                  </div>
                  <span className="ml-2 text-sm font-medium text-gray-700">
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
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-[calc(100vh-4rem)]">
          <div className="p-4">
            <div className="space-y-1">
              {navigation.map(item => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`
                      flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors
                      ${
                        isActive
                          ? 'bg-red-50 text-red-700 border-r-2 border-red-600'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }
                    `}
                  >
                    <span className="text-lg mr-3">{item.icon}</span>
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="mt-8 p-4 border-t border-gray-200">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Quick Stats
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">Active Bookings</span>
                <span className="font-medium text-gray-900">24</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">This Month</span>
                <span className="font-medium text-green-600">+18%</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">Revenue</span>
                <span className="font-medium text-gray-900">$12,450</span>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>

      {/* AI ChatBot Widget */}
      <ChatBot 
        defaultMinimized={true}
        showDebugInfo={true}
        className="z-50"
      />
    </div>
  );
}
