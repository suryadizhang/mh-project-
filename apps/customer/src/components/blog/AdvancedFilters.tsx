'use client'

import { ChevronDown, Filter, MapPin, Users, X } from 'lucide-react'
import React, { useState } from 'react'

import { BlogPost } from '@/data/blogPosts'

interface AdvancedFiltersProps {
  posts: BlogPost[]
  onFiltersChange: (filters: FilterState) => void
  activeFilters: FilterState
}

export interface FilterState {
  locations: string[]
  eventSizes: string[]
  searchQuery: string
  tags: string[]
  categories: string[]
}

const EVENT_SIZES = [
  'Intimate (2-10 people)',
  'Small (10-25 people)',
  'Medium (25-50 people)',
  'Large (50-100 people)',
  'Extra Large (100+ people)'
]

export default function AdvancedFilters({
  posts,
  onFiltersChange,
  activeFilters
}: AdvancedFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  // Extract unique values from posts
  const uniqueLocations = [...new Set(posts.map(post => post.serviceArea))].filter(Boolean).sort()
  const uniqueCategories = [...new Set(posts.map(post => post.category))].sort()
  const allTags = [...new Set(posts.flatMap(post => post.keywords || []))].sort()

  const handleFilterChange = (
    key: keyof FilterState,
    value: string | string[] | { start: string; end: string }
  ) => {
    const newFilters = { ...activeFilters, [key]: value }
    onFiltersChange(newFilters)
  }

  const handleArrayFilterToggle = (key: keyof FilterState, value: string) => {
    const currentArray = activeFilters[key] as string[]
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value]
    handleFilterChange(key, newArray)
  }

  const clearAllFilters = () => {
    onFiltersChange({
      locations: [],
      eventSizes: [],
      searchQuery: '',
      tags: [],
      categories: []
    })
  }

  const hasActiveFilters = () => {
    return (
      activeFilters.locations.length > 0 ||
      activeFilters.eventSizes.length > 0 ||
      activeFilters.searchQuery ||
      activeFilters.tags.length > 0 ||
      activeFilters.categories.length > 0
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm mb-8">
      {/* Filter Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Advanced Filters</h3>
          {hasActiveFilters() && (
            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">Active</span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {hasActiveFilters() && (
            <button
              onClick={clearAllFilters}
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              Clear All
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center text-sm text-gray-600 hover:text-gray-800"
          >
            {isExpanded ? 'Hide' : 'Show'} Filters
            <ChevronDown
              className={`w-4 h-4 ml-1 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="p-4 border-b border-gray-100">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <svg
              className="h-4 w-4 text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search articles by title, content, or keywords..."
            value={activeFilters.searchQuery}
            onChange={e => handleFilterChange('searchQuery', e.target.value)}
            className="w-full pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            style={{ paddingLeft: '3.5rem' }}
          />
          {activeFilters.searchQuery && (
            <button
              onClick={() => handleFilterChange('searchQuery', '')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Expandable Filters */}
      {isExpanded && (
        <div className="p-4 space-y-6">
          {/* Quick Category Pills */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Categories</h4>
            <div className="flex flex-wrap gap-2">
              {uniqueCategories.map(category => (
                <button
                  key={category}
                  onClick={() => handleArrayFilterToggle('categories', category)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    activeFilters.categories.includes(category)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          {/* Location Filter */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <MapPin className="w-4 h-4 text-gray-600" />
              <h4 className="text-sm font-medium text-gray-700">Service Areas</h4>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {uniqueLocations.map(location => (
                <label key={location} className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={activeFilters.locations.includes(location)}
                    onChange={() => handleArrayFilterToggle('locations', location)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">{location}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Event Size Filter */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <Users className="w-4 h-4 text-gray-600" />
              <h4 className="text-sm font-medium text-gray-700">Event Size</h4>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {EVENT_SIZES.map(size => (
                <label key={size} className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={activeFilters.eventSizes.includes(size)}
                    onChange={() => handleArrayFilterToggle('eventSizes', size)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">{size}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Popular Tags */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Popular Tags</h4>
            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
              {allTags.slice(0, 20).map(tag => (
                <button
                  key={tag}
                  onClick={() => handleArrayFilterToggle('tags', tag)}
                  className={`px-2 py-1 rounded text-xs transition-colors ${
                    activeFilters.tags.includes(tag)
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Active Filters Display */}
      {hasActiveFilters() && (
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <div className="flex flex-wrap gap-2">
            {activeFilters.searchQuery && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                Search: &ldquo;{activeFilters.searchQuery}&rdquo;
                <button
                  onClick={() => handleFilterChange('searchQuery', '')}
                  className="ml-2 text-blue-600 hover:text-blue-800"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {activeFilters.categories.map(category => (
              <span
                key={category}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-purple-100 text-purple-800"
              >
                Category: {category}
                <button
                  onClick={() => handleArrayFilterToggle('categories', category)}
                  className="ml-2 text-purple-600 hover:text-purple-800"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
            {activeFilters.locations.map(location => (
              <span
                key={location}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-orange-100 text-orange-800"
              >
                Location: {location}
                <button
                  onClick={() => handleArrayFilterToggle('locations', location)}
                  className="ml-2 text-orange-600 hover:text-orange-800"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
