import { Metadata } from 'next';
import Link from 'next/link';

import { FAQSchema, LocalBusinessSchema } from '@/components/seo/TechnicalSEO';
import { generateLocationPage, locationContentBlocks } from '@/lib/locationPageGenerator';

const locationData = generateLocationPage('San Francisco');

export const metadata: Metadata = {
  title: locationData.title,
  description: locationData.metaDescription,
  keywords:
    'San Francisco hibachi catering, hibachi chef San Francisco, SF party catering, hibachi catering near San Francisco, private chef SF, Japanese catering San Francisco, hibachi birthday party SF, San Francisco wedding hibachi',
  openGraph: {
    title: locationData.title,
    description: locationData.metaDescription,
    type: 'website',
    locale: 'en_US',
    siteName: 'MyHibachi',
  },
  alternates: {
    canonical: '/locations/san-francisco',
  },
};

export default function SanFranciscoHibachiPage() {
  return (
    <div className="min-h-screen">
      {/* Schema Markup */}
      <LocalBusinessSchema
        businessName="MyHibachi San Francisco"
        location="San Francisco"
        description="Professional hibachi catering service in San Francisco, California"
      />
      <FAQSchema faqs={locationData.content.faq} />

      {/* Hero Section */}
      <section className="page-hero-background py-20 text-center text-white">
        <div className="mx-auto max-w-4xl px-4">
          <h1 className="mb-6 text-5xl font-bold">{locationData.h1}</h1>
          <p className="mb-8 text-xl text-gray-200">{locationData.content.hero}</p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/booking"
              className="inline-flex items-center rounded-md border border-transparent bg-orange-600 px-8 py-3 text-base font-medium text-white transition-colors hover:bg-orange-700"
            >
              Book San Francisco Hibachi Catering
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center rounded-md border-2 border-white bg-transparent px-8 py-3 text-base font-medium text-white transition-colors hover:bg-white hover:text-gray-900"
            >
              Get Free Quote
            </Link>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="bg-gray-50 py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-12 text-center text-3xl font-bold text-gray-900">
            San Francisco Hibachi Catering Services
          </h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            {locationData.content.services.map((service: string, index: number) => (
              <div key={index} className="rounded-lg bg-white p-6 text-center shadow-sm">
                <h3 className="mb-2 text-lg font-semibold text-gray-900">{service}</h3>
                <p className="text-sm text-gray-600">
                  Professional hibachi entertainment for your San Francisco celebration
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-16">
        <div className="mx-auto max-w-4xl px-4">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{
              __html: locationContentBlocks.whyChooseUs('San Francisco').replace(/\n/g, '<br />'),
            }}
          />
        </div>
      </section>

      {/* Popular Events */}
      <section className="bg-gray-50 py-16">
        <div className="mx-auto max-w-4xl px-4">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{
              __html: locationContentBlocks.popularEvents('San Francisco').replace(/\n/g, '<br />'),
            }}
          />
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-12 text-center text-3xl font-bold text-gray-900">
            What San Francisco Customers Say
          </h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {locationData.content.testimonials.map((testimonial: string, index: number) => (
              <div key={index} className="rounded-lg bg-white p-6 shadow-sm">
                <p className="mb-4 text-gray-600 italic">
                  &ldquo;{testimonial.split('"')[1]}&rdquo;
                </p>
                <p className="font-semibold text-gray-900">- {testimonial.split('- ')[1]}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Service Areas */}
      <section className="bg-gray-50 py-16">
        <div className="mx-auto max-w-4xl px-4">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{
              __html: locationContentBlocks.serviceAreas('San Francisco').replace(/\n/g, '<br />'),
            }}
          />
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16">
        <div className="mx-auto max-w-4xl px-4">
          <h2 className="mb-12 text-center text-3xl font-bold text-gray-900">
            San Francisco Hibachi Catering FAQ
          </h2>
          <div className="space-y-6">
            {locationData.content.faq.map(
              (faq: { question: string; answer: string }, index: number) => (
                <div key={index} className="rounded-lg bg-white p-6 shadow-sm">
                  <h3 className="mb-3 text-xl font-semibold text-gray-900">{faq.question}</h3>
                  <p className="text-gray-600">{faq.answer}</p>
                </div>
              ),
            )}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-orange-600 py-16 text-center text-white">
        <div className="mx-auto max-w-4xl px-4">
          <h2 className="mb-6 text-3xl font-bold">
            Ready to Book Your San Francisco Hibachi Experience?
          </h2>
          <p className="mb-8 text-xl">
            Contact us today for a free quote on your San Francisco hibachi catering event!
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/booking"
              className="inline-flex items-center rounded-md border-2 border-white bg-white px-8 py-3 text-base font-medium text-orange-600 transition-colors hover:bg-gray-100"
            >
              Book Now
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center rounded-md border-2 border-white bg-transparent px-8 py-3 text-base font-medium text-white transition-colors hover:bg-white hover:text-orange-600"
            >
              Get Quote
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
