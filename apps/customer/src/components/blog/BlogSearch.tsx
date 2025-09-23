'use client'

import { Filter, Search, X } from 'lucide-react'
import { useEffect, useState } from 'react'

import type { BlogPost } from '@/data/blogPosts'
import { getAllCategories, getAllEventTypes, getAllServiceAreas } from '@/data/blogPosts'

interface BlogSearchProps {
  posts: BlogPost[]
  onFilteredPosts: (filteredPosts: BlogPost[]) => void
}

export default function BlogSearch({ posts, onFilteredPosts }: BlogSearchProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [selectedArea, setSelectedArea] = useState('All')
  const [selectedEvent, setSelectedEvent] = useState('All')
  const [showFilters, setShowFilters] = useState(false)

  const categories = ['All', ...getAllCategories()]
  const serviceAreas = ['All', ...getAllServiceAreas()]
  const eventTypes = ['All', ...getAllEventTypes()]

  useEffect(() => {
    let filtered = posts

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        post =>
          post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (post.content && post.content.toLowerCase().includes(searchQuery.toLowerCase())) ||
          post.keywords.some(keyword => keyword.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    // Category filter
    if (selectedCategory !== 'All') {
      filtered = filtered.filter(post => post.category === selectedCategory)
    }

    // Service area filter
    if (selectedArea !== 'All') {
      filtered = filtered.filter(post => post.serviceArea === selectedArea)
    }

    // Event type filter
    if (selectedEvent !== 'All') {
      filtered = filtered.filter(post => post.eventType === selectedEvent)
    }

    onFilteredPosts(filtered)
  }, [searchQuery, selectedCategory, selectedArea, selectedEvent, posts, onFilteredPosts])

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedCategory('All')
    setSelectedArea('All')
    setSelectedEvent('All')
  }

  const hasActiveFilters =
    searchQuery || selectedCategory !== 'All' || selectedArea !== 'All' || selectedEvent !== 'All'

  return (
    <div className="blog-search-container">
      {/* Search Bar */}
      <div className="blog-search-bar">
        <div className="blog-search-input-wrapper">
          <Search className="blog-search-icon" />
          <input
            type="text"
            placeholder="Search hibachi guides, events, locations..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="blog-search-input"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="blog-search-clear">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <button onClick={() => setShowFilters(!showFilters)} className="blog-filter-toggle">
          <Filter className="w-4 h-4" />
          Filters
          {hasActiveFilters && <span className="blog-filter-badge"></span>}
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="blog-filters">
          <div className="blog-filter-group">
            <label className="blog-filter-label">Category</label>
            <select
              value={selectedCategory}
              onChange={e => setSelectedCategory(e.target.value)}
              className="blog-filter-select"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>

          <div className="blog-filter-group">
            <label className="blog-filter-label">Service Area</label>
            <select
              value={selectedArea}
              onChange={e => setSelectedArea(e.target.value)}
              className="blog-filter-select"
            >
              {serviceAreas.map(area => (
                <option key={area} value={area}>
                  {area}
                </option>
              ))}
            </select>
          </div>

          <div className="blog-filter-group">
            <label className="blog-filter-label">Event Type</label>
            <select
              value={selectedEvent}
              onChange={e => setSelectedEvent(e.target.value)}
              className="blog-filter-select"
            >
              {eventTypes.map(event => (
                <option key={event} value={event}>
                  {event}
                </option>
              ))}
            </select>
          </div>

          {hasActiveFilters && (
            <button onClick={clearFilters} className="blog-clear-filters">
              Clear All
            </button>
          )}
        </div>
      )}

      {/* Results Counter */}
      <div className="blog-search-results">
        {searchQuery && (
          <p className="blog-search-query">
            Searching for: <strong>&ldquo;{searchQuery}&rdquo;</strong>
          </p>
        )}
      </div>
    </div>
  )
}
