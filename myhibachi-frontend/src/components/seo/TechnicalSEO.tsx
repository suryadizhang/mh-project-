// Technical SEO Components for Next.js App Router
// ================================================

import { Metadata } from 'next';

interface TechnicalSEOProps {
  title: string;
  description: string;
  keywords?: string[];
  canonicalUrl?: string;
  openGraph?: {
    title?: string;
    description?: string;
    image?: string;
    type?: 'website' | 'article';
  };
  structuredData?: Record;
  location?: string;
  eventType?: string;
}

// Enhanced metadata generator for perfect SEO
function generateEnhancedMetadata({
  title,
  description,
  keywords = [],
  canonicalUrl,
  openGraph,
  location,
}: TechnicalSEOProps): Metadata {
  const baseUrl = 'https://myhibachi.com';
  const fullCanonicalUrl = canonicalUrl ? `${baseUrl}${canonicalUrl}` : baseUrl;

  return {
    title: `${title} | My Hibachi Catering`,
    description,
    keywords: keywords.join(', '),
    authors: [{ name: 'My Hibachi Catering Team' }],
    creator: 'My Hibachi Catering',
    publisher: 'My Hibachi Catering',

    // Open Graph
    openGraph: {
      title: openGraph?.title || title,
      description: openGraph?.description || description,
      url: fullCanonicalUrl,
      siteName: 'My Hibachi Catering',
      images: [
        {
          url: openGraph?.image || '/images/hibachi-og-default.jpg',
          width: 1200,
          height: 630,
          alt: `${title} - My Hibachi Catering`,
        },
      ],
      locale: 'en_US',
      type: openGraph?.type || 'website',
    },

    // Twitter Cards
    twitter: {
      card: 'summary_large_image',
      title: openGraph?.title || title,
      description: openGraph?.description || description,
      site: '@MyHibachiCatering',
      creator: '@MyHibachiCatering',
      images: [openGraph?.image || '/images/hibachi-og-default.jpg'],
    },

    // Additional metadata
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        'max-video-preview': -1,
        'max-image-preview': 'large',
        'max-snippet': -1,
      },
    },

    // Verification tags
    verification: {
      google: 'your-google-verification-code',
      yandex: 'your-yandex-verification',
      yahoo: 'your-yahoo-verification',
    },

    // Canonical URL
    alternates: {
      canonical: fullCanonicalUrl,
    },

    // Location-specific metadata
    ...(location && {
      other: {
        'geo.region': 'US-CA',
        'geo.placename': location,
        'geo.position': getLocationCoordinates(location),
        ICBM: getLocationCoordinates(location),
      },
    }),
  };
}

// Core Web Vitals optimization metadata helper
function getCoreWebVitalsMetadata() {
  return {
    // Resource hints and preloading
    other: {
      'dns-prefetch': '//fonts.googleapis.com',
      preconnect: '//fonts.gstatic.com',
      'resource-hint': 'preload',
    },
  };
}

// Local Business Schema Component
function LocalBusinessSchema({
  location,
  eventType,
  businessName = 'My Hibachi Catering',
  description,
  url,
}: {
  location: string;
  eventType?: string;
  businessName?: string;
  description?: string;
  url?: string;
}) {
  const coordinates = getLocationCoordinatesDetailed(location);

  const schema = {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    '@id': `${url || 'https://myhibachi.com'}#LocalBusiness`,
    name: businessName,
    description: description || `Professional hibachi catering service in ${location}`,
    url: url || 'https://myhibachi.com',
    telephone: '+1-555-HIBACHI',
    email: 'info@myhibachi.com',

    address: {
      '@type': 'PostalAddress',
      addressLocality: location,
      addressRegion: 'CA',
      addressCountry: 'US',
      postalCode: coordinates.zipCode,
    },

    geo: {
      '@type': 'GeoCoordinates',
      latitude: coordinates.lat,
      longitude: coordinates.lng,
    },

    areaServed: [
      {
        '@type': 'City',
        name: location,
      },
      {
        '@type': 'State',
        name: 'California',
      },
    ],

    serviceType: 'Hibachi Catering',
    priceRange: '$$$',
    paymentAccepted: ['Cash', 'Credit Card', 'Check', 'Venmo', 'Zelle'],
    currenciesAccepted: 'USD',

    openingHours: ['Mo-Su 09:00-22:00'],

    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.9',
      reviewCount: '127',
      bestRating: '5',
      worstRating: '1',
    },

    review: [
      {
        '@type': 'Review',
        author: {
          '@type': 'Person',
          name: 'Sarah M.',
        },
        reviewRating: {
          '@type': 'Rating',
          ratingValue: '5',
        },
        reviewBody: `Amazing hibachi experience in ${location}! The chef was entertaining and the food was delicious.`,
      },
    ],

    hasOfferCatalog: {
      '@type': 'OfferCatalog',
      name: 'Hibachi Catering Services',
      itemListElement: [
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: `${eventType || 'Private'} Hibachi Catering`,
            description: `Professional hibachi catering for ${
              eventType?.toLowerCase() || 'private'
            } events in ${location}`,
          },
        },
      ],
    },

    sameAs: [
      'https://www.facebook.com/myhibachicatering',
      'https://www.instagram.com/myhibachicatering',
      'https://www.yelp.com/biz/my-hibachi-catering',
      'https://www.linkedin.com/company/my-hibachi-catering',
    ],
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(schema, null, 2),
      }}
    />
  );
}

// FAQ Schema Component for rich snippets
function FAQSchema({ faqs }: { faqs: Array }) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(schema, null, 2),
      }}
    />
  );
}

// Breadcrumb Schema Component
function BreadcrumbSchema({ items }: { items: Array }) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: `https://myhibachi.com${item.url}`,
    })),
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(schema, null, 2),
      }}
    />
  );
}

// Event Schema Component
function EventSchema({
  name,
  description,
  location,
  startDate,
  endDate,
  organizer = 'My Hibachi Catering',
}: {
  name: string;
  description: string;
  location: string;
  startDate?: string;
  endDate?: string;
  organizer?: string;
}) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Event',
    name: name,
    description: description,
    startDate: startDate || new Date().toISOString(),
    endDate: endDate || new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(), // 3 hours later
    eventStatus: 'https://schema.org/EventScheduled',
    eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',

    location: {
      '@type': 'Place',
      name: location,
      address: {
        '@type': 'PostalAddress',
        addressLocality: location,
        addressRegion: 'CA',
        addressCountry: 'US',
      },
    },

    organizer: {
      '@type': 'Organization',
      name: organizer,
      url: 'https://myhibachi.com',
    },

    offers: {
      '@type': 'Offer',
      url: 'https://myhibachi.com/booking',
      price: 'Contact for pricing',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
      validFrom: new Date().toISOString(),
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(schema, null, 2),
      }}
    />
  );
}

// Performance monitoring component
function PerformanceMonitoring() {
  return (
    <script
      dangerouslySetInnerHTML={{
        __html: `
          // Core Web Vitals monitoring
          import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
            getCLS(console.log);
            getFID(console.log);
            getFCP(console.log);
            getLCP(console.log);
            getTTFB(console.log);
          });
        `,
      }}
    />
  );
}

// Helper functions
function getLocationCoordinates(location: string): string {
  const coords = {
    'San Francisco': '37.7749,-122.4194',
    'San Jose': '37.3382,-121.8863',
    Oakland: '37.8044,-122.2711',
    'Palo Alto': '37.4419,-122.1430',
    'Mountain View': '37.3861,-122.0839',
    'Santa Clara': '37.3541,-121.9552',
    Sunnyvale: '37.3688,-122.0363',
  };
  return coords[location as keyof typeof coords] || coords['San Jose'];
}

function getLocationCoordinatesDetailed(location: string) {
  const details = {
    'San Francisco': { lat: 37.7749, lng: -122.4194, zipCode: '94102' },
    'San Jose': { lat: 37.3382, lng: -121.8863, zipCode: '95110' },
    Oakland: { lat: 37.8044, lng: -122.2711, zipCode: '94612' },
    'Palo Alto': { lat: 37.4419, lng: -122.143, zipCode: '94301' },
    'Mountain View': { lat: 37.3861, lng: -122.0839, zipCode: '94041' },
    'Santa Clara': { lat: 37.3541, lng: -121.9552, zipCode: '95050' },
    Sunnyvale: { lat: 37.3688, lng: -122.0363, zipCode: '94085' },
  };
  return details[location as keyof typeof details] || details['San Jose'];
}

export type { TechnicalSEOProps };
export {
  BreadcrumbSchema,
  EventSchema,
  FAQSchema,
  generateEnhancedMetadata,
  getCoreWebVitalsMetadata,
  LocalBusinessSchema,
  PerformanceMonitoring,
};
