'use client';

import { format } from 'date-fns';
import { Download, ExternalLink, Gift, MessageSquare, Star } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import React, { Suspense, useEffect, useState } from 'react';

import { useProtectedPhone, useProtectedPaymentEmail } from '@/components/ui/ProtectedPhone';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { logger } from '@/lib/logger';

interface BookingDetails {
  bookingId: string;
  customerName: string;
  customerEmail: string;
  eventDate: string;
  eventTime: string;
  guestCount: number;
  venueAddress: string;
  createdAt: string;
}

const REVIEW_PLATFORMS = [
  {
    name: 'Google Reviews',
    icon: '🔍',
    url: 'https://g.page/r/YOUR_GOOGLE_BUSINESS_ID/review',
    color: 'hover:bg-blue-50 hover:border-blue-300',
    description: 'Most visible to customers',
    reward: '5% off next booking',
  },
  {
    name: 'Yelp',
    icon: '🌟',
    url: 'https://www.yelp.com/writeareview/biz/YOUR_YELP_BUSINESS_ID',
    color: 'hover:bg-red-50 hover:border-red-300',
    description: 'Foodie community favorite',
    reward: 'Monthly free hibachi',
  },
  {
    name: 'Facebook',
    icon: '📘',
    url: 'https://www.facebook.com/people/My-hibachi/61577483702847/',
    color: 'hover:bg-blue-50 hover:border-blue-300',
    description: 'Share with friends',
    reward: 'Bonus discount',
  },
  {
    name: 'Quick Review',
    icon: '💬',
    url: '/review',
    color: 'hover:bg-orange-50 hover:border-orange-300',
    description: 'Leave feedback here',
    reward: 'Instant rewards',
  },
];

function BookingSuccessContent() {
  // Anti-scraper protected contact info
  const { formatted: protectedPhone, tel: protectedTel } = useProtectedPhone();
  const { email: protectedEmail } = useProtectedPaymentEmail();

  const searchParams = useSearchParams();
  const [booking, setBooking] = useState<BookingDetails | null>(null);
  const [isGeneratingInvoice, setIsGeneratingInvoice] = useState(false);

  useEffect(() => {
    // In production, fetch booking details from API using bookingId
    const bookingId = searchParams?.get('id');

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
        createdAt: new Date().toISOString(),
      };
      setBooking(mockBooking);
    }
  }, [searchParams]);

  const handleDownloadInvoice = async () => {
    if (!booking) return;

    setIsGeneratingInvoice(true);

    try {
      // In production, call API to generate PDF invoice
      const response = await fetch(`/api/v1/bookings/${booking.bookingId}/invoice`, {
        method: 'GET',
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `MyHibachi-Invoice-${booking.bookingId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // Fallback to opening invoice page
        window.open(`/invoice/${booking.bookingId}`, '_blank');
      }
    } catch (error) {
      logger.error('Error downloading invoice', error as Error);
      // Fallback to opening invoice page
      window.open(`/invoice/${booking.bookingId}`, '_blank');
    } finally {
      setIsGeneratingInvoice(false);
    }
  };

  const handleReviewClick = (platform: { url: string; name: string }) => {
    if (platform.url.startsWith('http')) {
      window.open(platform.url, '_blank');
    } else {
      window.location.href = platform.url;
    }
  };

  const generateCalendarLink = () => {
    if (!booking) return '';

    const startDate = new Date(
      `${booking.eventDate}T${
        booking.eventTime === '12PM'
          ? '12:00'
          : booking.eventTime === '3PM'
            ? '15:00'
            : booking.eventTime === '6PM'
              ? '18:00'
              : '21:00'
      }:00`,
    );
    const endDate = new Date(startDate.getTime() + 3 * 60 * 60 * 1000); // 3 hours later

    const title = encodeURIComponent('MyHibachi Private Chef Experience');
    const details = encodeURIComponent(
      `Private hibachi chef experience for ${booking.guestCount} guests.\n\nVenue: ${booking.venueAddress}\n\nBooking ID: ${booking.bookingId}`,
    );
    const location = encodeURIComponent(booking.venueAddress);

    const startTime = startDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    const endTime = endDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';

    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${startTime}/${endTime}&details=${details}&location=${location}`;
  };

  const downloadICalFile = () => {
    if (!booking) return;

    const startDate = new Date(
      `${booking.eventDate}T${
        booking.eventTime === '12PM'
          ? '12:00'
          : booking.eventTime === '3PM'
            ? '15:00'
            : booking.eventTime === '6PM'
              ? '18:00'
              : '21:00'
      }:00`,
    );
    const endDate = new Date(startDate.getTime() + 3 * 60 * 60 * 1000);

    const icalContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MyHibachi//Booking System//EN
BEGIN:VEVENT
UID:${booking.bookingId}@myhibachi.com
DTSTART:${startDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z
DTEND:${endDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z
SUMMARY:MyHibachi Private Chef Experience
DESCRIPTION:Private hibachi chef experience for ${booking.guestCount} guests.\\n\\nBooking ID: ${
      booking.bookingId
    }
LOCATION:${booking.venueAddress}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR`;

    const blob = new Blob([icalContent], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `hibachi-booking-${booking.bookingId}.ics`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!booking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 animate-spin rounded-full border-b-2 border-red-600"></div>
          <p className="mt-4 text-gray-600">Loading booking details...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen">
        {/* Success Hero Section with Company Background */}
        <section className="page-hero-background py-20 text-center text-white">
          <div className="mx-auto max-w-4xl px-4">
            <div className="mb-6 text-6xl">🎉</div>
            <h1 className="mb-6 text-5xl font-bold">Booking Confirmed!</h1>
            <p className="mb-8 text-xl text-gray-200">
              Your hibachi experience has been successfully booked
            </p>
            <div className="text-lg">
              <span className="rounded-full bg-green-600 px-4 py-2 text-white">
                Confirmation Complete
              </span>
            </div>
          </div>
        </section>

        {/* Success Details Section */}
        <div className="section-background py-12">
          <div className="mx-auto max-w-2xl px-4">
            {/* Booking Details Card */}
            <div className="mb-6 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg">
              <div className="bg-gradient-to-r from-red-600 to-orange-600 p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold">Booking Summary</h2>
                    <p className="text-red-100">Confirmation #{booking.bookingId}</p>
                  </div>
                  <div className="text-4xl">🍤</div>
                </div>
              </div>

              <div className="space-y-6 p-6">
                {/* Event Details */}
                <div className="border-b border-gray-200 pb-6">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">📅 Event Details</h3>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
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
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">
                    👤 Customer Information
                  </h3>
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
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">🎪 Venue Location</h3>
                  <div className="rounded-lg bg-gray-50 p-4">
                    <p className="text-gray-900">{booking.venueAddress}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2">
              <button
                onClick={() => window.open(generateCalendarLink(), '_blank')}
                className="flex items-center justify-center space-x-2 rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700"
              >
                <span>📅</span>
                <span>Add to Google Calendar</span>
              </button>

              <button
                onClick={downloadICalFile}
                className="flex items-center justify-center space-x-2 rounded-lg bg-purple-600 px-6 py-3 font-medium text-white transition-colors hover:bg-purple-700"
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
                className="flex w-full items-center justify-center space-x-2 rounded-lg bg-gray-600 px-6 py-3 font-medium text-white transition-colors hover:bg-gray-700 disabled:bg-gray-400"
              >
                <Download className="h-4 w-4" />
                <span>
                  {isGeneratingInvoice ? 'Generating Invoice...' : 'Download Invoice (PDF)'}
                </span>
              </button>
            </div>

            {/* Review Request Section */}
            <Card className="mb-6">
              <CardHeader className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white">
                <CardTitle className="flex items-center justify-center gap-2 text-xl">
                  <Star className="h-5 w-5" />
                  Help Others Discover MyHibachi
                  <Star className="h-5 w-5" />
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="mb-6 text-center">
                  <h3 className="mb-2 text-lg font-semibold">
                    Share Your Experience & Get Rewarded!
                  </h3>
                  <p className="text-gray-600">
                    Your feedback helps us improve and helps other families discover the authentic
                    hibachi experience.
                  </p>
                </div>

                <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                  {REVIEW_PLATFORMS.map((platform) => (
                    <Button
                      key={platform.name}
                      variant="outline"
                      className={`flex h-auto flex-col items-center gap-2 p-4 ${platform.color} transition-all`}
                      onClick={() => handleReviewClick(platform)}
                    >
                      <div className="text-2xl">{platform.icon}</div>
                      <div className="font-semibold">{platform.name}</div>
                      <div className="text-center text-xs text-gray-500">
                        {platform.description}
                      </div>
                      <Badge className="bg-green-100 text-xs text-green-800">
                        <Gift className="mr-1 h-3 w-3" />
                        {platform.reward}
                      </Badge>
                      {platform.url.startsWith('http') ? (
                        <ExternalLink className="h-4 w-4" />
                      ) : (
                        <MessageSquare className="h-4 w-4" />
                      )}
                    </Button>
                  ))}
                </div>

                <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                  <h4 className="mb-2 flex items-center gap-2 font-semibold text-blue-800">
                    📸 Photo Contest Bonus!
                  </h4>
                  <p className="text-sm text-blue-700">
                    Share a photo of your hibachi experience on social media and tag us
                    <strong> @MyHibachi</strong> or <strong>#MyHibachiExperience</strong> for an
                    extra
                    <strong> 15% discount</strong> on your next booking!
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* What's Next Section */}
            <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-lg">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">✨ What Happens Next?</h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-green-100 text-sm font-bold text-green-800">
                    1
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">Confirmation Email</div>
                    <div className="text-sm text-gray-600">
                      You&apos;ll receive a confirmation email within 5 minutes
                    </div>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-800">
                    2
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">Chef Assignment</div>
                    <div className="text-sm text-gray-600">
                      We&apos;ll assign your hibachi chef and confirm within 24 hours
                    </div>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-purple-100 text-sm font-bold text-purple-800">
                    3
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">Pre-Event Contact</div>
                    <div className="text-sm text-gray-600">
                      Your chef will contact you 24-48 hours before your event
                    </div>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-sm font-bold text-red-800">
                    4
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">Event Day</div>
                    <div className="text-sm text-gray-600">
                      Enjoy your amazing hibachi experience!
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="rounded-2xl bg-gradient-to-r from-gray-50 to-gray-100 p-6 text-center">
              <h3 className="mb-2 text-lg font-semibold text-gray-900">Need Help?</h3>
              <p className="mb-4 text-gray-600">
                If you have any questions or need to make changes to your booking
              </p>
              <div className="flex flex-col justify-center gap-3 sm:flex-row">
                <a
                  href={protectedEmail ? `mailto:${protectedEmail}` : '/contact'}
                  className="inline-flex items-center justify-center space-x-2 rounded-lg bg-red-600 px-6 py-2 font-medium text-white transition-colors hover:bg-red-700"
                >
                  <span>✉️</span>
                  <span>{protectedEmail || 'Contact Us'}</span>
                </a>
                <a
                  href={protectedTel ? `tel:${protectedTel}` : '/contact'}
                  className="inline-flex items-center justify-center space-x-2 rounded-lg bg-green-600 px-6 py-2 font-medium text-white transition-colors hover:bg-green-700"
                >
                  <span>📞</span>
                  <span>{protectedPhone || 'Call Us'}</span>
                </a>
              </div>
            </div>

            {/* Footer */}
            <div className="mt-8 text-center">
              <Link
                href="/"
                className="font-medium text-red-600 transition-colors hover:text-red-700"
              >
                ← Back to MyHibachi Home
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function BookingSuccess() {
  return (
    <Suspense
      fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}
    >
      <BookingSuccessContent />
    </Suspense>
  );
}
