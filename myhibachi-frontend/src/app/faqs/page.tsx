'use client'

import { useState, useEffect } from 'react'
import { faqs } from '@/data/faqsData'
import '@/styles/base.css'
import '@/styles/faqs.css'

export default function FAQsPage() {
  const [openFAQ, setOpenFAQ] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredFAQs, setFilteredFAQs] = useState(faqs)

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredFAQs(faqs)
    } else {
      const filtered = faqs.filter(
        faq =>
          faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
          faq.answer.toLowerCase().includes(searchTerm.toLowerCase())
      )
      setFilteredFAQs(filtered)
      setOpenFAQ(null) // Close any open FAQ when searching
    }
  }, [searchTerm])

  const toggleFAQ = (index: number) => {
    setOpenFAQ(openFAQ === index ? null : index)
  }

  return (
    <>
      {/* SEO Meta Tags */}
      <head>
        <title>Frequently Asked Questions – My Hibachi</title>
        <meta 
          name="description" 
          content="Find answers to your most common questions about My Hibachi's private chef catering service. Learn about pricing, booking, menus, and more." 
        />
        <meta name="keywords" content="hibachi catering FAQ, private chef questions, hibachi party booking, My Hibachi" />
      </head>

      <main>
        {/* Hero Section */}
        <section className="faqs-hero">
          <div className="container">
            <h1>Frequently Asked Questions</h1>
            <p>
              Everything you need to know about My Hibachi&apos;s private chef catering service. 
              From booking and pricing to menus and dietary accommodations, we&apos;ve got you covered.
            </p>
          </div>
        </section>

        {/* FAQs Content */}
        <section className="faqs-container">
          {/* Search Bar */}
          <div className="faq-search">
            <input
              type="text"
              placeholder="Search FAQs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="faq-search-input"
            />
          </div>

          {/* Results Count */}
          {searchTerm && (
            <p className="search-results-count">
              Found {filteredFAQs.length} result{filteredFAQs.length !== 1 ? 's' : ''} for &quot;{searchTerm}&quot;
            </p>
          )}

          {/* FAQ Accordion */}
          <div className="faqs-accordion">
            {filteredFAQs.length === 0 ? (
              <div className="no-results">
                <p>No FAQs found matching your search. Try different keywords or browse all questions below.</p>
              </div>
            ) : (
              filteredFAQs.map((faq, index) => (
                <div
                  key={index}
                  className={`faq-item ${openFAQ === index ? 'active' : ''}`}
                >
                  <button
                    onClick={() => toggleFAQ(index)}
                    className="faq-question"
                    aria-expanded={openFAQ === index}
                    aria-controls={`faq-answer-${index}`}
                  >
                    <h3>{faq.question}</h3>
                    <span className="faq-icon">+</span>
                  </button>
                  
                  <div
                    id={`faq-answer-${index}`}
                    className="faq-answer"
                    role="region"
                    aria-labelledby={`faq-question-${index}`}
                  >
                    <div className="faq-answer-content">
                      {faq.answer.split('\n').map((paragraph, pIndex) => (
                        <p key={pIndex} dangerouslySetInnerHTML={{ 
                          __html: paragraph.replace(
                            /contact@myhibachi\.com/g, 
                            '<a href="mailto:contact@myhibachi.com" class="contact-link">contact@myhibachi.com</a>'
                          )
                        }} />
                      ))}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Contact CTA */}
          <div className="contact-highlight" style={{ marginTop: '3rem' }}>
            <h2 style={{ color: '#ff6b35', marginBottom: '1rem' }}>Still have questions?</h2>
            <p style={{ marginBottom: '1rem' }}>
              Our team is here to help you plan the perfect hibachi experience for your event. 
              Contact us for personalized assistance and custom quotes.
            </p>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <a 
                href="mailto:contact@myhibachi.com" 
                className="contact-highlight"
                style={{ 
                  display: 'inline-block',
                  padding: '0.75rem 1.5rem',
                  background: '#ff6b35',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '25px',
                  fontWeight: '600',
                  transition: 'background 0.3s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = '#e55a2b'}
                onMouseOut={(e) => e.currentTarget.style.background = '#ff6b35'}
              >
                📧 Email Us
              </a>
              <a 
                href="/contact"
                style={{
                  display: 'inline-block',
                  padding: '0.75rem 1.5rem',
                  border: '2px solid #ff6b35',
                  color: '#ff6b35',
                  textDecoration: 'none',
                  borderRadius: '25px',
                  fontWeight: '600',
                  transition: 'all 0.3s ease'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = '#ff6b35'
                  e.currentTarget.style.color = 'white'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.color = '#ff6b35'
                }}
              >
                📞 Contact Form
              </a>
              <a 
                href="/booking"
                style={{
                  display: 'inline-block',
                  padding: '0.75rem 1.5rem',
                  background: '#4a2d13',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '25px',
                  fontWeight: '600',
                  transition: 'background 0.3s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = '#3a2310'}
                onMouseOut={(e) => e.currentTarget.style.background = '#4a2d13'}
              >
                🎉 Book Now
              </a>
            </div>
          </div>
        </section>
      </main>
    </>
  )
}
