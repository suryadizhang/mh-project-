import { Metadata } from 'next'
import Link from 'next/link'

import Assistant from '@/components/chat/Assistant'
import { FAQSchema, LocalBusinessSchema } from '@/components/seo/TechnicalSEO'
import { generateLocationPage, locationContentBlocks } from '@/lib/locationPageGenerator'

const locationData = generateLocationPage('Palo Alto')

export const metadata: Metadata = {
  title: locationData.title,
  description: locationData.metaDescription,
  keywords:
    'Palo Alto hibachi catering, hibachi chef Palo Alto, Stanford area catering, hibachi catering near Palo Alto, private chef Palo Alto, Japanese catering Palo Alto, hibachi birthday party Palo Alto, corporate hibachi Palo Alto',
  openGraph: {
    title: locationData.title,
    description: locationData.metaDescription,
    type: 'website',
    locale: 'en_US',
    siteName: 'MyHibachi'
  },
  alternates: {
    canonical: '/locations/palo-alto'
  }
}

export default function PaloAltoHibachiPage() {
  return (
    <div className="min-h-screen">
      {/* Schema Markup */}
      <LocalBusinessSchema
        businessName="MyHibachi Palo Alto"
        location="Palo Alto"
        description="Professional hibachi catering service in Palo Alto, California. Serving Stanford area with premium private chef experiences"
      />
      <FAQSchema faqs={locationData.content.faq} />

      {/* Hero Section */}
      <section className="page-hero-background py-20 text-white text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-5xl font-bold mb-6">{locationData.h1}</h1>
          <p className="text-xl mb-8 text-gray-200">{locationData.content.hero}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/booking"
              className="inline-flex items-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 transition-colors"
            >
              Book Palo Alto Hibachi Catering
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center px-8 py-3 border-2 border-white text-base font-medium rounded-md text-white bg-transparent hover:bg-white hover:text-gray-900 transition-colors"
            >
              Get Free Quote
            </Link>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Palo Alto & Stanford Area Hibachi Catering Services
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {locationData.content.services.map((service, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-sm text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{service}</h3>
                <p className="text-gray-600 text-sm">
                  Professional hibachi entertainment for your Palo Alto celebration
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stanford Area Special Section */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">
            Stanford University & Silicon Valley Corporate Events
          </h2>
          <div className="bg-white p-8 rounded-lg shadow-sm">
            <p className="text-lg text-gray-600 mb-6">
              Serving the Stanford University community and Silicon Valley tech companies with
              premium hibachi catering. Perfect for graduation celebrations, corporate team
              building, faculty events, and student organization gatherings.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Stanford Events</h3>
                <ul className="text-gray-600 space-y-2">
                  <li>• Graduation celebrations</li>
                  <li>• Faculty dinner parties</li>
                  <li>• Student organization events</li>
                  <li>• Alumni reunions</li>
                </ul>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Corporate Events</h3>
                <ul className="text-gray-600 space-y-2">
                  <li>• Tech company team building</li>
                  <li>• Client entertainment</li>
                  <li>• Product launch celebrations</li>
                  <li>• Executive dinners</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{
              __html: locationContentBlocks.whyChooseUs('Palo Alto').replace(/\n/g, '<br />')
            }}
          />
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            What Palo Alto & Stanford Customers Say
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {locationData.content.testimonials.map((testimonial, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-sm">
                <p className="text-gray-600 italic mb-4">
                  &ldquo;{testimonial.split('"')[1]}&rdquo;
                </p>
                <p className="text-gray-900 font-semibold">- {testimonial.split('- ')[1]}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Palo Alto Hibachi Catering FAQ
          </h2>
          <div className="space-y-6">
            {locationData.content.faq.map((faq, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{faq.question}</h3>
                <p className="text-gray-600">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-orange-600 text-white text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-bold mb-6">
            Ready to Book Your Palo Alto Hibachi Experience?
          </h2>
          <p className="text-xl mb-8">
            Contact us today for a free quote on your Palo Alto or Stanford area hibachi catering
            event!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/booking"
              className="inline-flex items-center px-8 py-3 border-2 border-white text-base font-medium rounded-md text-orange-600 bg-white hover:bg-gray-100 transition-colors"
            >
              Book Now
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center px-8 py-3 border-2 border-white text-base font-medium rounded-md text-white bg-transparent hover:bg-white hover:text-orange-600 transition-colors"
            >
              Get Quote
            </Link>
          </div>
        </div>
      </section>

      <Assistant page="/locations/palo-alto" />
    </div>
  )
}
