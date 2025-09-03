'use client'

import Image from 'next/image'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ReactNode, useState } from 'react'

interface AdminLayoutProps {
  children: ReactNode
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname()
  const [imageError, setImageError] = useState(false)

  const navigation = [
    { name: 'Dashboard', href: '/admin', icon: '🏠' },
    { name: 'Bookings', href: '/admin/bookings', icon: '📅' },
    { name: 'Invoices', href: '/admin/invoices', icon: '🧾' },
    { name: 'Discounts & Promos', href: '/admin/discounts', icon: '💰' },
    { name: 'Menu Management', href: '/admin/menu', icon: '🍱' },
    { name: 'Customer Reviews', href: '/admin/reviews', icon: '⭐' },
    { name: 'SEO Automation', href: '/admin/automation', icon: '🚀' },
    { name: 'Analytics', href: '/admin/analytics', icon: '📊' }
  ]

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
                    src={imageError ? '/images/myhibachi-logo.svg' : '/images/myhibachi-logo.png'}
                    alt="MyHibachi Logo"
                    fill
                    className="object-contain"
                    onError={() => setImageError(true)}
                  />
                </div>
                <div className="ml-3">
                  <h1 className="text-xl font-bold text-gray-900">MyHibachi Admin</h1>
                  <p className="text-sm text-gray-500">Management Dashboard</p>
                </div>
              </Link>
            </div>

            <div className="flex items-center space-x-4">
              <Link
                href="/"
                className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                🌐 View Site
              </Link>
              <div className="h-8 w-px bg-gray-200"></div>
              <div className="flex items-center">
                <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  A
                </div>
                <span className="ml-2 text-sm font-medium text-gray-700">Admin User</span>
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
                const isActive = pathname === item.href
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
                )
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
    </div>
  )
}
