'use client';

import { useState } from 'react';

interface FaqFiltersProps {
  activeCategory: string;
  activeTags: string[];
  onCategoryChange: (category: string) => void;
  onTagToggle: (tag: string) => void;
  availableTags: string[];
}

export function FaqFilters({
  activeCategory,
  activeTags,
  onCategoryChange,
  onTagToggle,
  availableTags,
}: FaqFiltersProps) {
  const [showAllTags, setShowAllTags] = useState(false);

  // Define categories locally to avoid import issues
  const categories = [
    'Pricing & Minimums',
    'Menu & Upgrades',
    'Booking & Payments',
    'Travel & Service Area',
    'On-Site Setup & Requirements',
    'Dietary & Allergens',
    'Policies (Cancellation, Weather, Refunds)',
    'Kids & Special Occasions',
    'Corporate & Insurance',
    'Contact & Response Times',
  ];

  const maxVisibleTags = 6;
  const visibleTags = showAllTags ? availableTags : availableTags.slice(0, maxVisibleTags);

  return (
    <div className="faq-filters">
      {/* Category Tabs */}
      <div className="category-tabs">
        <button
          onClick={() => onCategoryChange('All')}
          className={`category-tab ${activeCategory === 'All' ? 'active' : ''}`}
          data-category="all"
        >
          All Questions
        </button>
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => onCategoryChange(category)}
            className={`category-tab ${activeCategory === category ? 'active' : ''}`}
            data-category={category.toLowerCase().replace(/[^a-z0-9]/g, '-')}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Tag Filters - Compact & Collapsible */}
      {availableTags.length > 0 && (
        <div className="tag-filters">
          <div className="tag-chips">
            {visibleTags.map((tag) => (
              <button
                key={tag}
                onClick={() => onTagToggle(tag)}
                className={`tag-chip ${activeTags.includes(tag) ? 'active' : ''}`}
                data-tag={tag}
              >
                {tag}
                {activeTags.includes(tag) && <span className="tag-remove">×</span>}
              </button>
            ))}
            {availableTags.length > maxVisibleTags && (
              <button onClick={() => setShowAllTags(!showAllTags)} className="more-tags-toggle">
                {showAllTags
                  ? '← Show Less'
                  : `+${availableTags.length - maxVisibleTags} more topics`}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Active Filters Summary - Only show if there are active filters */}
      {(activeCategory !== 'All' || activeTags.length > 0) && (
        <div className="active-filters">
          {activeCategory !== 'All' && (
            <span className="active-filter">
              {activeCategory}
              <button onClick={() => onCategoryChange('All')} className="remove-filter">
                ×
              </button>
            </span>
          )}
          {activeTags.map((tag) => (
            <span key={tag} className="active-filter">
              {tag}
              <button onClick={() => onTagToggle(tag)} className="remove-filter">
                ×
              </button>
            </span>
          ))}
          <button
            onClick={() => {
              onCategoryChange('All');
              activeTags.forEach((tag) => onTagToggle(tag));
            }}
            className="clear-all-filters"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}
