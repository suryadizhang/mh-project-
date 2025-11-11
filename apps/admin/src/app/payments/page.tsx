'use client';

import PaymentManagement from '@/components/PaymentManagement';

export default function AdminPaymentsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <nav className="flex space-x-8">
              <a
                href="/admin"
                className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                Dashboard
              </a>
              <a
                href="/admin/bookings"
                className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                Bookings
              </a>
              <a
                href="/admin/payments"
                className="bg-blue-100 text-blue-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                Payments
              </a>
              <a
                href="/admin/customers"
                className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                Customers
              </a>
              <a
                href="/admin/analytics"
                className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                Analytics
              </a>
            </nav>
          </div>
        </div>
      </div>

      <PaymentManagement />
    </div>
  );
}
