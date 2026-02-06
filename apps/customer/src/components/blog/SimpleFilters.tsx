'use client';

import type { BlogPost } from '@my-hibachi/blog-types';
import { ChevronDown, MapPin, Search, Users, X } from 'lucide-react';
import React, { useState } from 'react';

interface SimpleFiltersProps {
  posts: BlogPost[];
  onFiltersChange: (filters: FilterState) => void;
  activeFilters: FilterState;
}

export interface FilterState {
  locations: string[];
  eventSizes: string[];
  searchQuery: string;
  categories: string[];
}

const EVENT_SIZES = [
  'Intimate (2-10 people)',
  'Small (10-25 people)',
  'Medium (25-50 people)',
  'Large (50-100 people)',
  'Extra Large (100+ people)',
];

export default function SimpleFilters({
  posts,
  onFiltersChange,
  activeFilters,
}: SimpleFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Extract unique values from posts
  const uniqueLocations = [...new Set(posts.map((post) => post.serviceArea))]
    .filter(Boolean)
    .sort();
  const uniqueCategories = [...new Set(posts.map((post) => post.category))].sort();

  const handleFilterChange = (key: keyof FilterState, value: string | string[]) => {
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
      categories: [],
    });
  };

  const hasActiveFilters = () => {
    return (
      activeFilters.locations.length > 0 ||
      activeFilters.eventSizes.length > 0 ||
      activeFilters.searchQuery ||
      activeFilters.categories.length > 0
    );
  };

  return (
    <div className="mb-8 rounded-lg border border-slate-200 bg-white shadow-sm">
      {/* Filter Header */}
      <div className="flex items-center justify-between border-b border-slate-200 p-4">
        <div className="flex items-center space-x-2">
          <Search className="h-5 w-5 text-slate-600" />
          <h3 className="text-lg font-semibold text-slate-900">Search & Filter</h3>
          {hasActiveFilters() && (
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
              Active
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {hasActiveFilters() && (
            <button
              onClick={clearAllFilters}
              className="text-sm font-medium text-slate-600 hover:text-slate-900"
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
              className={`ml-1 h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="border-b border-slate-100 p-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Search posts by title, content, or keywords..."
            value={activeFilters.searchQuery}
            onChange={(e) => handleFilterChange('searchQuery', e.target.value)}
            className="w-full rounded-lg border border-slate-300 py-3 pr-4 pl-10 text-slate-900 placeholder-slate-500 focus:border-transparent focus:ring-2 focus:ring-slate-500"
          />
          <Search className="absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 transform text-slate-400" />
          {activeFilters.searchQuery && (
            <button
              onClick={() => handleFilterChange('searchQuery', '')}
              className="absolute top-1/2 right-3 -translate-y-1/2 transform text-slate-400 hover:text-slate-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Expandable Filters */}
      {isExpanded && (
        <div className="space-y-6 p-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {/* Location Filter */}
            <div>
              <label className="mb-3 block text-sm font-medium text-slate-700">
                <MapPin className="mr-2 inline h-4 w-4" />
                Locations
              </label>
              <div className="max-h-40 space-y-2 overflow-y-auto">
                {uniqueLocations.map((location) => (
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
              <label className="mb-3 block text-sm font-medium text-slate-700">
                <Users className="mr-2 inline h-4 w-4" />
                Event Size
              </label>
              <div className="space-y-2">
                {EVENT_SIZES.map((size) => (
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
              <label className="mb-3 block text-sm font-medium text-slate-700">Categories</label>
              <div className="space-y-2">
                {uniqueCategories.map((category) => (
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
        <div className="border-t border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700">Active Filters:</span>
            <button
              onClick={clearAllFilters}
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Clear All
            </button>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {activeFilters.searchQuery && (
              <span className="inline-flex items-center rounded-full bg-slate-200 px-3 py-1 text-sm text-slate-700">
                Search: &ldquo;{activeFilters.searchQuery}&rdquo;
                <button
                  onClick={() => handleFilterChange('searchQuery', '')}
                  className="ml-2 text-slate-500 hover:text-slate-700"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {activeFilters.locations.map((location) => (
              <span
                key={location}
                className="inline-flex items-center rounded-full bg-slate-200 px-3 py-1 text-sm text-slate-700"
              >
                📍 {location}
                <button
                  onClick={() => handleArrayFilterToggle('locations', location)}
                  className="ml-2 text-slate-500 hover:text-slate-700"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            {activeFilters.eventSizes.map((size) => (
              <span
                key={size}
                className="inline-flex items-center rounded-full bg-slate-200 px-3 py-1 text-sm text-slate-700"
              >
                👥 {size}
                <button
                  onClick={() => handleArrayFilterToggle('eventSizes', size)}
                  className="ml-2 text-slate-500 hover:text-slate-700"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            {activeFilters.categories.map((category) => (
              <span
                key={category}
                className="inline-flex items-center rounded-full bg-slate-200 px-3 py-1 text-sm text-slate-700"
              >
                {category}
                <button
                  onClick={() => handleArrayFilterToggle('categories', category)}
                  className="ml-2 text-slate-500 hover:text-slate-700"
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
