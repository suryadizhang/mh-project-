'use client'

import { useState } from 'react'

interface FaqSearchProps {
  value: string
  onChange: (query: string) => void
  resultsCount: number
}

export function FaqSearch({ value, onChange, resultsCount }: FaqSearchProps) {
  const [isFocused, setIsFocused] = useState(false)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onChange('')
    }
  }

  return (
    <div className="faq-search-container">
      <div className={`faq-search ${isFocused ? 'focused' : ''}`}>
        <div className="search-icon">🔍</div>
        <input
          type="text"
          placeholder="Search FAQs... (Press / to focus)"
          value={value}
          onChange={e => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          className="faq-search-input"
          autoComplete="off"
        />
        {value && (
          <button onClick={() => onChange('')} className="clear-search" aria-label="Clear search">
            ✕
          </button>
        )}
      </div>

      {value && (
        <div className="search-results-info">
          {resultsCount > 0 ? (
            <span className="results-count">
              Found {resultsCount} result{resultsCount !== 1 ? 's' : ''} for &quot;{value}&quot;
            </span>
          ) : (
            <div className="no-results-message">
              <span>No results found for &quot;{value}&quot;</span>
              <a href="/contact" className="ask-question-cta">
                Ask us directly →
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
