import { faqs } from '@/data/faqsData'
import { FaqList } from '@/components/faq/FaqList'
// import { FreeQuoteButton } from '@/components/quote/FreeQuoteButton' // Removed floating button
import Assistant from '@/components/chat/Assistant'
import '@/styles/base.css'
import '@/styles/faqs/faqs-base.css'
import '@/styles/faqs/faqs-items.css'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: "Hibachi Catering FAQs | Private Chef Questions | Bay Area & Sacramento",
  description: "Get answers to common hibachi catering questions. Pricing, booking, menu options, service areas for Bay Area, Sacramento, San Jose private hibachi chef services.",
  keywords: "hibachi catering faq, private chef questions, hibachi booking questions, bay area hibachi faq, sacramento hibachi questions, hibachi pricing faq, mobile chef questions",
  openGraph: {
    title: "Hibachi Catering FAQs | Private Chef Questions",
    description: "Get answers to common hibachi catering questions about pricing, booking, and service areas.",
    type: 'website'
  }
}

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
        <section className="faqs-hero page-hero-background">
          <div className="container">
            <h1>Frequently Asked Questions</h1>
            <p>
              Everything you need to know about My Hibachi Chef&apos;s private catering service.
              From pricing and booking to menus and dietary accommodations.
            </p>
          </div>
        </section>

        {/* FAQ List */}
        <section className="faqs-content section-background">
          <div className="container">
            <FaqList
              items={faqs}
            />
          </div>
        </section>

        {/* Floating Quote Button removed - users can get quotes from dedicated quote page */}
        <Assistant page="/faqs" />
      </main>
    </>
  )
}
