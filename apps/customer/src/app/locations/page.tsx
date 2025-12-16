import { Metadata } from 'next';
import Link from 'next/link';

import { LocalBusinessSchema } from '@/components/seo/TechnicalSEO';

export const metadata: Metadata = {
  title: 'Hibachi Catering Locations | Bay Area, Sacramento & Central Valley | MyHibachi',
  description:
    'Professional hibachi catering across California! Serving San Jose, San Francisco, Oakland, Palo Alto, Mountain View, Sacramento & more. Book your private chef today!',
  keywords:
    'hibachi catering locations, Bay Area hibachi chef, Sacramento hibachi catering, California hibachi service, mobile hibachi catering, private chef California',
  openGraph: {
    title: 'Hibachi Catering Locations | Bay Area, Sacramento & Central Valley',
    description:
      'Professional hibachi catering across California! Serving San Jose, San Francisco, Oakland, Palo Alto, Mountain View, Sacramento & more.',
    type: 'website',
    locale: 'en_US',
    siteName: 'MyHibachi',
  },
  alternates: {
    canonical: '/locations',
  },
};

export default function LocationsPage() {
  const locationCards = [
    {
      city: 'San Jose',
      slug: 'san-jose',
      description: "Silicon Valley's premier hibachi catering for tech companies and families",
      highlights: ['Tech Company Events', 'Family Celebrations', 'Backyard Parties'],
    },
    {
      city: 'San Francisco',
      slug: 'san-francisco',
      description: 'Bringing hibachi entertainment to the heart of the Bay Area',
      highlights: ['Luxury Events', 'Apartment Parties', 'Corporate Dinners'],
    },
    {
      city: 'Palo Alto',
      slug: 'palo-alto',
      description: 'Stanford area hibachi catering for academic and business communities',
      highlights: ['Stanford Events', 'Corporate Catering', 'Alumni Reunions'],
    },
    {
      city: 'Oakland',
      slug: 'oakland',
      description: 'East Bay hibachi catering for weddings, parties, and celebrations',
      highlights: ['Wedding Receptions', 'Cultural Events', 'Community Gatherings'],
    },
    {
      city: 'Mountain View',
      slug: 'mountain-view',
      description: 'Google area hibachi catering for tech workers and families',
      highlights: ['Tech Birthday Parties', 'Team Building', 'Family Events'],
    },
    {
      city: 'Santa Clara',
      slug: 'santa-clara',
      description: 'University and tech hub hibachi catering services',
      highlights: ['Graduation Parties', 'Corporate Events', 'Sports Celebrations'],
    },
    {
      city: 'Sacramento',
      slug: 'sacramento',
      description: 'Capital city hibachi catering for government and private events',
      highlights: ['Government Events', 'Large Celebrations', 'Holiday Parties'],
    },
    {
      city: 'Sunnyvale',
      slug: 'sunnyvale',
      description: 'Tech hub hibachi catering for international families',
      highlights: ['International Events', 'Tech Celebrations', 'Cultural Festivals'],
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Schema Markup */}
      <LocalBusinessSchema
        location="California Bay Area"
        description="Professional hibachi catering service across California - Bay Area, Sacramento, and Central Valley"
      />

      {/* Hero Section */}
      <section className="page-hero-background py-10 text-center text-white">
        <div className="mx-auto max-w-4xl px-4">
          <h1 className="mb-3 text-3xl font-bold md:text-4xl">
            Hibachi Catering Locations Across California
          </h1>
          <p className="mb-4 text-base text-gray-200">
            Professional hibachi chefs bringing authentic Japanese entertainment to your location
            throughout the Bay Area, Sacramento, and Central Valley.
          </p>
          <div className="mb-6 text-sm">
            <span className="rounded-full bg-orange-600 px-4 py-2 text-white">
              Serving 50+ Cities Across California
            </span>
          </div>
        </div>
      </section>

      {/* Coverage Map Section */}
      <section className="bg-gray-50 py-8">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-6 text-center text-2xl font-bold text-gray-900">
            Our Service Area Coverage
          </h2>
          <div className="mb-4 rounded-lg bg-white p-4 shadow-sm">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="text-center">
                <h3 className="mb-2 text-lg font-bold text-orange-600">Bay Area</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>San Jose & Silicon Valley</li>
                  <li>San Francisco</li>
                  <li>Oakland & East Bay</li>
                  <li>Palo Alto & Stanford</li>
                  <li>Mountain View</li>
                  <li>Santa Clara & Sunnyvale</li>
                </ul>
              </div>
              <div className="text-center">
                <h3 className="mb-2 text-lg font-bold text-orange-600">Central Valley</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>Sacramento Metro</li>
                  <li>Stockton Area</li>
                  <li>Modesto Region</li>
                  <li>Tracy & Lathrop</li>
                  <li>Manteca & Ripon</li>
                  <li>Surrounding Communities</li>
                </ul>
              </div>
              <div className="text-center">
                <h3 className="mb-2 text-lg font-bold text-orange-600">Extended Areas</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>Fremont & Newark</li>
                  <li>Milpitas & Union City</li>
                  <li>Livermore & Pleasanton</li>
                  <li>San Mateo County</li>
                  <li>Marin County</li>
                  <li>Custom Travel Available</li>
                </ul>
              </div>
            </div>
          </div>
          <div className="text-center">
            <p className="mb-2 text-sm text-gray-600">
              Don&apos;t see your city? We travel throughout California!
            </p>
            <Link
              href="/contact"
              className="inline-flex items-center rounded-md bg-orange-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-orange-700"
            >
              Check Service Availability
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Locations */}
      <section className="py-8">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-6 text-center text-2xl font-bold text-gray-900">
            Featured Hibachi Catering Locations
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {locationCards.map((location) => (
              <div
                key={location.slug}
                className="overflow-hidden rounded-lg bg-white shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex h-20 items-center justify-center bg-gradient-to-br from-orange-500 to-red-600">
                  <h3 className="text-lg font-bold text-white">{location.city}</h3>
                </div>
                <div className="p-3">
                  <p className="mb-2 text-xs text-gray-600">{location.description}</p>
                  <div className="mb-2">
                    <div className="flex flex-wrap gap-1">
                      {location.highlights.slice(0, 2).map((highlight, index) => (
                        <span
                          key={index}
                          className="rounded-full bg-gray-100 px-1.5 py-0.5 text-xs text-gray-700"
                        >
                          {highlight}
                        </span>
                      ))}
                    </div>
                  </div>
                  <Link
                    href={`/locations/${location.slug}`}
                    className="text-xs font-medium text-orange-600 hover:text-orange-700"
                  >
                    Learn More →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Service Benefits */}
      <section className="bg-gray-50 py-8">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-4 text-center text-xl font-bold text-gray-900">
            Why Choose MyHibachi?
          </h2>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="text-center">
              <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-orange-100">
                <span className="text-lg">🚗</span>
              </div>
              <h3 className="text-sm font-semibold text-gray-900">Flexible Travel</h3>
              <p className="text-xs text-gray-600">Full mobile setup anywhere</p>
            </div>
            <div className="text-center">
              <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-orange-100">
                <span className="text-lg">👨‍🍳</span>
              </div>
              <h3 className="text-sm font-semibold text-gray-900">Local Expertise</h3>
              <p className="text-xs text-gray-600">Area-specific recommendations</p>
            </div>
            <div className="text-center">
              <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-orange-100">
                <span className="text-lg">📱</span>
              </div>
              <h3 className="text-sm font-semibold text-gray-900">Easy Booking</h3>
              <p className="text-xs text-gray-600">Simple online system</p>
            </div>
            <div className="text-center">
              <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-orange-100">
                <span className="text-lg">🏆</span>
              </div>
              <h3 className="text-sm font-semibold text-gray-900">Consistent Quality</h3>
              <p className="text-xs text-gray-600">Same excellence everywhere</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-orange-600 py-8 text-center text-white">
        <div className="mx-auto max-w-4xl px-4">
          <h2 className="mb-2 text-xl font-bold">Ready to Book Hibachi in Your Area?</h2>
          <p className="mb-4 text-sm">Contact us for availability and a free quote!</p>
          <div className="flex flex-row items-center justify-center gap-3">
            <Link
              href="/booking"
              className="inline-flex items-center rounded-md border-2 border-white bg-white px-5 py-2 text-sm font-medium text-orange-600 transition-colors hover:bg-gray-100"
            >
              Book Event
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center rounded-md border-2 border-white bg-transparent px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-white hover:text-orange-600"
            >
              Get Quote
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
