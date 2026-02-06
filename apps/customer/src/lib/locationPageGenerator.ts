// Location Page Generator for Local SEO
// ====================================

export interface LocationPage {
  city: string;
  slug: string;
  title: string;
  metaDescription: string;
  h1: string;
  content: {
    hero: string;
    services: string[];
    testimonials: string[];
    faq: Array<{ question: string; answer: string }>;
  };
  schema: Record<string, unknown>;
}

export const targetLocations = [
  'San Jose',
  'San Francisco',
  'Oakland',
  'Palo Alto',
  'Mountain View',
  'Santa Clara',
  'Sunnyvale',
  'Sacramento',
  'Fremont',
];

export function generateLocationPage(city: string): LocationPage {
  return {
    city,
    slug: city.toLowerCase().replace(/\s+/g, '-'),
    title: `Professional Hibachi Catering in ${city} | MyHibachi Private Chef Services`,
    metaDescription: `Premium hibachi catering in ${city}! Private chefs bring authentic Japanese hibachi to your ${city.toLowerCase()} event. Book your interactive dining experience today!`,
    h1: `${city} Hibachi Catering: Premium Private Chef Experience at Your Location`,
    content: {
      hero: `Transform your ${city} celebration into an unforgettable culinary adventure with MyHibachi's premium private chef services. Our professional hibachi chefs bring the excitement of Japanese steakhouse dining directly to your ${city.toLowerCase()} location, creating interactive entertainment that amazes guests of all ages.`,
      services: [
        `${city} Birthday Party Hibachi`,
        `${city} Corporate Event Catering`,
        `${city} Wedding Reception Hibachi`,
        `${city} Anniversary Celebrations`,
        `${city} Holiday Party Catering`,
        `${city} Backyard Party Entertainment`,
        `${city} Family Reunion Hibachi`,
        `${city} Graduation Celebrations`,
      ],
      testimonials: [
        `"MyHibachi made our ${city} wedding reception absolutely magical! The chef was entertaining and the food was restaurant quality. All our guests are still talking about it!" - Sarah & Mike, ${city}`,
        `"For our ${city} corporate event, MyHibachi provided the perfect team building experience. Professional, engaging, and delicious!" - Tech Company, ${city}`,
        `"Best birthday party ever in ${city}! The hibachi chef made my daughter's 16th birthday unforgettable. Highly recommend!" - Jennifer, ${city} Mom`,
      ],
      faq: [
        {
          question: `What areas of ${city} do you serve?`,
          answer: `We provide hibachi catering throughout ${city} and surrounding areas. Our chefs are familiar with ${city.toLowerCase()} venues, homes, and event spaces. We'll travel anywhere in the ${city} area to bring you exceptional hibachi entertainment.`,
        },
        {
          question: `How much space do I need for hibachi catering in ${city}?`,
          answer: `For ${city} hibachi events, we need a minimum 8x8 foot area for our portable grill setup. Most ${city.toLowerCase()} homes, backyards, patios, or event venues provide adequate space. We'll assess your ${city} location during booking.`,
        },
        {
          question: `What's included in ${city} hibachi catering packages?`,
          answer: `Our ${city} hibachi catering includes: professional chef, portable hibachi grill, all cooking equipment, fresh premium ingredients, interactive cooking show, and complete cleanup. You provide the venue and guests - we handle everything else for your ${city} event!`,
        },
        {
          question: `How far in advance should I book ${city} hibachi catering?`,
          answer: `For ${city} events, we recommend booking 2-4 weeks in advance, especially during peak seasons. However, we can sometimes accommodate last-minute ${city} bookings based on chef availability.`,
        },
        {
          question: `Do you provide hibachi catering for large events in ${city}?`,
          answer: `Yes! We cater ${city} events from intimate dinners for 8 to large celebrations for 100+ guests. Multiple hibachi stations ensure everyone enjoys the full interactive experience at your ${city} event.`,
        },
      ],
    },
    schema: {
      '@context': 'https://schema.org',
      '@type': 'LocalBusiness',
      name: `MyHibachi ${city}`,
      image: 'https://myhibachichef.com/logo.png',
      description: `Professional hibachi catering service in ${city}, California. Private chefs bring authentic Japanese hibachi entertainment to your location.`,
      address: {
        '@type': 'PostalAddress',
        addressLocality: city,
        addressRegion: 'CA',
        addressCountry: 'US',
      },
      telephone: '+1-555-HIBACHI',
      url: `https://myhibachichef.com/locations/${city.toLowerCase().replace(/\s+/g, '-')}`,
      servesCuisine: 'Japanese',
      priceRange: '$$-$$$',
      serviceArea: {
        '@type': 'Place',
        name: `${city} and surrounding areas`,
      },
      aggregateRating: {
        '@type': 'AggregateRating',
        ratingValue: '4.9',
        reviewCount: '150',
      },
      hasOfferCatalog: {
        '@type': 'OfferCatalog',
        name: `${city} Hibachi Catering Services`,
        itemListElement: [
          {
            '@type': 'Offer',
            itemOffered: {
              '@type': 'Service',
              name: `${city} Birthday Party Hibachi`,
            },
          },
          {
            '@type': 'Offer',
            itemOffered: {
              '@type': 'Service',
              name: `${city} Corporate Event Catering`,
            },
          },
          {
            '@type': 'Offer',
            itemOffered: {
              '@type': 'Service',
              name: `${city} Wedding Reception Hibachi`,
            },
          },
        ],
      },
    },
  };
}

export function generateAllLocationPages(): LocationPage[] {
  return targetLocations.map(generateLocationPage);
}

// SEO-optimized content blocks for location pages
export const locationContentBlocks = {
  whyChooseUs: (city: string) => `
    ## Why Choose MyHibachi for Your ${city} Event?

    ### 🔥 Authentic Japanese Entertainment
    Our ${city} hibachi chefs are trained in traditional Japanese cooking techniques and entertainment. They bring the excitement of Tokyo steakhouses directly to your ${city.toLowerCase()} location.

    ### 👨‍🍳 Professional & Experienced Chefs
    All our ${city} hibachi chefs are professionally trained, licensed, and insured. They have extensive experience catering events throughout the ${city} area.

    ### 🏠 Complete Mobile Setup
    We bring everything needed for your ${city} hibachi experience - portable grills, premium ingredients, cooking utensils, and professional setup/cleanup.

    ### 🎭 Interactive Entertainment
    Beyond amazing food, our ${city} hibachi chefs provide engaging entertainment with knife tricks, onion volcanoes, and crowd interaction that delights guests.
  `,

  popularEvents: (city: string) => `
    ## Popular ${city} Hibachi Events

    ### 🎂 Birthday Parties
    Make birthdays special with ${city} hibachi entertainment! Perfect for kids and adults alike, creating memorable celebrations.

    ### 💼 Corporate Events
    ${city} businesses choose hibachi for team building, client entertainment, and company celebrations that build relationships.

    ### 💒 Weddings & Receptions
    Add unique flair to ${city} weddings with hibachi catering that guests will remember forever.

    ### 🎓 Graduations
    Celebrate academic achievements with ${city} graduation hibachi parties that honor your accomplishments.

    ### 🏠 Backyard Gatherings
    Transform your ${city} backyard into a Japanese steakhouse with professional hibachi entertainment.
  `,

  serviceAreas: (city: string) => `
    ## ${city} Service Areas

    We proudly serve all neighborhoods and areas throughout ${city}, including:
    - Downtown ${city}
    - ${city} suburbs and residential areas
    - ${city} business districts
    - ${city} event venues and community centers
    - ${city} parks and outdoor spaces (with permits)
    - Private homes throughout ${city}

    No matter where your ${city} event is located, our mobile hibachi service brings the restaurant experience to you!
  `,
};
