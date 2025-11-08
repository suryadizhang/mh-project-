'use client';

import type { BlogPost } from '@my-hibachi/blog-types';
import { Filter, Search, X } from 'lucide-react';
import { useEffect, useMemo,useState } from 'react';

import { useCategories, useEventTypes,useServiceAreas } from '@/hooks/useBlogAPI';

import styles from './BlogSearch.module.css';

interface BlogSearchProps {
  posts: BlogPost[];
  onFilteredPosts: (filteredPosts: BlogPost[]) => void;
}

export default function BlogSearch({ posts, onFilteredPosts }: BlogSearchProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedArea, setSelectedArea] = useState('All');
  const [selectedEvent, setSelectedEvent] = useState('All');
  const [showFilters, setShowFilters] = useState(false);

  // Use cached hooks for filter options
  const { data: categoriesData } = useCategories();
  const { data: serviceAreasData } = useServiceAreas();
  const { data: eventTypesData } = useEventTypes();

  // Extract arrays from API responses
  const categories = useMemo(
    () => ['All', ...(categoriesData?.categories ?? [])],
    [categoriesData],
  );
  const serviceAreas = useMemo(
    () => ['All', ...(serviceAreasData?.serviceAreas ?? [])],
    [serviceAreasData],
  );
  const eventTypes = useMemo(
    () => ['All', ...(eventTypesData?.eventTypes ?? [])],
    [eventTypesData],
  );

  useEffect(() => {
    let filtered = posts;

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (post) =>
          post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (post.content && post.content.toLowerCase().includes(searchQuery.toLowerCase())) ||
          post.keywords.some((keyword: string) =>
            keyword.toLowerCase().includes(searchQuery.toLowerCase()),
          ),
      );
    }

    // Category filter
    if (selectedCategory !== 'All') {
      filtered = filtered.filter((post) => post.category === selectedCategory);
    }

    // Service area filter
    if (selectedArea !== 'All') {
      filtered = filtered.filter((post) => post.serviceArea === selectedArea);
    }

    // Event type filter
    if (selectedEvent !== 'All') {
      filtered = filtered.filter((post) => post.eventType === selectedEvent);
    }

    onFilteredPosts(filtered);
  }, [searchQuery, selectedCategory, selectedArea, selectedEvent, posts, onFilteredPosts]);

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory('All');
    setSelectedArea('All');
    setSelectedEvent('All');
  };

  const hasActiveFilters =
    searchQuery || selectedCategory !== 'All' || selectedArea !== 'All' || selectedEvent !== 'All';

  return (
    <div className={styles.container}>
      {/* Search Bar */}
      <div className={styles.searchBar}>
        <div className={styles.inputWrapper}>
          <Search className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search hibachi guides, events, locations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.input}
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className={styles.clearButton}>
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <button onClick={() => setShowFilters(!showFilters)} className={styles.filterToggle}>
          <Filter className="h-4 w-4" />
          Filters
          {hasActiveFilters && <span className={styles.filterBadge}></span>}
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className={styles.filters}>
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className={styles.filterSelect}
            >
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Service Area</label>
            <select
              value={selectedArea}
              onChange={(e) => setSelectedArea(e.target.value)}
              className={styles.filterSelect}
            >
              {serviceAreas.map((area) => (
                <option key={area} value={area}>
                  {area}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Event Type</label>
            <select
              value={selectedEvent}
              onChange={(e) => setSelectedEvent(e.target.value)}
              className={styles.filterSelect}
            >
              {eventTypes.map((event) => (
                <option key={event} value={event}>
                  {event}
                </option>
              ))}
            </select>
          </div>

          {hasActiveFilters && (
            <button onClick={clearFilters} className={styles.clearFilters}>
              Clear All
            </button>
          )}
        </div>
      )}

      {/* Results Counter */}
      <div className={styles.results}>
        {searchQuery && (
          <p className={styles.query}>
            Searching for: <strong>&ldquo;{searchQuery}&rdquo;</strong>
          </p>
        )}
      </div>
    </div>
  );
}
