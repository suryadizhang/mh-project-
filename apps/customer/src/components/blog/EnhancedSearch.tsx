'use client';

import Link from 'next/link';
import React, { useEffect, useRef, useState, useMemo } from 'react';
import type { BlogPost } from '@my-hibachi/blog-types';

import { useAllPosts } from '@/hooks/useBlogAPI';

interface SearchResult {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  category: string;
  author: string;
  date: string;
  matchType: 'title' | 'excerpt' | 'keyword' | 'content';
  matchText: string;
  relevanceScore: number;
}

interface EnhancedSearchProps {
  onResultClick?: (result: SearchResult) => void;
  placeholder?: string;
  maxResults?: number;
  showCategories?: boolean;
  autoFocus?: boolean;
}

const EnhancedSearch: React.FC<EnhancedSearchProps> = ({
  onResultClick,
  placeholder = 'Search blog posts, topics, locations...',
  maxResults = 8,
  showCategories = true,
  autoFocus = false,
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Use cached hook for all posts
  const { data } = useAllPosts();
  const allPosts = useMemo(() => data?.posts ?? [], [data]);

  // Auto focus if requested
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Perform search function
  const performSearch = React.useCallback(
    (searchQuery: string): SearchResult[] => {
      const normalizedQuery = searchQuery.toLowerCase().trim();
      const queryWords = normalizedQuery.split(/\s+/);

      const searchResults: SearchResult[] = [];

      allPosts.forEach((post: BlogPost) => {
        let relevanceScore = 0;
        const matches: { type: SearchResult['matchType']; text: string; score: number }[] = [];

        // Search in title (highest priority)
        const titleMatch = post.title.toLowerCase();
        if (titleMatch.includes(normalizedQuery)) {
          matches.push({ type: 'title', text: post.title, score: 100 });
          relevanceScore += 100;
        } else {
          // Check individual words in title
          const titleWordMatches = queryWords.filter((word) => titleMatch.includes(word));
          if (titleWordMatches.length > 0) {
            matches.push({ type: 'title', text: post.title, score: titleWordMatches.length * 50 });
            relevanceScore += titleWordMatches.length * 50;
          }
        }

        // Search in excerpt
        const excerptMatch = post.excerpt.toLowerCase();
        if (excerptMatch.includes(normalizedQuery)) {
          matches.push({ type: 'excerpt', text: post.excerpt, score: 60 });
          relevanceScore += 60;
        } else {
          const excerptWordMatches = queryWords.filter((word) => excerptMatch.includes(word));
          if (excerptWordMatches.length > 0) {
            matches.push({
              type: 'excerpt',
              text: post.excerpt,
              score: excerptWordMatches.length * 30,
            });
            relevanceScore += excerptWordMatches.length * 30;
          }
        }

        // Search in keywords
        const keywordMatches = post.keywords.filter(
          (keyword: string) =>
            keyword.toLowerCase().includes(normalizedQuery) ||
            queryWords.some((word) => keyword.toLowerCase().includes(word)),
        );
        if (keywordMatches.length > 0) {
          matches.push({
            type: 'keyword',
            text: keywordMatches.join(', '),
            score: keywordMatches.length * 40,
          });
          relevanceScore += keywordMatches.length * 40;
        }

        // Search in category, service area, event type
        const metaFields = [post.category, post.serviceArea, post.eventType]
          .join(' ')
          .toLowerCase();
        if (metaFields.includes(normalizedQuery)) {
          matches.push({
            type: 'content',
            text: `${post.category} • ${post.serviceArea}`,
            score: 30,
          });
          relevanceScore += 30;
        }

        // If we have matches, add to results
        if (matches.length > 0) {
          const bestMatch = matches.reduce((best, current) =>
            current.score > best.score ? current : best,
          );

          searchResults.push({
            id: typeof post.id === 'number' ? post.id : parseInt(String(post.id)),
            title: post.title,
            slug: post.slug,
            excerpt: post.excerpt,
            category: post.category,
            author:
              typeof post.author === 'string'
                ? post.author
                : post.author?.name || 'My Hibachi Team',
            date: post.date,
            matchType: bestMatch.type,
            matchText: bestMatch.text,
            relevanceScore,
          });
        }
      });

      // Sort by relevance and limit results
      return searchResults.sort((a, b) => b.relevanceScore - a.relevanceScore).slice(0, maxResults);
    },
    [maxResults, allPosts],
  );

  // Perform search
  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);

    // Simulate search delay for better UX
    const searchTimeout = setTimeout(() => {
      const searchResults = performSearch(query);
      setResults(searchResults);
      setIsOpen(true);
      setSelectedIndex(-1);
      setIsLoading(false);
    }, 150);

    return () => clearTimeout(searchTimeout);
  }, [query, performSearch]);

  const highlightText = (text: string, query: string) => {
    if (!query) return text;

    const normalizedQuery = query.toLowerCase();
    const queryWords = normalizedQuery.split(/\s+/).filter((word) => word.length > 1);

    let highlightedText = text;

    // Highlight exact phrase first
    const exactRegex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    highlightedText = highlightedText.replace(
      exactRegex,
      '<mark class="bg-yellow-200 px-1 rounded">$1</mark>',
    );

    // Then highlight individual words
    queryWords.forEach((word) => {
      const wordRegex = new RegExp(`(${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      highlightedText = highlightedText.replace(wordRegex, (match) => {
        // Don't double-highlight already marked text
        if (match.includes('<mark')) return match;
        return `<mark class="bg-blue-100 px-1 rounded">${match}</mark>`;
      });
    });

    return highlightedText;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleResultClick(results[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  const handleResultClick = (result: SearchResult) => {
    setQuery('');
    setIsOpen(false);
    setSelectedIndex(-1);

    if (onResultClick) {
      onResultClick(result);
    }
  };

  const getMatchTypeIcon = (matchType: SearchResult['matchType']) => {
    switch (matchType) {
      case 'title':
        return '📄';
      case 'excerpt':
        return '📝';
      case 'keyword':
        return '🏷️';
      case 'content':
        return '📂';
    }
  };

  const getMatchTypeLabel = (matchType: SearchResult['matchType']) => {
    switch (matchType) {
      case 'title':
        return 'Title match';
      case 'excerpt':
        return 'Content match';
      case 'keyword':
        return 'Topic match';
      case 'content':
        return 'Category match';
    }
  };

  return (
    <div ref={searchRef} className="relative w-full max-w-2xl">
      {/* Search Input */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="block w-full rounded-lg border border-gray-300 bg-white py-3 pr-12 pl-10 text-sm leading-5 placeholder-gray-500 focus:border-orange-500 focus:placeholder-gray-400 focus:ring-2 focus:ring-orange-500 focus:outline-none"
        />

        {/* Loading/Clear Button */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3">
          {isLoading ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
          ) : (
            query && (
              <button
                onClick={() => {
                  setQuery('');
                  setIsOpen(false);
                  inputRef.current?.focus();
                }}
                className="text-gray-400 transition-colors hover:text-gray-600"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )
          )}
        </div>
      </div>

      {/* Search Results Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-2 max-h-96 w-full overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
          {results.length > 0 ? (
            <>
              <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
                <span className="text-xs text-gray-600">
                  {results.length} result{results.length !== 1 ? 's' : ''} for &ldquo;{query}&rdquo;
                </span>
              </div>

              {results.map((result, index) => (
                <Link
                  key={result.id}
                  href={`/blog/${result.slug}`}
                  onClick={() => handleResultClick(result)}
                  className={`block px-4 py-3 transition-colors hover:bg-gray-50 ${
                    index === selectedIndex ? 'border-l-4 border-orange-500 bg-orange-50' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="mt-1 flex-shrink-0">
                      <span className="text-lg">{getMatchTypeIcon(result.matchType)}</span>
                    </div>

                    <div className="min-w-0 flex-1">
                      <h4
                        className="line-clamp-1 text-sm font-medium text-gray-900"
                        dangerouslySetInnerHTML={{
                          __html: highlightText(result.title, query),
                        }}
                      />

                      <p
                        className="mt-1 line-clamp-2 text-sm text-gray-600"
                        dangerouslySetInnerHTML={{
                          __html: highlightText(
                            result.matchType === 'excerpt' ? result.excerpt : result.matchText,
                            query,
                          ),
                        }}
                      />

                      <div className="mt-2 flex items-center space-x-2">
                        <span className="text-xs text-gray-500">
                          {getMatchTypeLabel(result.matchType)}
                        </span>
                        {showCategories && (
                          <>
                            <span className="text-xs text-gray-400">•</span>
                            <span className="text-xs text-orange-600">{result.category}</span>
                          </>
                        )}
                        <span className="text-xs text-gray-400">•</span>
                        <span className="text-xs text-gray-500">{result.author}</span>
                      </div>
                    </div>

                    <div className="flex-shrink-0">
                      <div className="text-xs text-gray-400">Score: {result.relevanceScore}</div>
                    </div>
                  </div>
                </Link>
              ))}

              {results.length === maxResults && (
                <div className="border-t border-gray-100 bg-gray-50 px-4 py-2">
                  <Link
                    href={`/blog?search=${encodeURIComponent(query)}`}
                    className="text-xs font-medium text-orange-600 hover:text-orange-700"
                  >
                    View all results for &ldquo;{query}&rdquo; →
                  </Link>
                </div>
              )}
            </>
          ) : (
            <div className="px-4 py-8 text-center">
              <div className="mb-2 text-gray-400">
                <svg
                  className="mx-auto h-8 w-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6M4 8h16a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2v-8a2 2 0 012-2z"
                  />
                </svg>
              </div>
              <p className="text-sm text-gray-500">No results found for &ldquo;{query}&rdquo;</p>
              <p className="mt-1 text-xs text-gray-400">Try different keywords or check spelling</p>
            </div>
          )}
        </div>
      )}

      {/* Search Tips */}
      {query.length === 0 && isOpen && (
        <div className="absolute z-50 mt-2 w-full rounded-lg border border-gray-200 bg-white p-4 shadow-lg">
          <h4 className="mb-2 text-sm font-medium text-gray-900">Search Tips</h4>
          <ul className="space-y-1 text-xs text-gray-600">
            <li>• Search by location: &ldquo;San Francisco&rdquo;, &ldquo;Bay Area&rdquo;</li>
            <li>
              • Search by event: &ldquo;birthday&rdquo;, &ldquo;wedding&rdquo;,
              &ldquo;corporate&rdquo;
            </li>
            <li>
              • Search by season: &ldquo;summer&rdquo;, &ldquo;holiday&rdquo;,
              &ldquo;valentine&rdquo;
            </li>
            <li>• Use quotes for exact phrases: &ldquo;hibachi catering&rdquo;</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default EnhancedSearch;
