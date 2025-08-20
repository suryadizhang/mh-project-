'use client'

import type { FaqItem } from '@/data/faqsData'
import { FaqItemComponent } from './FaqItem'
import { useState } from 'react'

interface FaqListProps {
  items: FaqItem[]
}

// Helper function to group FAQs by category only
function groupFAQsByCategory(faqs: FaqItem[]) {
  const grouped = faqs.reduce((acc, faq) => {
    const category = faq.category
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(faq)
    return acc
  }, {} as Record<string, FaqItem[]>)

  return grouped
}

export function FaqList({ items }: FaqListProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set())

  // Calculate grouped FAQs first
  const groupedFAQs = groupFAQsByCategory(items)

  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    // Start with all categories expanded for better UX
    new Set(Object.keys(groupedFAQs))
  )

  const toggleItem = (id: string) => {
    setOpenItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev)
      if (newSet.has(category)) {
        newSet.delete(category)
      } else {
        newSet.add(category)
      }
      return newSet
    })
  }

  if (items.length === 0) {
    return (
      <div className="no-results">
        <div className="no-results-content">
          <h3>No FAQs found</h3>
          <p>
            If you can&apos;t find what you&apos;re looking for, we&apos;re here to help!
          </p>
          <div className="no-results-actions">
            <a href="/contact" className="contact-cta-btn">
              Contact us directly
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="faq-list">
      <div className="faqs-accordion">
        <div className="faqs-categories">
          {Object.entries(groupedFAQs).map(([category, faqs]) => (
            <div key={category} className="faq-category">
              {/* Category Header */}
              <div className="category-header">
                <button
                  onClick={() => toggleCategory(category)}
                  className="category-toggle"
                  aria-expanded={expandedCategories.has(category)}
                >
                  <div className="category-title-wrapper">
                    <span className="category-icon">📋</span>
                    <h2 className="category-title">{category}</h2>
                  </div>
                  <span className="toggle-icon">
                    {expandedCategories.has(category) ? '▲' : '▼'}
                  </span>
                </button>
                <div className="category-count">
                  {faqs.length} questions
                </div>
              </div>

              {/* Category Content */}
              <div className={`category-content ${expandedCategories.has(category) ? 'expanded' : ''}`}>
                <div className="category-faqs">
                  {faqs.map((faq) => (
                    <FaqItemComponent
                      key={faq.id}
                      faq={faq}
                      isOpen={openItems.has(faq.id)}
                      onToggle={() => toggleItem(faq.id)}
                    />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
