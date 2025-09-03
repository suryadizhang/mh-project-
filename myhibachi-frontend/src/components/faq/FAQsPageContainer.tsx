'use client'

import type { FaqItem } from '@/data/faqsData'
import { FaqList } from './FaqList'

interface FAQsPageContainerProps {
  faqs: FaqItem[]
}

export function FAQsPageContainer({ faqs }: FAQsPageContainerProps) {
  return (
    <div className="faqs-page">
      <div className="faqs-container">
        {/* Page Header */}
        <div className="faqs-header">
          <h1>Frequently Asked Questions</h1>
          <p className="faqs-subtitle">
            Everything you need to know about our hibachi catering services. Can&apos;t find what
            you&apos;re looking for? <a href="/contact">Contact us directly</a>.
          </p>
        </div>

        {/* FAQ List */}
        <div className="faqs-content">
          <FaqList items={faqs} />
        </div>

        {/* Help Section */}
        <div className="faqs-help">
          <div className="help-content">
            <h3>Still have questions?</h3>
            <p>We&apos;re here to help! Get in touch with our team for personalized assistance.</p>
            <div className="help-actions">
              <a href="/contact" className="contact-btn primary">
                Contact Us
              </a>
              <a href="/BookUs" className="book-btn secondary">
                Book Your Event
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
