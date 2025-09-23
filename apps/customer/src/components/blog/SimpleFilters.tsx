'use client'

import { ChevronDown, MapPin, Search, Users, X } from 'lucide-react'
import React, { useState } from 'react'

import { BlogPost } from '@/data/blogPosts'

interface SimpleFiltersProps {
  posts: BlogPost[]
  onFiltersChange: (filters: FilterState) => void
  activeFilters: FilterState
}

export interface FilterState {
  locations: string[]
  eventSizes: string[]
  searchQuery: string
  categories: string[]
}

const EVENT_SIZES = [
  'Intimate (2-10 people)',
  'Small (10-25 people)',
  'Medium (25-50 people)',
  'Large (50-100 people)',
  'Extra Large (100+ people)'
]

export default function SimpleFilters({
  posts,
  onFiltersChange,
  activeFilters
}: SimpleFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  // Extract unique values from posts
  const uniqueLocations = [...new Set(posts.map(post => post.serviceArea))].filter(Boolean).sort()
  const uniqueCategories = [...new Set(posts.map(post => post.category))].sort()

  const handleFilterChange = (key: keyof FilterState, value: string | string[]) => {
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
      categories: []
    })
  }

  const hasActiveFilters = () => {
    return (
      activeFilters.locations.length > 0 ||
      activeFilters.eventSizes.length > 0 ||
      activeFilters.searchQuery ||
      activeFilters.categories.length > 0
    )
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm mb-8">
      {/* Filter Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          <Search className="w-5 h-5 text-slate-600" />
          <h3 className="text-lg font-semibold text-slate-900">Search & Filter</h3>
          {hasActiveFilters() && (
            <span className="bg-slate-100 text-slate-700 text-xs px-2 py-1 rounded-full">
              Active
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {hasActiveFilters() && (
            <button
              onClick={clearAllFilters}
              className="text-sm text-slate-600 hover:text-slate-900 font-medium"
            >
              Clear All
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center text-sm text-slate-600 hover:text-slate-800"
          >
            {isExpanded ? 'Hide' : 'Show'} Filters
            <ChevronDown
              className={`w-4 h-4 ml-1 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="p-4 border-b border-slate-100">
        <div className="relative">
          <input
            type="text"
            placeholder="Search posts by title, content, or keywords..."
            value={activeFilters.searchQuery}
            onChange={e => handleFilterChange('searchQuery', e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-500 focus:border-transparent text-slate-900 placeholder-slate-500"
          />
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
          {activeFilters.searchQuery && (
            <button
              onClick={() => handleFilterChange('searchQuery', '')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Expandable Filters */}
      {isExpanded && (
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Location Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                <MapPin className="w-4 h-4 inline mr-2" />
                Locations
              </label>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {uniqueLocations.map(location => (
                  <label key={location} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={activeFilters.locations.includes(location)}
                      onChange={() => handleArrayFilterToggle('locations', location)}
                      className="rounded border-slate-300 text-slate-600 focus:ring-slate-500"
                    />
                    <span className="ml-2 text-sm text-slate-700">{location}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Event Size Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                <Users className="w-4 h-4 inline mr-2" />
                Event Size
              </label>
              <div className="space-y-2">
                {EVENT_SIZES.map(size => (
                  <label key={size} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={activeFilters.eventSizes.includes(size)}
                      onChange={() => handleArrayFilterToggle('eventSizes', size)}
                      className="rounded border-slate-300 text-slate-600 focus:ring-slate-500"
                    />
                    <span className="ml-2 text-sm text-slate-700">{size}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">Categories</label>
              <div className="space-y-2">
                {uniqueCategories.map(category => (
                  <label key={category} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={activeFilters.categories.includes(category)}
                      onChange={() => handleArrayFilterToggle('categories', category)}
                      className="rounded border-slate-300 text-slate-600 focus:ring-slate-500"
                    />
                    <span className="ml-2 text-sm text-slate-700">{category}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Active Filters Display */}
      {hasActiveFilters() && (
        <div className="p-4 bg-slate-50 border-t border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700">Active Filters:</span>
            <button
              onClick={clearAllFilters}
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Clear All
            </button>
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {activeFilters.searchQuery && (
              <span className="inline-flex items-center bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-sm">
                Search: &ldquo;{activeFilters.searchQuery}&rdquo;
                <button
                  onClick={() => handleFilterChange('searchQuery', '')}
                  className="ml-2 text-slate-500 hover:text-slate-700"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {activeFilters.locations.map(location => (
              <span
                key={location}
                className="inline-flex items-center bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-sm"
              >
                📍 {location}
                <button
                  onClick={() => handleArrayFilterToggle('locations', location)}
                  className="ml-2 text-slate-500 hover:text-slate-700"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
            {activeFilters.eventSizes.map(size => (
              <span
                key={size}
                className="inline-flex items-center bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-sm"
              >
                👥 {size}
                <button
                  onClick={() => handleArrayFilterToggle('eventSizes', size)}
                  className="ml-2 text-slate-500 hover:text-slate-700"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
            {activeFilters.categories.map(category => (
              <span
                key={category}
                className="inline-flex items-center bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-sm"
              >
                {category}
                <button
                  onClick={() => handleArrayFilterToggle('categories', category)}
                  className="ml-2 text-slate-500 hover:text-slate-700"
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
