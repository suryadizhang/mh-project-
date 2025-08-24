'use client'

import type { FAQsPageProps } from './types'
import { JSONLDSchema } from './JSONLDSchema'
import { FAQsHero } from './FAQsHero'
import { FAQsContent } from './FAQsContent'
import { FAQsListContainer } from './FAQsListContainer'
import Assistant from '@/components/chat/Assistant'
import styles from './styles/FAQsPageContainer.module.css'

export function FAQsPageContainer({ faqs }: FAQsPageProps) {
  return (
    <>
      {/* JSON-LD Schema for SEO */}
      <JSONLDSchema faqs={faqs} />

      <main className={`${styles.faqsPage} faqs-page`}>
        {/* Hero Section */}
        <FAQsHero 
          title="Frequently Asked Questions"
          description="Everything you need to know about My Hibachi Chef's private catering service. From pricing and booking to menus and dietary accommodations."
        />

        {/* FAQ Content */}
        <FAQsContent>
          <FAQsListContainer faqs={faqs} />
        </FAQsContent>

        {/* Chat Assistant */}
        <Assistant />
      </main>
    </>
  )
}
