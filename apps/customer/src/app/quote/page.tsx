'use client'

import '@/styles/quote-calculator.css'

import Assistant from '@/components/chat/Assistant'
import { QuoteCalculator } from '@/components/quote/QuoteCalculator'
import { QuoteRequestForm } from '@/components/forms/QuoteRequestForm'

export default function QuotePage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            name: 'Free Hibachi Catering Quote Calculator - My Hibachi Chef',
            description:
              'Get an instant estimate for your hibachi party. Calculate pricing for adults, children, upgrades, and travel fees. Serving Northern California.',
            url: 'https://myhibachichef.com/quote',
            mainEntity: {
              '@type': 'LocalBusiness',
              '@id': 'https://myhibachichef.com/#business',
              name: 'My Hibachi Chef',
              description: 'Professional hibachi catering service',
              priceRange: '$55-$70 per person',
              serviceArea: {
                '@type': 'GeoCircle',
                geoMidpoint: {
                  '@type': 'GeoCoordinates',
                  latitude: 37.5485,
                  longitude: -121.9886
                },
                geoRadius: 150
              }
            }
          })
        }}
      />

      <main className="quote-page">
        {/* Hero Section */}
        <section className="page-hero-background">
          <div className="container">
            <h1>Free Hibachi Catering Quote</h1>
            <p>
              Get an instant estimate for your hibachi party. Our calculator includes pricing for
              adults, children, upgrades, and travel fees based on your location.
            </p>
          </div>
        </section>

        {/* Quote Calculator */}
        <section className="section-background">
          <div className="container">
            <QuoteCalculator />
          </div>
        </section>

        {/* Additional Info */}
        <section className="section-background">
          <div className="container">
            <div className="info-grid">
              <div className="info-card">
                <h3>📊 Initial Estimates</h3>
                <p>
                  Our calculator provides initial estimates based on current pricing. Final pricing
                  may vary and will be confirmed during booking consultation.
                </p>
              </div>
              <div className="info-card">
                <h3>📞 Personal Consultation</h3>
                <p>
                  Every quote is followed up by our customer service team to confirm details,
                  finalize pricing, and answer any questions you may have.
                </p>
              </div>
              <div className="info-card">
                <h3>🚛 Travel Fee Transparency</h3>
                <p>
                  First 30 miles from our location are completely free. After that, it&apos;s just
                  $2 per mile. No hidden fees or surprise charges.
                </p>
              </div>
            </div>

            <div className="pricing-summary">
              <h3>What&apos;s Always Included</h3>
              <div className="included-grid">
                <div className="included-item">
                  <span className="included-icon">🍽️</span>
                  <span>Your choice of protein - additional charges apply depending on order</span>
                </div>
                <div className="included-item">
                  <span className="included-icon">🍚</span>
                  <span>Hibachi fried rice & fresh vegetables</span>
                </div>
                <div className="included-item">
                  <span className="included-icon">🥗</span>
                  <span>Side salad & signature sauces</span>
                </div>
                <div className="included-item">
                  <span className="included-icon">🍶</span>
                  <span>Plenty of sake for adults 21+</span>
                </div>
                <div className="included-item">
                  <span className="included-icon">👨‍🍳</span>
                  <span>Professional chef & cooking entertainment</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Quote Request Form */}
        <section className="section-background">
          <div className="container">
            <div className="row">
              <div className="col-lg-8 mx-auto">
                <div className="card" style={{ padding: '2rem' }}>
                  <div className="mb-4 text-center">
                    <h2 className="mb-2">Or Request a Custom Quote</h2>
                    <p className="text-muted">
                      Fill out the form below and we&apos;ll get back to you within 24 hours with a
                      personalized quote.
                    </p>
                  </div>
                  <QuoteRequestForm
                    onSuccess={() => {
                      // Track conversion
                      if (typeof window !== 'undefined' && window.dataLayer) {
                        window.dataLayer.push({
                          event: 'quote_request_submit',
                          form_type: 'quote',
                          page: '/quote',
                        })
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>
        <Assistant page="/quote" />
      </main>
    </>
  )
}
