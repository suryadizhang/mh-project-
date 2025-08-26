'use client'

import { useState, useMemo } from 'react'
import type { FaqItem } from '@/data/faqsData'
import { FaqSearch } from './FaqSearch'
import { FaqFilters } from './FaqFilters'
import { FaqList } from './FaqList'

interface FAQsPageContainerProps {
  faqs: FaqItem[]
}

export function FAQsPageContainer({ faqs }: FAQsPageContainerProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('All')
  const [activeTags, setActiveTags] = useState<string[]>([])

  // Get all available tags from FAQs
  const availableTags = useMemo(() => {
    const tagSet = new Set<string>()
    faqs.forEach(faq => {
      if (faq.tags) {
        faq.tags.forEach(tag => tagSet.add(tag))
      }
    })
    return Array.from(tagSet).sort()
  }, [faqs])

  // Filter FAQs based on search, category, and tags
  const filteredFaqs = useMemo(() => {
    return faqs.filter(faq => {
      // Search filter
      const matchesSearch = searchQuery === '' || 
        faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (faq.tags && faq.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())))

      // Category filter
      const matchesCategory = activeCategory === 'All' || faq.category === activeCategory

      // Tags filter
      const matchesTags = activeTags.length === 0 || 
        (faq.tags && activeTags.some(tag => faq.tags!.includes(tag)))

      return matchesSearch && matchesCategory && matchesTags
    })
  }, [faqs, searchQuery, activeCategory, activeTags])

  const handleTagToggle = (tag: string) => {
    setActiveTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    )
  }

  return (
    <div className="faqs-page">
      <div className="faqs-container">
        {/* Page Header */}
        <div className="faqs-header">
          <h1>Frequently Asked Questions</h1>
          <p className="faqs-subtitle">
            Everything you need to know about our hibachi catering services. 
            Can&apos;t find what you&apos;re looking for? <a href="/contact">Contact us directly</a>.
          </p>
        </div>

        {/* Search and Filters */}
        <div className="faqs-controls">
          <FaqSearch 
            value={searchQuery} 
            onChange={setSearchQuery}
            resultsCount={filteredFaqs.length}
          />
          
          <FaqFilters
            activeCategory={activeCategory}
            activeTags={activeTags}
            onCategoryChange={setActiveCategory}
            onTagToggle={handleTagToggle}
            availableTags={availableTags}
          />
        </div>

        {/* FAQ List */}
        <div className="faqs-content">
          <FaqList items={filteredFaqs} />
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
              <a href="/book" className="book-btn secondary">
                Book Your Event
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
