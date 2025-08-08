'use client'

import React, { Suspense } from 'react'
import { format } from 'date-fns'
import { useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Star, ExternalLink, Download, MessageSquare, Gift } from 'lucide-react'

interface BookingDetails {
  bookingId: string
  customerName: string
  customerEmail: string
  eventDate: string
  eventTime: string
  guestCount: number
  venueAddress: string
  createdAt: string
}

const REVIEW_PLATFORMS = [
  {
    name: 'Google Reviews',
    icon: '🔍',
    url: 'https://g.page/r/YOUR_GOOGLE_BUSINESS_ID/review',
    color: 'hover:bg-blue-50 hover:border-blue-300',
    description: 'Most visible to customers',
    reward: '5% off next booking'
  },
  {
    name: 'Yelp',
    icon: '🌟',
    url: 'https://www.yelp.com/writeareview/biz/YOUR_YELP_BUSINESS_ID',
    color: 'hover:bg-red-50 hover:border-red-300',
    description: 'Foodie community favorite',
    reward: 'Monthly free hibachi'
  },
  {
    name: 'Facebook',
    icon: '📘',
    url: 'https://www.facebook.com/YOUR_FACEBOOK_PAGE/reviews',
    color: 'hover:bg-blue-50 hover:border-blue-300',
    description: 'Share with friends',
    reward: 'Bonus discount'
  },
  {
    name: 'Quick Review',
    icon: '💬',
    url: '/review',
    color: 'hover:bg-orange-50 hover:border-orange-300',
    description: 'Leave feedback here',
    reward: 'Instant rewards'
  }
]

function BookingSuccessContent() {
  const searchParams = useSearchParams()
  const [booking, setBooking] = useState<BookingDetails | null>(null)
  const [isGeneratingInvoice, setIsGeneratingInvoice] = useState(false)

  useEffect(() => {
    // In production, fetch booking details from API using bookingId
    const bookingId = searchParams?.get('id')
    
    if (bookingId) {
      // Mock booking data (in production, fetch from API)
      const mockBooking: BookingDetails = {
        bookingId,
        customerName: 'John Doe',
        customerEmail: 'john@example.com',
        eventDate: '2025-08-15',
        eventTime: '6PM',
        guestCount: 12,
        venueAddress: '123 Main St, Anytown, CA 12345',
        createdAt: new Date().toISOString()
      }
      setBooking(mockBooking)
    }
  }, [searchParams])

  const handleDownloadInvoice = async () => {
    if (!booking) return
    
    setIsGeneratingInvoice(true)
    
    try {
      // In production, call API to generate PDF invoice
      const response = await fetch(`/api/v1/bookings/${booking.bookingId}/invoice`, {
        method: 'GET',
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `MyHibachi-Invoice-${booking.bookingId}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        // Fallback to opening invoice page
        window.open(`/invoice/${booking.bookingId}`, '_blank')
      }
    } catch (error) {
      console.error('Error downloading invoice:', error)
      // Fallback to opening invoice page
      window.open(`/invoice/${booking.bookingId}`, '_blank')
    } finally {
      setIsGeneratingInvoice(false)
    }
  }

  const handleReviewClick = (platform: { url: string; name: string }) => {
    if (platform.url.startsWith('http')) {
      window.open(platform.url, '_blank')
    } else {
      window.location.href = platform.url
    }
  }

  const generateCalendarLink = () => {
    if (!booking) return ''
    
    const startDate = new Date(`${booking.eventDate}T${booking.eventTime === '12PM' ? '12:00' : booking.eventTime === '3PM' ? '15:00' : booking.eventTime === '6PM' ? '18:00' : '21:00'}:00`)
    const endDate = new Date(startDate.getTime() + 3 * 60 * 60 * 1000) // 3 hours later
    
    const title = encodeURIComponent('MyHibachi Private Chef Experience')
    const details = encodeURIComponent(`Private hibachi chef experience for ${booking.guestCount} guests.\n\nVenue: ${booking.venueAddress}\n\nBooking ID: ${booking.bookingId}`)
    const location = encodeURIComponent(booking.venueAddress)
    
    const startTime = startDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
    const endTime = endDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
    
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${startTime}/${endTime}&details=${details}&location=${location}`
  }

  const downloadICalFile = () => {
    if (!booking) return
    
    const startDate = new Date(`${booking.eventDate}T${booking.eventTime === '12PM' ? '12:00' : booking.eventTime === '3PM' ? '15:00' : booking.eventTime === '6PM' ? '18:00' : '21:00'}:00`)
    const endDate = new Date(startDate.getTime() + 3 * 60 * 60 * 1000)
    
    const icalContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MyHibachi//Booking System//EN
BEGIN:VEVENT
UID:${booking.bookingId}@myhibachi.com
DTSTART:${startDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z
DTEND:${endDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z
SUMMARY:MyHibachi Private Chef Experience
DESCRIPTION:Private hibachi chef experience for ${booking.guestCount} guests.\\n\\nBooking ID: ${booking.bookingId}
LOCATION:${booking.venueAddress}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR`

    const blob = new Blob([icalContent], { type: 'text/calendar' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `hibachi-booking-${booking.bookingId}.ics`
    link.click()
    URL.revokeObjectURL(url)
  }

  if (!booking) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading booking details...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          {/* Success Header */}
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🎉</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Booking Confirmed!
            </h1>
            <p className="text-lg text-gray-600">
              Your hibachi experience has been successfully booked
            </p>
          </div>

          {/* Booking Details Card */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden mb-6">
            <div className="bg-gradient-to-r from-red-600 to-orange-600 text-white p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">Booking Summary</h2>
                  <p className="text-red-100">Confirmation #{booking.bookingId}</p>
                </div>
                <div className="text-4xl">🍤</div>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Event Details */}
              <div className="border-b border-gray-200 pb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">📅 Event Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-700">Date</div>
                    <div className="text-lg text-gray-900">
                      {format(new Date(booking.eventDate), 'EEEE, MMMM dd, yyyy')}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-700">Time</div>
                    <div className="text-lg text-gray-900">{booking.eventTime}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-700">Guests</div>
                    <div className="text-lg text-gray-900">{booking.guestCount} people</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-700">Duration</div>
                    <div className="text-lg text-gray-900">~3 hours</div>
                  </div>
                </div>
              </div>

              {/* Customer Details */}
              <div className="border-b border-gray-200 pb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">👤 Customer Information</h3>
                <div className="space-y-2">
                  <div>
                    <span className="text-sm font-medium text-gray-700">Name: </span>
                    <span className="text-gray-900">{booking.customerName}</span>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-700">Email: </span>
                    <span className="text-gray-900">{booking.customerEmail}</span>
                  </div>
                </div>
              </div>

              {/* Venue Details */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🎪 Venue Location</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-900">{booking.venueAddress}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <button
              onClick={() => window.open(generateCalendarLink(), '_blank')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
            >
              <span>📅</span>
              <span>Add to Google Calendar</span>
            </button>
            
            <button
              onClick={downloadICalFile}
              className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
            >
              <span>📲</span>
              <span>Download .ics File</span>
            </button>
          </div>

          {/* Download Invoice Button */}
          <div className="mb-6">
            <button
              onClick={handleDownloadInvoice}
              disabled={isGeneratingInvoice}
              className="w-full bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>{isGeneratingInvoice ? 'Generating Invoice...' : 'Download Invoice (PDF)'}</span>
            </button>
          </div>

          {/* Review Request Section */}
          <Card className="mb-6">
            <CardHeader className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white">
              <CardTitle className="text-xl flex items-center justify-center gap-2">
                <Star className="w-5 h-5" />
                Help Others Discover MyHibachi
                <Star className="w-5 h-5" />
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold mb-2">Share Your Experience & Get Rewarded!</h3>
                <p className="text-gray-600">
                  Your feedback helps us improve and helps other families discover the authentic hibachi experience.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {REVIEW_PLATFORMS.map((platform) => (
                  <Button
                    key={platform.name}
                    variant="outline"
                    className={`h-auto p-4 flex flex-col items-center gap-2 ${platform.color} transition-all`}
                    onClick={() => handleReviewClick(platform)}
                  >
                    <div className="text-2xl">{platform.icon}</div>
                    <div className="font-semibold">{platform.name}</div>
                    <div className="text-xs text-center text-gray-500">
                      {platform.description}
                    </div>
                    <Badge className="bg-green-100 text-green-800 text-xs">
                      <Gift className="w-3 h-3 mr-1" />
                      {platform.reward}
                    </Badge>
                    {platform.url.startsWith('http') ? (
                      <ExternalLink className="w-4 h-4" />
                    ) : (
                      <MessageSquare className="w-4 h-4" />
                    )}
                  </Button>
                ))}
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                  📸 Photo Contest Bonus!
                </h4>
                <p className="text-blue-700 text-sm">
                  Share a photo of your hibachi experience on social media and tag us 
                  <strong> @MyHibachi</strong> or <strong>#MyHibachiExperience</strong> for an extra 
                  <strong> 15% discount</strong> on your next booking!
                </p>
              </div>
            </CardContent>
          </Card>

          {/* What's Next Section */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">✨ What Happens Next?</h3>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="bg-green-100 text-green-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</div>
                <div>
                  <div className="font-medium text-gray-900">Confirmation Email</div>
                  <div className="text-sm text-gray-600">You&apos;ll receive a confirmation email within 5 minutes</div>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</div>
                <div>
                  <div className="font-medium text-gray-900">Chef Assignment</div>
                  <div className="text-sm text-gray-600">We&apos;ll assign your hibachi chef and confirm within 24 hours</div>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="bg-purple-100 text-purple-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</div>
                <div>
                  <div className="font-medium text-gray-900">Pre-Event Contact</div>
                  <div className="text-sm text-gray-600">Your chef will contact you 24-48 hours before your event</div>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="bg-red-100 text-red-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">4</div>
                <div>
                  <div className="font-medium text-gray-900">Event Day</div>
                  <div className="text-sm text-gray-600">Enjoy your amazing hibachi experience!</div>
                </div>
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-2xl p-6 text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Need Help?</h3>
            <p className="text-gray-600 mb-4">
              If you have any questions or need to make changes to your booking
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <a
                href="mailto:bookings@myhibachi.com"
                className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors inline-flex items-center justify-center space-x-2"
              >
                <span>✉️</span>
                <span>bookings@myhibachi.com</span>
              </a>
              <a
                href="tel:+15551234567"
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors inline-flex items-center justify-center space-x-2"
              >
                <span>📞</span>
                <span>(555) 123-4567</span>
              </a>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center mt-8">
            <Link
              href="/"
              className="text-red-600 hover:text-red-700 font-medium transition-colors"
            >
              ← Back to MyHibachi Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function BookingSuccess() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
      <BookingSuccessContent />
    </Suspense>
  )
}
