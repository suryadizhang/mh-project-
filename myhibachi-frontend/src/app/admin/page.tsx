'use client'

import { format } from 'date-fns'
import { Calendar, Mail, TrendingUp, Users } from 'lucide-react'
import React, { useEffect, useState } from 'react'

// Enhanced booking interface for production
interface Booking {
  id: string
  customerName: string
  customerEmail: string
  customerPhone: string
  eventDate: string
  eventTime: string
  guestCount: number
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed'
  createdAt: string
  venueAddress: string
  billingAddress: string
}

export default function AdminDashboard() {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [dateFilter, setDateFilter] = useState<string>('')

  // Load bookings (in production, fetch from API)
  useEffect(() => {
    // Simulate API call
    const fetchBookings = async () => {
      // Mock data with realistic booking scenarios
      const mockBookings: Booking[] = [
        {
          id: 'MH-1691234567890-ABC123',
          customerName: 'John Smith',
          customerEmail: 'john.smith@email.com',
          customerPhone: '(555) 123-4567',
          eventDate: '2025-08-10',
          eventTime: '6PM',
          guestCount: 25,
          status: 'confirmed',
          createdAt: '2025-08-07T14:30:00Z',
          venueAddress: '123 Main St, Anytown, CA 12345',
          billingAddress: '123 Main St, Anytown, CA 12345'
        },
        {
          id: 'MH-1691234567891-DEF456',
          customerName: 'Sarah Johnson',
          customerEmail: 'sarah.j@email.com',
          customerPhone: '(555) 987-6543',
          eventDate: '2025-08-12',
          eventTime: '3PM',
          guestCount: 15,
          status: 'pending',
          createdAt: '2025-08-07T16:45:00Z',
          venueAddress: '456 Oak Ave, Somewhere, NY 54321',
          billingAddress: '789 Pine St, Elsewhere, NY 98765'
        },
        {
          id: 'MH-1691234567892-GHI789',
          customerName: 'Mike Chen',
          customerEmail: 'mike.chen@email.com',
          customerPhone: '(555) 456-7890',
          eventDate: '2025-08-15',
          eventTime: '12PM',
          guestCount: 40,
          status: 'confirmed',
          createdAt: '2025-08-07T18:20:00Z',
          venueAddress: '789 Elm Blvd, Cityville, TX 67890',
          billingAddress: '789 Elm Blvd, Cityville, TX 67890'
        },
        {
          id: 'MH-1691234567893-JKL012',
          customerName: 'Lisa Rodriguez',
          customerEmail: 'lisa.r@email.com',
          customerPhone: '(555) 321-0987',
          eventDate: '2025-08-18',
          eventTime: '9PM',
          guestCount: 30,
          status: 'pending',
          createdAt: '2025-08-07T20:10:00Z',
          venueAddress: '321 Maple Dr, Hometown, FL 13579',
          billingAddress: '321 Maple Dr, Hometown, FL 13579'
        }
      ]

      setTimeout(() => {
        setBookings(mockBookings)
        setLoading(false)
      }, 1000)
    }

    fetchBookings()
  }, [])

  // Calculate stats from real data
  const stats = [
    {
      title: 'Total Bookings',
      value: bookings.length.toString(),
      change: '+12%',
      icon: Calendar,
      color: 'text-blue-600'
    },
    {
      title: 'Confirmed Bookings',
      value: bookings.filter(b => b.status === 'confirmed').length.toString(),
      change: '+8%',
      icon: Users,
      color: 'text-green-600'
    },
    {
      title: 'Pending Approvals',
      value: bookings.filter(b => b.status === 'pending').length.toString(),
      change: `${bookings.filter(b => b.status === 'pending').length > 0 ? 'Action needed' : 'All clear'}`,
      icon: Mail,
      color: 'text-purple-600'
    },
    {
      title: 'Total Guests',
      value: bookings.reduce((sum, b) => sum + b.guestCount, 0).toString(),
      change: '+23%',
      icon: TrendingUp,
      color: 'text-orange-600'
    }
  ]

  // Filter bookings based on status and date
  const filteredBookings = bookings.filter(booking => {
    if (statusFilter !== 'all' && booking.status !== statusFilter) return false
    if (dateFilter && booking.eventDate !== dateFilter) return false
    return true
  })

  // Export bookings to CSV
  const exportToCSV = () => {
    const csvContent = [
      [
        'ID',
        'Customer Name',
        'Email',
        'Phone',
        'Event Date',
        'Time',
        'Guests',
        'Status',
        'Venue Address',
        'Created At'
      ],
      ...filteredBookings.map(booking => [
        booking.id,
        booking.customerName,
        booking.customerEmail,
        booking.customerPhone,
        booking.eventDate,
        booking.eventTime,
        booking.guestCount.toString(),
        booking.status,
        booking.venueAddress,
        new Date(booking.createdAt).toLocaleString()
      ])
    ]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `hibachi-bookings-${format(new Date(), 'yyyy-MM-dd')}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Update booking status
  const updateBookingStatus = async (bookingId: string, newStatus: 'confirmed' | 'cancelled') => {
    try {
      // In production, this would be an API call
      setBookings(prev =>
        prev.map(booking =>
          booking.id === bookingId ? { ...booking, status: newStatus } : booking
        )
      )

      // Show success message (you could add a toast notification here)
      console.log(`Booking ${bookingId} updated to ${newStatus}`)
    } catch (error) {
      console.error('Failed to update booking:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'cancelled':
        return 'bg-red-100 text-red-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🍤 MyHibachi Admin Dashboard</h1>
          <p className="text-gray-600">Manage your hibachi bookings and customer data</p>
        </div>
        <button
          onClick={exportToCSV}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
        >
          <span>📊 Export CSV</span>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const IconComponent = stat.icon
          return (
            <div key={index} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  <p
                    className={`text-sm mt-1 ${stat.change.includes('+') ? 'text-green-600' : stat.change.includes('needed') ? 'text-red-600' : 'text-gray-500'}`}
                  >
                    {stat.change}
                  </p>
                </div>
                <div className={`${stat.color} bg-opacity-10 p-3 rounded-lg`}>
                  <IconComponent className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <span>🔍</span>
            <span>Filter Bookings</span>
          </h2>
          <div className="text-sm text-gray-500">
            {filteredBookings.length} of {bookings.length} bookings shown
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="cancelled">Cancelled</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Event Date</label>
            <input
              type="date"
              value={dateFilter}
              onChange={e => setDateFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setStatusFilter('all')
                setDateFilter('')
              }}
              className="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Recent Bookings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">📋 Booking Management</h2>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading bookings...</p>
          </div>
        ) : filteredBookings.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-6xl mb-4">📭</div>
            <p className="text-gray-500 text-lg">No bookings found</p>
            <p className="text-gray-400 text-sm mt-2">
              {statusFilter !== 'all' || dateFilter
                ? 'Try adjusting your filters'
                : 'Bookings will appear here once customers start booking'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Booking Details
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Event Info
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredBookings.map(booking => (
                  <tr key={booking.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm">
                        <div className="font-medium text-gray-900 font-mono text-xs">
                          {booking.id}
                        </div>
                        <div className="text-gray-500">
                          Created: {format(new Date(booking.createdAt), 'MMM dd, yyyy HH:mm')}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="font-medium text-gray-900">{booking.customerName}</div>
                        <div className="text-gray-500">{booking.customerEmail}</div>
                        <div className="text-gray-500">{booking.customerPhone}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="font-medium text-gray-900">
                          📅 {format(new Date(booking.eventDate), 'MMM dd, yyyy')}
                        </div>
                        <div className="text-gray-500">🕐 {booking.eventTime}</div>
                        <div className="text-gray-500">👥 {booking.guestCount} guests</div>
                        <div className="text-xs text-gray-400 mt-1">{booking.venueAddress}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(booking.status)}`}
                      >
                        {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="space-y-1">
                        {booking.status === 'pending' && (
                          <>
                            <button
                              onClick={() => updateBookingStatus(booking.id, 'confirmed')}
                              className="block w-full bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs transition-colors"
                            >
                              ✅ Confirm
                            </button>
                            <button
                              onClick={() => updateBookingStatus(booking.id, 'cancelled')}
                              className="block w-full bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs transition-colors"
                            >
                              ❌ Cancel
                            </button>
                          </>
                        )}
                        {booking.status === 'confirmed' && (
                          <button
                            onClick={() => updateBookingStatus(booking.id, 'cancelled')}
                            className="block w-full bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs transition-colors"
                          >
                            ❌ Cancel
                          </button>
                        )}
                        <a
                          href={`mailto:${booking.customerEmail}?subject=Hibachi Booking ${booking.id}&body=Hello ${booking.customerName},%0D%0A%0D%0ARegarding your hibachi booking for ${format(new Date(booking.eventDate), 'MMM dd, yyyy')} at ${booking.eventTime}...`}
                          className="block w-full bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs transition-colors text-center"
                        >
                          ✉️ Email
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
