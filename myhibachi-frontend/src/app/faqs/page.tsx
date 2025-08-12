'use client'

import { faqs } from '@/data/faqsData'
import { FaqList } from '@/components/faq/FaqList'
import { FreeQuoteButton } from '@/components/quote/FreeQuoteButton'
import '@/styles/base.css'
import '@/styles/faqs.css'

export default function FAQsPage() {
  // Static JSON-LD schema for SEO (using first 10 FAQs from original data)
  const jsonLdSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "name": "My Hibachi Chef - Frequently Asked Questions",
    "url": "https://myhibachichef.com/faqs",
    "mainEntity": faqs.slice(0, 10).map(faq => ({
      "@type": "Question",
      "name": faq.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.answer
      }
    }))
  }

  return (
    <>
      {/* JSON-LD Schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLdSchema)
        }}
      />

      <main className="faqs-page">
        {/* Hero Section */}
        <section className="faqs-hero">
          <div className="container">
            <h1>Frequently Asked Questions</h1>
            <p>
              Everything you need to know about My Hibachi Chef&apos;s private catering service. 
              From pricing and booking to menus and dietary accommodations.
            </p>
          </div>
        </section>

        {/* FAQ List */}
        <section className="faqs-content">
          <div className="container">
            <FaqList 
              items={faqs}
            />
          </div>
        </section>
        
        {/* Floating Quote Button */}
        <FreeQuoteButton variant="floating" />
      </main>
    </>
  )
}
