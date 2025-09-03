'use client'

import { useState } from 'react'
import { Search, User, Calendar, MapPin, DollarSign } from 'lucide-react'

interface BookingData {
  id: string
  customerName: string
  customerEmail: string
  eventDate: string
  eventTime: string
  guestCount: number
  venueAddress: string
  totalAmount: number
  depositPaid: boolean
  depositAmount: number
  remainingBalance: number
  services: Array<{
    name: string
    price: number
    quantity: number
  }>
}

interface BookingLookupProps {
  onBookingFound: (booking: BookingData | null) => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
}

// Mock booking data - in production, this would come from your database
const mockBookings: BookingData[] = [
  {
    id: 'MH-20250830-AB12',
    customerName: 'John Smith',
    customerEmail: 'john.smith@email.com',
    eventDate: '2025-09-15',
    eventTime: '6:00 PM',
    guestCount: 12,
    venueAddress: '123 Main St, Sacramento CA 95825',
    totalAmount: 850.0,
    depositPaid: false,
    depositAmount: 100.0,
    remainingBalance: 750.0,
    services: [
      { name: 'Hibachi Chef Service', price: 600, quantity: 1 },
      { name: 'Premium Ingredients', price: 150, quantity: 1 },
      { name: 'Table Setup', price: 100, quantity: 1 }
    ]
  },
  {
    id: 'MH-20250825-CD34',
    customerName: 'Sarah Johnson',
    customerEmail: 'sarah.j@email.com',
    eventDate: '2025-09-20',
    eventTime: '7:00 PM',
    guestCount: 8,
    venueAddress: '456 Oak Ave, Davis CA 95616',
    totalAmount: 680.0,
    depositPaid: true,
    depositAmount: 100.0,
    remainingBalance: 580.0,
    services: [
      { name: 'Hibachi Chef Service', price: 480, quantity: 1 },
      { name: 'Standard Ingredients', price: 120, quantity: 1 },
      { name: 'Table Setup', price: 80, quantity: 1 }
    ]
  },
  {
    id: 'MH-20250828-EF56',
    customerName: 'Mike Davis',
    customerEmail: 'mike.davis@email.com',
    eventDate: '2025-09-10',
    eventTime: '6:30 PM',
    guestCount: 15,
    venueAddress: '789 Pine St, Elk Grove CA 95624',
    totalAmount: 950.0,
    depositPaid: true,
    depositAmount: 100.0,
    remainingBalance: 850.0,
    services: [
      { name: 'Hibachi Chef Service', price: 750, quantity: 1 },
      { name: 'Premium Ingredients', price: 200, quantity: 1 }
    ]
  }
]

export default function BookingLookup({
  onBookingFound,
  isLoading,
  setIsLoading
}: BookingLookupProps) {
  const [searchType, setSearchType] = useState<'booking-id' | 'email'>('booking-id')
  const [searchQuery, setSearchQuery] = useState('')
  const [foundBooking, setFoundBooking] = useState<BookingData | null>(null)
  const [searchError, setSearchError] = useState('')

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchError('Please enter a search term')
      return
    }

    setIsLoading(true)
    setSearchError('')

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000))

    try {
      let booking = null

      if (searchType === 'booking-id') {
        booking = mockBookings.find(b => b.id.toLowerCase().includes(searchQuery.toLowerCase()))
      } else {
        booking = mockBookings.find(
          b =>
            b.customerEmail.toLowerCase().includes(searchQuery.toLowerCase()) ||
            b.customerName.toLowerCase().includes(searchQuery.toLowerCase())
        )
      }

      if (booking) {
        setFoundBooking(booking)
        onBookingFound(booking)
        setSearchError('')
      } else {
        setFoundBooking(null)
        onBookingFound(null)
        setSearchError('No booking found. Please check your information and try again.')
      }
    } catch (error) {
      setSearchError('Error searching for booking. Please try again.')
      console.error('Search error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <Search className="w-5 h-5 mr-2 text-red-600" />
        Find Your Booking
      </h3>

      {/* Search Type Selection */}
      <div className="mb-4">
        <div className="flex space-x-4 mb-3">
          <label className="flex items-center">
            <input
              type="radio"
              name="searchType"
              value="booking-id"
              checked={searchType === 'booking-id'}
              onChange={e => setSearchType(e.target.value as 'booking-id' | 'email')}
              className="mr-2 text-red-600 focus:ring-red-500"
            />
            <span className="text-sm">Booking ID</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="searchType"
              value="email"
              checked={searchType === 'email'}
              onChange={e => setSearchType(e.target.value as 'booking-id' | 'email')}
              className="mr-2 text-red-600 focus:ring-red-500"
            />
            <span className="text-sm">Email/Name</span>
          </label>
        </div>
      </div>

      {/* Search Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {searchType === 'booking-id' ? 'Enter Booking ID' : 'Enter Email or Name'}
        </label>
        <div className="flex space-x-2">
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              searchType === 'booking-id'
                ? 'e.g., MH-20250830-AB12'
                : 'Enter email or customer name'
            }
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Search Error */}
      {searchError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{searchError}</p>
        </div>
      )}

      {/* Found Booking Display */}
      {foundBooking && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center mb-3">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
              <User className="w-4 h-4 text-green-600" />
            </div>
            <div>
              <h4 className="font-medium text-green-900">{foundBooking.customerName}</h4>
              <p className="text-sm text-green-700">{foundBooking.customerEmail}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-2 text-sm text-green-800">
            <div className="flex items-center">
              <Calendar className="w-4 h-4 mr-2" />
              <span>
                {foundBooking.eventDate} at {foundBooking.eventTime}
              </span>
            </div>
            <div className="flex items-center">
              <MapPin className="w-4 h-4 mr-2" />
              <span>{foundBooking.venueAddress}</span>
            </div>
            <div className="flex items-center">
              <DollarSign className="w-4 h-4 mr-2" />
              <span>Total: ${foundBooking.totalAmount.toFixed(2)}</span>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-green-200">
            <div className="text-xs text-green-600 uppercase tracking-wide mb-1">
              Payment Status
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Deposit Status:</span>
              <span
                className={`text-sm font-medium px-2 py-1 rounded ${
                  foundBooking.depositPaid
                    ? 'bg-green-200 text-green-800'
                    : 'bg-yellow-200 text-yellow-800'
                }`}
              >
                {foundBooking.depositPaid ? 'Paid' : 'Pending'}
              </span>
            </div>
            <div className="flex justify-between items-center mt-1">
              <span className="text-sm">Remaining Balance:</span>
              <span className="text-sm font-medium">
                ${foundBooking.remainingBalance.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Demo Booking IDs */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Demo Booking IDs for Testing:</h4>
        <div className="text-xs text-blue-700 space-y-1">
          <div>
            • <code className="bg-blue-100 px-1 rounded">MH-20250830-AB12</code> - No deposit paid
          </div>
          <div>
            • <code className="bg-blue-100 px-1 rounded">MH-20250825-CD34</code> - Deposit paid
          </div>
          <div>
            • <code className="bg-blue-100 px-1 rounded">MH-20250828-EF56</code> - Deposit paid
          </div>
        </div>
        <div className="mt-2 text-xs text-blue-600">
          Or try email: <code className="bg-blue-100 px-1 rounded">john.smith@email.com</code>
        </div>
      </div>
    </div>
  )
}
