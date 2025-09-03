import { Metadata } from 'next'
import Link from 'next/link'
import { LocalBusinessSchema } from '@/components/seo/TechnicalSEO'
import Assistant from '@/components/chat/Assistant'

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
    siteName: 'MyHibachi'
  },
  alternates: {
    canonical: '/locations'
  }
}

export default function LocationsPage() {
  const locationCards = [
    {
      city: 'San Jose',
      slug: 'san-jose',
      description: "Silicon Valley's premier hibachi catering for tech companies and families",
      highlights: ['Tech Company Events', 'Family Celebrations', 'Backyard Parties']
    },
    {
      city: 'San Francisco',
      slug: 'san-francisco',
      description: 'Bringing hibachi entertainment to the heart of the Bay Area',
      highlights: ['Luxury Events', 'Apartment Parties', 'Corporate Dinners']
    },
    {
      city: 'Palo Alto',
      slug: 'palo-alto',
      description: 'Stanford area hibachi catering for academic and business communities',
      highlights: ['Stanford Events', 'Corporate Catering', 'Alumni Reunions']
    },
    {
      city: 'Oakland',
      slug: 'oakland',
      description: 'East Bay hibachi catering for weddings, parties, and celebrations',
      highlights: ['Wedding Receptions', 'Cultural Events', 'Community Gatherings']
    },
    {
      city: 'Mountain View',
      slug: 'mountain-view',
      description: 'Google area hibachi catering for tech workers and families',
      highlights: ['Tech Birthday Parties', 'Team Building', 'Family Events']
    },
    {
      city: 'Santa Clara',
      slug: 'santa-clara',
      description: 'University and tech hub hibachi catering services',
      highlights: ['Graduation Parties', 'Corporate Events', 'Sports Celebrations']
    },
    {
      city: 'Sacramento',
      slug: 'sacramento',
      description: 'Capital city hibachi catering for government and private events',
      highlights: ['Government Events', 'Large Celebrations', 'Holiday Parties']
    },
    {
      city: 'Sunnyvale',
      slug: 'sunnyvale',
      description: 'Tech hub hibachi catering for international families',
      highlights: ['International Events', 'Tech Celebrations', 'Cultural Festivals']
    }
  ]

  return (
    <div className="min-h-screen">
      {/* Schema Markup */}
      <LocalBusinessSchema
        location="California Bay Area"
        description="Professional hibachi catering service across California - Bay Area, Sacramento, and Central Valley"
      />

      {/* Hero Section */}
      <section className="page-hero-background py-20 text-white text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-5xl font-bold mb-6">Hibachi Catering Locations Across California</h1>
          <p className="text-xl mb-8 text-gray-200">
            Professional hibachi chefs bringing authentic Japanese entertainment to your location
            throughout the Bay Area, Sacramento, and Central Valley. From intimate family dinners to
            large corporate events.
          </p>
          <div className="text-lg mb-12">
            <span className="bg-orange-600 text-white px-6 py-3 rounded-full">
              Serving 50+ Cities Across California
            </span>
          </div>
        </div>
      </section>

      {/* Coverage Map Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Our Service Area Coverage
          </h2>
          <div className="bg-white p-8 rounded-lg shadow-sm mb-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-orange-600 mb-4">Bay Area</h3>
                <ul className="text-gray-600 space-y-2">
                  <li>San Jose & Silicon Valley</li>
                  <li>San Francisco</li>
                  <li>Oakland & East Bay</li>
                  <li>Palo Alto & Stanford</li>
                  <li>Mountain View & Google Area</li>
                  <li>Santa Clara & Sunnyvale</li>
                </ul>
              </div>
              <div className="text-center">
                <h3 className="text-2xl font-bold text-orange-600 mb-4">Central Valley</h3>
                <ul className="text-gray-600 space-y-2">
                  <li>Sacramento Metro</li>
                  <li>Stockton Area</li>
                  <li>Modesto Region</li>
                  <li>Tracy & Lathrop</li>
                  <li>Manteca & Ripon</li>
                  <li>Surrounding Communities</li>
                </ul>
              </div>
              <div className="text-center">
                <h3 className="text-2xl font-bold text-orange-600 mb-4">Extended Areas</h3>
                <ul className="text-gray-600 space-y-2">
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
            <p className="text-lg text-gray-600 mb-4">
              Don&apos;t see your city listed? We travel throughout California for special events!
            </p>
            <Link
              href="/contact"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 transition-colors"
            >
              Check Service Availability
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Locations */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Featured Hibachi Catering Locations
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {locationCards.map(location => (
              <div
                key={location.slug}
                className="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="h-32 bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
                  <h3 className="text-2xl font-bold text-white">{location.city}</h3>
                </div>
                <div className="p-6">
                  <p className="text-gray-600 mb-4">{location.description}</p>
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Popular Services:</h4>
                    <div className="flex flex-wrap gap-2">
                      {location.highlights.map((highlight, index) => (
                        <span
                          key={index}
                          className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full"
                        >
                          {highlight}
                        </span>
                      ))}
                    </div>
                  </div>
                  <Link
                    href={`/locations/${location.slug}`}
                    className="inline-flex items-center text-orange-600 hover:text-orange-700 font-medium"
                  >
                    Learn More About {location.city} →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Service Benefits */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Why Choose MyHibachi for Multi-Location Events?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🚗</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Flexible Travel</h3>
              <p className="text-gray-600 text-sm">
                We travel to your location anywhere in our service area with full mobile setup
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">👨‍🍳</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Local Expertise</h3>
              <p className="text-gray-600 text-sm">
                Our chefs know each area and can recommend the best setup for your location
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📱</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Easy Booking</h3>
              <p className="text-gray-600 text-sm">
                Simple online booking system with location-specific pricing and availability
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🏆</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Consistent Quality</h3>
              <p className="text-gray-600 text-sm">
                Same high-quality service and entertainment regardless of your location
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-orange-600 text-white text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-bold mb-6">Ready to Book Hibachi Catering in Your Area?</h2>
          <p className="text-xl mb-8">
            Contact us today to check availability and get a free quote for your location!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/booking"
              className="inline-flex items-center px-8 py-3 border-2 border-white text-base font-medium rounded-md text-orange-600 bg-white hover:bg-gray-100 transition-colors"
            >
              Book Your Event
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center px-8 py-3 border-2 border-white text-base font-medium rounded-md text-white bg-transparent hover:bg-white hover:text-orange-600 transition-colors"
            >
              Get Free Quote
            </Link>
          </div>
        </div>
      </section>

      <Assistant page="/locations" />
    </div>
  )
}
