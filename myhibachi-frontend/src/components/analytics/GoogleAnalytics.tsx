'use client';

import Script from 'next/script';

interface GoogleAnalyticsProps {
  measurementId: string;
}

// Analytics event types
interface BookingDetails {
  booking_type?: string;
  service_area?: string;
  guest_count?: number;
  event_type?: string;
  location?: string;
  estimated_value?: number;
}

interface QuoteDetails {
  event_type?: string;
  location?: string;
  estimated_value?: number;
  guest_count?: number;
}

interface BookingData {
  booking_id: string;
  estimated_value?: number;
  event_type?: string;
  location?: string;
  guest_count?: number;
}

interface AnalyticsParameters {
  event_category?: string;
  event_label?: string;
  value?: number;
  currency?: string;
  custom_parameter_1?: string;
  custom_parameter_2?: string;
  custom_parameter_3?: string;
  engagement_time_msec?: number;
  [key: string]: string | number | undefined;
}

export default function GoogleAnalytics({ measurementId }: GoogleAnalyticsProps) {
  // Don't render analytics if measurement ID is missing or placeholder
  if (!measurementId || measurementId === 'G-XXXXXXXXXX' || measurementId.trim() === '') {
    console.warn(
      '[GoogleAnalytics] Measurement ID not configured. Please set NEXT_PUBLIC_GA_MEASUREMENT_ID in your environment variables.',
    );
    return null;
  }

  return (
    <>
      {/* Google Analytics 4 */}
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${measurementId}`}
        strategy="afterInteractive"
      />
      <Script id="google-analytics" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          gtag('config', '${measurementId}', {
            page_title: document.title,
            page_location: window.location.href,
          });

          // Enhanced ecommerce and conversion tracking
          gtag('config', '${measurementId}', {
            custom_map: {
              'custom_parameter_1': 'booking_type',
              'custom_parameter_2': 'service_area',
              'custom_parameter_3': 'guest_count'
            }
          });

          // Track page views with enhanced data
          function trackPageView(url, title) {
            gtag('event', 'page_view', {
              page_title: title,
              page_location: url,
              page_referrer: document.referrer
            });
          }

          // Track booking form interactions
          function trackBookingInteraction(action, details = {}) {
            gtag('event', 'booking_interaction', {
              event_category: 'Booking Form',
              event_label: action,
              custom_parameter_1: details.booking_type || 'unknown',
              custom_parameter_2: details.service_area || 'unknown',
              custom_parameter_3: details.guest_count || 0
            });
          }

          // Track quote requests
          function trackQuoteRequest(details = {}) {
            gtag('event', 'generate_lead', {
              event_category: 'Quote Request',
              event_label: 'Quote Calculator',
              value: details.estimated_value || 0,
              currency: 'USD',
              custom_parameter_1: details.event_type || 'unknown',
              custom_parameter_2: details.location || 'unknown'
            });
          }

          // Track successful bookings (conversion)
          function trackBookingConversion(bookingData) {
            gtag('event', 'purchase', {
              transaction_id: bookingData.booking_id,
              value: bookingData.estimated_value || 500,
              currency: 'USD',
              event_category: 'Booking',
              event_label: 'Booking Completed',
              custom_parameter_1: bookingData.event_type || 'hibachi_catering',
              custom_parameter_2: bookingData.location || 'bay_area',
              custom_parameter_3: bookingData.guest_count || 0
            });
          }

          // Track contact form submissions
          function trackContactSubmission(formType = 'contact') {
            gtag('event', 'generate_lead', {
              event_category: 'Contact Form',
              event_label: formType,
              value: 100
            });
          }

          // Track phone calls (when phone number is clicked)
          function trackPhoneCall() {
            gtag('event', 'phone_call', {
              event_category: 'Contact',
              event_label: 'Phone Number Clicked',
              value: 150
            });
          }

          // Track social media interactions
          function trackSocialInteraction(platform, action) {
            gtag('event', 'social_interaction', {
              event_category: 'Social Media',
              event_label: platform + '_' + action,
              social_network: platform,
              social_action: action
            });
          }

          // Make functions globally available
          window.gtag = gtag;
          window.trackPageView = trackPageView;
          window.trackBookingInteraction = trackBookingInteraction;
          window.trackQuoteRequest = trackQuoteRequest;
          window.trackBookingConversion = trackBookingConversion;
          window.trackContactSubmission = trackContactSubmission;
          window.trackPhoneCall = trackPhoneCall;
          window.trackSocialInteraction = trackSocialInteraction;
        `}
      </Script>
    </>
  );
}

// Hook for tracking events in React components
export function useAnalytics() {
  const trackEvent = (eventName: string, parameters: AnalyticsParameters = {}) => {
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', eventName, parameters);
    }
  };

  const trackBookingStep = (step: string, details: BookingDetails = {}) => {
    trackEvent('booking_step_completed', {
      event_category: 'Booking Form',
      event_label: step,
      ...details,
    });
  };

  const trackQuoteCalculated = (quoteValue: number, details: QuoteDetails = {}) => {
    trackEvent('quote_calculated', {
      event_category: 'Quote Calculator',
      event_label: 'Quote Generated',
      value: quoteValue,
      currency: 'USD',
      ...details,
    });
  };

  const trackPageEngagement = (action: string, element: string) => {
    trackEvent('engagement', {
      event_category: 'Page Interaction',
      event_label: `${element}_${action}`,
      engagement_time_msec: Date.now(),
    });
  };

  return {
    trackEvent,
    trackBookingStep,
    trackQuoteCalculated,
    trackPageEngagement,
  };
}

// TypeScript declarations
declare global {
  interface Window {
    gtag: (command: string, ...args: unknown[]) => void;
    trackPageView: (url: string, title: string) => void;
    trackBookingInteraction: (action: string, details?: BookingDetails) => void;
    trackQuoteRequest: (details?: QuoteDetails) => void;
    trackBookingConversion: (bookingData: BookingData) => void;
    trackContactSubmission: (formType?: string) => void;
    trackPhoneCall: () => void;
    trackSocialInteraction: (platform: string, action: string) => void;
  }
}
