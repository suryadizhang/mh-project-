// Global SEO Configuration for MyHibachi
// =====================================

import type { Metadata } from 'next'

// Base SEO constants
export const SITE_CONFIG = {
  name: "My Hibachi Chef",
  url: "https://myhibachichef.com",
  title: "My Hibachi Chef - Premium Mobile Hibachi Catering Bay Area & Sacramento",
  description: "Professional hibachi catering service bringing authentic Japanese teppanyaki experience to your location. Serving Bay Area, Sacramento, San Jose with premium quality and reasonable prices.",
  keywords: [
    "hibachi catering",
    "mobile hibachi chef",
    "Bay Area hibachi",
    "Sacramento hibachi",
    "San Jose hibachi",
    "private hibachi chef",
    "teppanyaki catering",
    "Japanese catering",
    "birthday party hibachi",
    "wedding hibachi",
    "corporate hibachi",
    "backyard hibachi",
    "pool party hibachi"
  ],
  author: "My Hibachi Chef Team",
  social: {
    instagram: "https://www.instagram.com/my_hibachi_chef/",
    facebook: "https://www.facebook.com/people/My-hibachi/61577483702847/",
    yelp: "https://www.yelp.com/biz/my-hibachi-fremont"
  },
  contact: {
    phone: "(916) 740-8768",
    email: "cs@myhibachichef.com",
    serviceArea: "Bay Area & Sacramento Region"
  }
} as const

// Generate page-specific metadata
export function generatePageMetadata({
  title,
  description,
  keywords = [],
  path = "",
  images = [],
  noIndex = false,
  canonical,
}: {
  title: string
  description: string
  keywords?: string[]
  path?: string
  images?: string[]
  noIndex?: boolean
  canonical?: string
}): Metadata {
  const fullTitle = title.includes(SITE_CONFIG.name) 
    ? title 
    : `${title} | ${SITE_CONFIG.name}`
  
  const url = `${SITE_CONFIG.url}${path}`
  const allKeywords = [...SITE_CONFIG.keywords, ...keywords].join(", ")

  const defaultImage = `${SITE_CONFIG.url}/images/myhibachi-logo.png`
  const ogImages = images.length > 0 ? images : [defaultImage]

  return {
    title: fullTitle,
    description,
    keywords: allKeywords,
    authors: [{ name: SITE_CONFIG.author }],
    creator: SITE_CONFIG.author,
    publisher: SITE_CONFIG.name,
    robots: noIndex ? "noindex,nofollow" : "index,follow",
    
    openGraph: {
      type: "website",
      url,
      title: fullTitle,
      description,
      siteName: SITE_CONFIG.name,
      images: ogImages.map(image => ({
        url: image,
        width: 1200,
        height: 630,
        alt: title,
      })),
    },
    
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description,
      images: ogImages,
      creator: "@myhibachichef",
    },

    alternates: {
      canonical: canonical || url,
    },

    other: {
      "business:contact_data:phone_number": SITE_CONFIG.contact.phone,
      "business:contact_data:email": SITE_CONFIG.contact.email,
      "business:contact_data:region": SITE_CONFIG.contact.serviceArea,
    },
  }
}

// Page-specific SEO configurations
export const PAGE_SEO = {
  home: {
    title: "My Hibachi Chef - Premium Mobile Hibachi Catering Bay Area & Sacramento",
    description: "Experience authentic Japanese hibachi catering at your location. Professional mobile teppanyaki chefs serving Bay Area, Sacramento, San Jose. Book premium quality hibachi for birthdays, weddings, corporate events.",
    keywords: [
      "mobile hibachi catering",
      "Bay Area hibachi chef",
      "Sacramento hibachi catering",
      "private teppanyaki chef",
      "hibachi birthday party",
      "corporate hibachi catering",
      "wedding hibachi entertainment"
    ]
  },
  
  menu: {
    title: "Hibachi Menu & Pricing - Premium Teppanyaki Catering Options",
    description: "Explore our authentic hibachi menu featuring premium steaks, fresh seafood, and traditional Japanese teppanyaki. Customizable packages for all events. View pricing and book your mobile hibachi experience.",
    keywords: [
      "hibachi menu",
      "teppanyaki pricing",
      "hibachi catering packages",
      "mobile hibachi menu",
      "Japanese steakhouse catering",
      "hibachi food options"
    ]
  },

  booking: {
    title: "Book Hibachi Catering - Easy Online Booking Bay Area & Sacramento",
    description: "Book premium hibachi catering for your event. Easy online booking for Bay Area, Sacramento, San Jose. Professional mobile teppanyaki chefs for birthdays, weddings, corporate events.",
    keywords: [
      "book hibachi catering",
      "hibachi chef booking",
      "mobile hibachi reservation",
      "Bay Area hibachi booking",
      "Sacramento hibachi scheduling"
    ]
  },

  quote: {
    title: "Get Free Hibachi Catering Quote - Instant Pricing Calculator",
    description: "Get instant free quote for hibachi catering. Professional pricing calculator for Bay Area, Sacramento, San Jose events. Custom packages for birthdays, weddings, corporate gatherings.",
    keywords: [
      "hibachi catering quote",
      "mobile hibachi pricing",
      "hibachi cost calculator",
      "Bay Area hibachi prices",
      "Sacramento hibachi rates"
    ]
  },

  contact: {
    title: "Contact My Hibachi Chef - Book Premium Mobile Hibachi Catering",
    description: "Contact My Hibachi Chef for premium mobile hibachi catering. Serving Bay Area, Sacramento, San Jose. Call (916) 740-8768 or message us for instant booking assistance.",
    keywords: [
      "contact hibachi chef",
      "hibachi catering contact",
      "mobile hibachi phone",
      "Bay Area hibachi contact",
      "Sacramento hibachi booking"
    ]
  },

  blog: {
    title: "Hibachi Catering Blog - Expert Event Planning Tips & Guides",
    description: "Complete hibachi catering guides for every event: birthdays, weddings, corporate events, pool parties. Expert tips for Bay Area, Sacramento, San Jose celebrations.",
    keywords: [
      "hibachi catering blog",
      "hibachi party planning",
      "teppanyaki event tips",
      "hibachi birthday guides",
      "corporate hibachi planning"
    ]
  },

  faqs: {
    title: "Hibachi Catering FAQs - Common Questions & Expert Answers",
    description: "Get answers to common hibachi catering questions. Learn about pricing, setup, menu options, service areas, and booking process for Bay Area & Sacramento mobile hibachi.",
    keywords: [
      "hibachi catering FAQ",
      "hibachi questions",
      "mobile hibachi info",
      "hibachi catering help",
      "teppanyaki catering guide"
    ]
  },

  locations: {
    title: "Service Areas - Bay Area & Sacramento Hibachi Catering Coverage",
    description: "Professional hibachi catering serving Bay Area, Sacramento, San Jose, Oakland, Fremont, and surrounding areas. Mobile teppanyaki chefs available for all locations.",
    keywords: [
      "hibachi service areas",
      "Bay Area hibachi coverage",
      "Sacramento hibachi service",
      "mobile hibachi locations",
      "hibachi delivery areas"
    ]
  }
} as const

// Location-specific SEO generator
export function generateLocationSEO(city: string, state: string = "California") {
  const cityFormatted = city.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())
  
  return {
    title: `${cityFormatted} Hibachi Catering - Premium Mobile Teppanyaki Chef Services`,
    description: `Professional hibachi catering in ${cityFormatted}, ${state}. Mobile teppanyaki chefs for birthdays, weddings, corporate events. Premium quality, reasonable prices. Book your ${cityFormatted} hibachi experience today.`,
    keywords: [
      `${cityFormatted.toLowerCase()} hibachi catering`,
      `hibachi chef ${cityFormatted.toLowerCase()}`,
      `${cityFormatted.toLowerCase()} teppanyaki catering`,
      `mobile hibachi ${cityFormatted.toLowerCase()}`,
      `${cityFormatted.toLowerCase()} Japanese catering`,
      `${cityFormatted.toLowerCase()} party catering`,
      `private hibachi chef ${cityFormatted.toLowerCase()}`
    ]
  }
}

// Structured data generators
export function generateOrganizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": SITE_CONFIG.name,
    "url": SITE_CONFIG.url,
    "logo": `${SITE_CONFIG.url}/images/myhibachi-logo.png`,
    "description": SITE_CONFIG.description,
    "telephone": SITE_CONFIG.contact.phone,
    "email": SITE_CONFIG.contact.email,
    "areaServed": SITE_CONFIG.contact.serviceArea,
    "serviceType": "Hibachi Catering",
    "sameAs": [
      SITE_CONFIG.social.instagram,
      SITE_CONFIG.social.facebook,
      SITE_CONFIG.social.yelp
    ],
    "address": {
      "@type": "PostalAddress",
      "addressRegion": "CA",
      "addressCountry": "US"
    }
  }
}

export function generateLocalBusinessSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": SITE_CONFIG.name,
    "url": SITE_CONFIG.url,
    "telephone": SITE_CONFIG.contact.phone,
    "email": SITE_CONFIG.contact.email,
    "description": SITE_CONFIG.description,
    "areaServed": [
      "San Francisco Bay Area",
      "Sacramento",
      "San Jose",
      "Oakland",
      "Fremont",
      "Mountain View",
      "Palo Alto",
      "Santa Clara",
      "Sunnyvale"
    ],
    "serviceType": "Mobile Hibachi Catering",
    "priceRange": "$$",
    "currenciesAccepted": "USD",
    "paymentAccepted": "Cash, Credit Card, Venmo, Zelle",
    "openingHours": "Mo-Su 09:00-21:00"
  }
}

export function generateServiceSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Mobile Hibachi Catering",
    "description": "Professional mobile hibachi catering service bringing authentic Japanese teppanyaki experience to your location",
    "provider": {
      "@type": "Organization",
      "name": SITE_CONFIG.name,
      "url": SITE_CONFIG.url
    },
    "areaServed": SITE_CONFIG.contact.serviceArea,
    "hasOfferCatalog": {
      "@type": "OfferCatalog",
      "name": "Hibachi Catering Services",
      "itemListElement": [
        {
          "@type": "Offer",
          "itemOffered": {
            "@type": "Service",
            "name": "Birthday Party Hibachi Catering"
          }
        },
        {
          "@type": "Offer",
          "itemOffered": {
            "@type": "Service",
            "name": "Wedding Hibachi Catering"
          }
        },
        {
          "@type": "Offer",
          "itemOffered": {
            "@type": "Service",
            "name": "Corporate Event Hibachi Catering"
          }
        }
      ]
    }
  }
}

// FAQ Schema generator
export function generateFAQSchema(faqs: Array<{question: string, answer: string}>) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faqs.map(faq => ({
      "@type": "Question",
      "name": faq.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.answer
      }
    }))
  }
}

// Breadcrumb schema generator
export function generateBreadcrumbSchema(items: Array<{name: string, url: string}>) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": items.map((item, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "name": item.name,
      "item": `${SITE_CONFIG.url}${item.url}`
    }))
  }
}
