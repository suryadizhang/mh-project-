import { Metadata } from 'next'
import Link from 'next/link'

import Assistant from '@/components/chat/Assistant'
import { FAQSchema, LocalBusinessSchema } from '@/components/seo/TechnicalSEO'
import { generateLocationPage, locationContentBlocks } from '@/lib/locationPageGenerator'

const locationData = generateLocationPage('San Jose')

export const metadata: Metadata = {
  title: locationData.title,
  description: locationData.metaDescription,
  keywords:
    'San Jose hibachi catering, hibachi chef San Jose, San Jose party catering, hibachi catering near San Jose, private chef San Jose, Japanese catering San Jose, hibachi birthday party San Jose, San Jose wedding hibachi',
  openGraph: {
    title: locationData.title,
    description: locationData.metaDescription,
    type: 'website',
    locale: 'en_US',
    siteName: 'MyHibachi'
  },
  alternates: {
    canonical: '/locations/san-jose'
  }
}

export default function SanJoseHibachiPage() {
  return (
    <div className="min-h-screen">
      {/* Schema Markup */}
      <LocalBusinessSchema
        businessName="MyHibachi San Jose"
        location="San Jose"
        description="Professional hibachi catering service in San Jose, California"
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
              Book San Jose Hibachi Catering
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
            San Jose Hibachi Catering Services
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {locationData.content.services.map((service, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-sm text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{service}</h3>
                <p className="text-gray-600 text-sm">
                  Professional hibachi entertainment for your San Jose celebration
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{
              __html: locationContentBlocks.whyChooseUs('San Jose').replace(/\n/g, '<br />')
            }}
          />
        </div>
      </section>

      {/* Popular Events */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{
              __html: locationContentBlocks.popularEvents('San Jose').replace(/\n/g, '<br />')
            }}
          />
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            What San Jose Customers Say
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

      {/* Service Areas */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{
              __html: locationContentBlocks.serviceAreas('San Jose').replace(/\n/g, '<br />')
            }}
          />
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            San Jose Hibachi Catering FAQ
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
            Ready to Book Your San Jose Hibachi Experience?
          </h2>
          <p className="text-xl mb-8">
            Contact us today for a free quote on your San Jose hibachi catering event!
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

      <Assistant page="/locations/san-jose" />
    </div>
  )
}
