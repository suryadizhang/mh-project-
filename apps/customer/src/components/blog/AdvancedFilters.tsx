'use client';

import type { BlogPost } from '@my-hibachi/blog-types';
import { ChevronDown, Filter, MapPin, Users, X } from 'lucide-react';
import React, { useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';

interface AdvancedFiltersProps {
  posts: BlogPost[];
  onFiltersChange: (filters: FilterState) => void;
  activeFilters: FilterState;
}

export interface FilterState {
  locations: string[];
  eventSizes: string[];
  searchQuery: string;
  tags: string[];
  categories: string[];
}

const EVENT_SIZES = [
  'Intimate (2-10 people)',
  'Small (10-25 people)',
  'Medium (25-50 people)',
  'Large (50-100 people)',
  'Extra Large (100+ people)',
];

export default function AdvancedFilters({
  posts,
  onFiltersChange,
  activeFilters,
}: AdvancedFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localSearchQuery, setLocalSearchQuery] = useState(activeFilters.searchQuery);

  // ENTERPRISE OPTIMIZATION: Debounced search (Instagram/Facebook pattern)
  // Wait 300ms after user stops typing before triggering filter
  // Prevents excessive re-renders and filter calculations
  const debouncedSearch = useDebouncedCallback(
    (query: string) => {
      handleFilterChange('searchQuery', query);
    },
    300, // 300ms delay - sweet spot for UX
  );

  // Extract unique values from posts
  const uniqueLocations = [...new Set(posts.map((post) => post.serviceArea))]
    .filter(Boolean)
    .sort();
  const uniqueCategories = [...new Set(posts.map((post) => post.category))].sort();
  const allTags = [...new Set(posts.flatMap((post) => post.keywords || []))].sort();

  const handleFilterChange = (
    key: keyof FilterState,
    value: string | string[] | { start: string; end: string },
  ) => {
    const newFilters = { ...activeFilters, [key]: value };
    onFiltersChange(newFilters);
  };

  const handleArrayFilterToggle = (key: keyof FilterState, value: string) => {
    const currentArray = activeFilters[key] as string[];
    const newArray = currentArray.includes(value)
      ? currentArray.filter((item) => item !== value)
      : [...currentArray, value];
    handleFilterChange(key, newArray);
  };

  const clearAllFilters = () => {
    onFiltersChange({
      locations: [],
      eventSizes: [],
      searchQuery: '',
      tags: [],
      categories: [],
    });
  };

  const hasActiveFilters = () => {
    return (
      activeFilters.locations.length > 0 ||
      activeFilters.eventSizes.length > 0 ||
      activeFilters.searchQuery ||
      activeFilters.tags.length > 0 ||
      activeFilters.categories.length > 0
    );
  };

  return (
    <div className="mb-8 rounded-lg border border-gray-200 bg-white shadow-sm">
      {/* Filter Header */}
      <div className="flex items-center justify-between border-b border-gray-200 p-4">
        <div className="flex items-center space-x-2">
          <Filter className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Advanced Filters</h3>
          {hasActiveFilters() && (
            <span className="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800">Active</span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {hasActiveFilters() && (
            <button
              onClick={clearAllFilters}
              className="text-sm font-medium text-red-600 hover:text-red-700"
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
              className={`ml-1 h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="border-b border-gray-100 p-4">
        <div className="relative">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
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
            value={localSearchQuery}
            onChange={(e) => {
              const newQuery = e.target.value;
              setLocalSearchQuery(newQuery); // Update input immediately (responsive UI)
              debouncedSearch(newQuery); // Trigger filter after 300ms delay
            }}
            className="w-full rounded-lg border border-gray-300 py-3 pr-10 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
            style={{ paddingLeft: '3.5rem' }}
          />
          {localSearchQuery && (
            <button
              onClick={() => {
                setLocalSearchQuery('');
                handleFilterChange('searchQuery', '');
              }}
              className="absolute top-1/2 right-3 -translate-y-1/2 transform text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Expandable Filters */}
      {isExpanded && (
        <div className="space-y-6 p-4">
          {/* Quick Category Pills */}
          <div>
            <h4 className="mb-3 text-sm font-medium text-gray-700">Categories</h4>
            <div className="flex flex-wrap gap-2">
              {uniqueCategories.map((category) => (
                <button
                  key={category}
                  onClick={() => handleArrayFilterToggle('categories', category)}
                  className={`rounded-full px-3 py-1 text-sm transition-colors ${
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
            <div className="mb-3 flex items-center space-x-2">
              <MapPin className="h-4 w-4 text-gray-600" />
              <h4 className="text-sm font-medium text-gray-700">Service Areas</h4>
            </div>
            <div className="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
              {uniqueLocations.map((location) => (
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
            <div className="mb-3 flex items-center space-x-2">
              <Users className="h-4 w-4 text-gray-600" />
              <h4 className="text-sm font-medium text-gray-700">Event Size</h4>
            </div>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {EVENT_SIZES.map((size) => (
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
            <h4 className="mb-3 text-sm font-medium text-gray-700">Popular Tags</h4>
            <div className="flex max-h-32 flex-wrap gap-2 overflow-y-auto">
              {allTags.slice(0, 20).map((tag) => (
                <button
                  key={tag}
                  onClick={() => handleArrayFilterToggle('tags', tag)}
                  className={`rounded px-2 py-1 text-xs transition-colors ${
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
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          <div className="flex flex-wrap gap-2">
            {activeFilters.searchQuery && (
              <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-xs text-blue-800">
                Search: &ldquo;{activeFilters.searchQuery}&rdquo;
                <button
                  onClick={() => handleFilterChange('searchQuery', '')}
                  className="ml-2 text-blue-600 hover:text-blue-800"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {activeFilters.categories.map((category) => (
              <span
                key={category}
                className="inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-xs text-purple-800"
              >
                Category: {category}
                <button
                  onClick={() => handleArrayFilterToggle('categories', category)}
                  className="ml-2 text-purple-600 hover:text-purple-800"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            {activeFilters.locations.map((location) => (
              <span
                key={location}
                className="inline-flex items-center rounded-full bg-orange-100 px-3 py-1 text-xs text-orange-800"
              >
                Location: {location}
                <button
                  onClick={() => handleArrayFilterToggle('locations', location)}
                  className="ml-2 text-orange-600 hover:text-orange-800"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
