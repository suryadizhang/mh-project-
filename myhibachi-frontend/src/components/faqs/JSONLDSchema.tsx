'use client'

import type { JSONLDSchemaProps } from './types'

export function JSONLDSchema({ 
  faqs, 
  url = "https://myhibachichef.com/faqs",
  name = "My Hibachi Chef - Frequently Asked Questions"
}: JSONLDSchemaProps) {
  const jsonLdSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "name": name,
    "url": url,
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
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(jsonLdSchema)
      }}
    />
  )
}
