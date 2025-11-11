/**
 * Filter Bar Component
 * Reusable filter bar with search and filter dropdowns
 */

import { Filter, Search, X } from 'lucide-react';

import { Button } from './button';

export interface FilterOption {
  label: string;
  value: string;
}

export interface FilterDefinition {
  key: string;
  label: string;
  options: FilterOption[];
  value?: string;
}

interface FilterBarProps {
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  searchPlaceholder?: string;
  filters?: FilterDefinition[];
  onFilterChange?: (key: string, value: string) => void;
  onClearFilters?: () => void;
  showClearButton?: boolean;
  className?: string;
}

export function FilterBar({
  searchQuery = '',
  onSearchChange,
  searchPlaceholder = 'Search...',
  filters = [],
  onFilterChange,
  onClearFilters,
  showClearButton = false,
  className = '',
}: FilterBarProps) {
  const hasActiveFilters =
    searchQuery ||
    filters.some(f => f.value && f.value !== 'all' && f.value !== '');

  return (
    <div
      className={`bg-white p-4 rounded-lg shadow border border-gray-200 ${className}`}
    >
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search Input */}
        {onSearchChange && (
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={e => onSearchChange(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {searchQuery && (
                <button
                  onClick={() => onSearchChange('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Filter Dropdowns */}
        {filters.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {filters.map(filter => (
              <select
                key={filter.key}
                value={filter.value || 'all'}
                onChange={e => onFilterChange?.(filter.key, e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              >
                <option value="all">{filter.label}</option>
                {filter.options.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ))}

            {/* Clear Filters Button */}
            {(showClearButton || hasActiveFilters) && onClearFilters && (
              <Button
                variant="outline"
                onClick={onClearFilters}
                disabled={!hasActiveFilters}
              >
                <Filter className="w-4 h-4 mr-2" />
                Clear Filters
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
