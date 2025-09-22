'use client';

import { useEffect, useState } from 'react';

import type { FaqItem } from '@/data/faqsData';

import { FaqItemComponent } from './FaqItem';

interface FaqListProps {
  items: FaqItem[];
}

// Helper function to group FAQs by category only
function groupFAQsByCategory(faqs: FaqItem[]) {
  const grouped = faqs.reduce((acc, faq) => {
    const category = faq.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(faq);
    return acc;
  }, {} as Record);

  return grouped;
}

export function FaqList({ items }: FaqListProps) {
  const [openItems, setOpenItems] = useState<Set>(new Set());

  // Start with all categories collapsed initially to prevent hydration errors
  const [expandedCategories, setExpandedCategories] = useState<Set>(new Set());
  const [mounted, setMounted] = useState(false);

  // Calculate grouped FAQs first
  const groupedFAQs = groupFAQsByCategory(items);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleItem = (id: string) => {
    setOpenItems((prev: Set) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev: Set) => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  };

  if (items.length === 0) {
    return (
      <div className="no-results">
        <div className="no-results-content">
          <h3>No FAQs found</h3>
          <p>If you can&apos;t find what you&apos;re looking for, we&apos;re here to help!</p>
          <div className="no-results-actions">
            <a href="/contact" className="contact-cta-btn">
              Contact us directly
            </a>
          </div>
        </div>
      </div>
    );
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
                  aria-expanded={mounted ? expandedCategories.has(category) : false}
                >
                  <div className="category-title-wrapper">
                    <span className="category-icon">📋</span>
                    <h2 className="category-title">{category}</h2>
                  </div>
                  <span className="toggle-icon">▼</span>
                </button>
                <div className="category-count">{faqs.length} questions</div>
              </div>

              {/* Category Content */}
              <div
                className={`category-content ${
                  mounted && expandedCategories.has(category) ? 'expanded' : ''
                }`}
              >
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
  );
}
