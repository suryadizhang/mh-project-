'use client'

import type { FaqItem } from '@/data/faqsData'
import { useState, useRef, useEffect } from 'react'

interface FaqItemComponentProps {
  faq: FaqItem
  isOpen: boolean
  onToggle: () => void
}

export function FaqItemComponent({ faq, isOpen, onToggle }: FaqItemComponentProps) {
  const answerRef = useRef<HTMLDivElement>(null)
  const [wasHelpful, setWasHelpful] = useState<boolean | null>(null)

  useEffect(() => {
    // Auto-expand if this FAQ matches a hash in URL
    const hash = window.location.hash.slice(1)
    if (hash === faq.id && !isOpen) {
      onToggle()
      setTimeout(() => {
        document.getElementById(faq.id)?.scrollIntoView({ behavior: 'smooth' })
      }, 300)
    }
  }, [faq.id, isOpen, onToggle])

  const trackHelpfulness = (helpful: boolean) => {
    setWasHelpful(helpful)
    // Analytics tracking would go here
    console.log('FAQ Feedback:', { faq_id: faq.id, helpful, category: faq.category })
  }

  return (
    <div
      id={faq.id}
      className={`faq-item ${isOpen ? 'active' : ''} ${faq.confidence === 'low' ? 'low-confidence' : ''}`}
      data-category={faq.category.toLowerCase().replace(/[^a-z0-9]/g, '-')}
    >
      <button
        onClick={onToggle}
        className="faq-toggle"
        aria-expanded={isOpen}
        aria-controls={`faq-answer-${faq.id}`}
        id={`faq-question-${faq.id}`}
      >
        <h3 className="faq-question">{faq.question}</h3>
        <div className="faq-meta">
          {faq.confidence === 'low' && (
            <span className="confidence-indicator" title="This answer may need verification">⚠️</span>
          )}
          <span className="faq-toggle-icon" aria-hidden="true">
            {isOpen ? '−' : '+'}
          </span>
        </div>
      </button>

      <div
        id={`faq-answer-${faq.id}`}
        className={`faq-answer ${isOpen ? 'expanded' : ''}`}
        role="region"
        aria-labelledby={`faq-question-${faq.id}`}
        ref={answerRef}
      >
        <div className="faq-answer-content">
          <div dangerouslySetInnerHTML={{ __html: faq.answer }} />

          {/* Feedback and actions */}
          <div className="faq-actions">
            <div className="helpfulness">
              <span className="helpfulness-label">Was this helpful?</span>
              <button
                onClick={() => trackHelpfulness(true)}
                className={`helpfulness-btn ${wasHelpful === true ? 'active' : ''}`}
                aria-label="Mark as helpful"
              >
                👍
              </button>
              <button
                onClick={() => trackHelpfulness(false)}
                className={`helpfulness-btn ${wasHelpful === false ? 'active' : ''}`}
                aria-label="Mark as not helpful"
              >
                👎
              </button>
            </div>
          </div>

          {/* Category and tags */}
          <div className="faq-metadata">
            <span className="faq-category">{faq.category}</span>
            {faq.tags.length > 0 && (
              <div className="faq-tags">
                {faq.tags.slice(0, 3).map(tag => (
                  <span key={tag} className="faq-tag">{tag}</span>
                ))}
              </div>
            )}
            {faq.review_needed && (
              <span className="review-needed" title="This information may need review">
                Review needed
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
