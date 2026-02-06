'use client';

import '@/styles/blog.css';

import type { BlogPost } from '@my-hibachi/blog-types';
import { Calendar, User } from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';

import AdvancedFilters, { type FilterState } from '@/components/blog/AdvancedFilters';
import BlogCardImage from '@/components/blog/BlogCardImage';
import Pagination from '@/components/blog/Pagination';
import { useFeaturedPosts, useSeasonalPosts, useRecentPosts } from '@/hooks/useBlogAPI';
import { getAuthorName } from '@/lib/blog/helpers';

// Constants for pagination
const POSTS_PER_PAGE = 9;

export default function BlogPage() {
  // Use cached hooks for blog data
  const { data: featuredData, isLoading: featuredLoading } = useFeaturedPosts();
  const { data: seasonalData, isLoading: seasonalLoading } = useSeasonalPosts();
  const { data: recentData, isLoading: recentLoading } = useRecentPosts(84);

  // Extract posts from API responses with memoization
  const featuredPosts = useMemo(() => featuredData?.posts ?? [], [featuredData]);
  const seasonalPosts = useMemo(() => seasonalData?.posts ?? [], [seasonalData]);
  const allRecentPosts = useMemo(() => recentData?.posts ?? [], [recentData]);

  // Get event-specific posts (first 6)
  const eventSpecificPosts = useMemo(() => {
    return allRecentPosts
      .filter((post: BlogPost) => post.eventType && post.eventType !== 'General')
      .slice(0, 6);
  }, [allRecentPosts]);

  const isLoading = featuredLoading || seasonalLoading || recentLoading;

  // All posts with memoization - ensure unique posts and consistent ordering
  const allPosts = useMemo(() => {
    const combinedPosts = [
      ...featuredPosts,
      ...seasonalPosts,
      ...eventSpecificPosts,
      ...allRecentPosts,
    ];

    // Remove duplicates by ID and sort by ID for consistent ordering
    const uniquePosts = combinedPosts.filter(
      (post, index, self) => index === self.findIndex((p) => p.id === post.id),
    );

    return uniquePosts.sort((a, b) => Number(a.id) - Number(b.id));
  }, [featuredPosts, seasonalPosts, eventSpecificPosts, allRecentPosts]);

  // Advanced filter state
  const [filters, setFilters] = useState<FilterState>({
    locations: [],
    eventSizes: [],
    searchQuery: '',
    tags: [],
    categories: [],
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);

  // Filter posts based on advanced filters
  const filteredPosts = useMemo(() => {
    return allPosts.filter((post) => {
      // Locations filter
      if (
        filters.locations.length > 0 &&
        !filters.locations.some(
          (loc: string) =>
            post.serviceArea.toLowerCase().includes(loc.toLowerCase()) ||
            post.title.toLowerCase().includes(loc.toLowerCase()) ||
            post.keywords.some((keyword: string) =>
              keyword.toLowerCase().includes(loc.toLowerCase()),
            ),
        )
      )
        return false;

      // Event sizes filter
      if (
        filters.eventSizes.length > 0 &&
        !filters.eventSizes.some(
          (size: string) =>
            post.eventType.toLowerCase().includes(size.toLowerCase()) ||
            post.title.toLowerCase().includes(size.toLowerCase()),
        )
      )
        return false;

      // Search query filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const searchableText = [
          post.title,
          post.excerpt,
          post.author,
          post.category,
          post.serviceArea,
          post.eventType,
          ...post.keywords,
        ]
          .join(' ')
          .toLowerCase();

        if (!searchableText.includes(query)) return false;
      }

      // Tags filter
      if (
        filters.tags.length > 0 &&
        !filters.tags.some((tag: string) =>
          post.keywords.some((keyword: string) =>
            keyword.toLowerCase().includes(tag.toLowerCase()),
          ),
        )
      )
        return false;

      // Categories filter
      if (filters.categories.length > 0 && !filters.categories.includes(post.category))
        return false;

      return true;
    });
  }, [allPosts, filters]);

  // Pagination logic for all posts (not filtered)
  const allPostsExceptFeatured = allPosts.filter((post) => !post.featured);
  const totalAllPostsPages = Math.ceil(allPostsExceptFeatured.length / POSTS_PER_PAGE);
  const [allPostsPage, setAllPostsPage] = useState(1);
  const startAllPostsIndex = (allPostsPage - 1) * POSTS_PER_PAGE;
  const paginatedAllPosts = allPostsExceptFeatured.slice(
    startAllPostsIndex,
    startAllPostsIndex + POSTS_PER_PAGE,
  );

  // Pagination logic for filtered posts
  const totalPages = Math.ceil(filteredPosts.length / POSTS_PER_PAGE);
  const startIndex = (currentPage - 1) * POSTS_PER_PAGE;
  const paginatedPosts = filteredPosts.slice(startIndex, startIndex + POSTS_PER_PAGE);

  // Check if we're in "view all posts" mode
  const [showAllPosts, setShowAllPosts] = useState(false);

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return !!(
      filters.locations.length > 0 ||
      filters.eventSizes.length > 0 ||
      filters.searchQuery ||
      filters.categories.length > 0
    );
  }, [filters]);

  const handleAdvancedFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  const handleAllPostsPageChange = (page: number) => {
    setAllPostsPage(page);
    // Scroll to top of results
    document.querySelector('[data-all-posts-section]')?.scrollIntoView({
      behavior: 'smooth',
    });
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);

    // Scroll to top of results
    document.querySelector('[data-results-section]')?.scrollIntoView({
      behavior: 'smooth',
    });
  };

  const handleViewAllPosts = () => {
    setShowAllPosts(true);
    setAllPostsPage(1);
  };

  return (
    <div className="min-h-screen w-full bg-white">
      {/* Loading State */}
      {isLoading && (
        <div className="flex min-h-[60vh] items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-slate-900"></div>
            <p className="text-slate-600">Loading posts...</p>
          </div>
        </div>
      )}

      {/* Content */}
      {!isLoading && (
        <>
          {/* Clean Hero Section */}
          <section className="w-full border-b border-slate-200 bg-slate-50">
            <div
              className="mx-auto max-w-4xl px-4 py-16 text-center"
              style={{ maxWidth: '56rem', marginLeft: 'auto', marginRight: 'auto' }}
            >
              <h1 className="mb-4 text-4xl font-bold text-slate-900">My Hibachi Blog</h1>
              <p className="mx-auto mb-8 max-w-2xl text-lg text-slate-600">
                Professional insights, culinary expertise, and event planning guidance for premium
                hibachi catering
              </p>
            </div>
          </section>

          {/* Advanced Filters - Collapsed by default */}
          <div
            className="mx-auto max-w-6xl px-4 py-8"
            style={{ maxWidth: '72rem', marginLeft: 'auto', marginRight: 'auto' }}
          >
            <AdvancedFilters
              posts={allPosts}
              onFiltersChange={handleAdvancedFiltersChange}
              activeFilters={filters}
            />
          </div>

          {/* Main Content */}
          <div
            className="mx-auto max-w-6xl px-4 pb-16"
            style={{ maxWidth: '72rem', marginLeft: 'auto', marginRight: 'auto' }}
          >
            {!hasActiveFilters && !showAllPosts ? (
              /* Clean Default Layout */
              <div>
                {/* Featured Posts */}
                <section className="mb-16">
                  <h2 className="mb-8 text-2xl font-bold text-slate-900">Featured Posts</h2>
                  <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
                    {allPosts
                      .filter((post) => post.featured)
                      .slice(0, 3)
                      .map((post) => (
                        <Link key={post.id} href={`/blog/${post.slug}`} className="block">
                          <article className="blog-card group cursor-pointer overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-all duration-300 hover:shadow-md">
                            <BlogCardImage post={post} className="h-48" />
                            <div className="p-6">
                              <div className="mb-3 flex items-center text-sm text-slate-500">
                                <Calendar className="mr-1 h-4 w-4" />
                                <span className="mr-3">{post.date}</span>
                                <User className="mr-1 h-4 w-4" />
                                <span>{getAuthorName(post.author)}</span>
                              </div>
                              <h3 className="mb-3 text-xl font-bold text-slate-900 hover:text-slate-700">
                                {post.title}
                              </h3>
                              <p className="mb-4 line-clamp-3 text-slate-600">{post.excerpt}</p>
                              <div className="flex items-center justify-between">
                                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                                  {post.category}
                                </span>
                                <span className="blog-read-more-inline">Read More →</span>
                              </div>
                            </div>
                          </article>
                        </Link>
                      ))}
                  </div>
                </section>

                {/* Recent Posts Preview */}
                <section>
                  <h2 className="mb-8 text-2xl font-bold text-slate-900">Recent Posts</h2>
                  <div className="mb-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
                    {allPostsExceptFeatured.slice(0, 6).map((post) => (
                      <Link key={post.id} href={`/blog/${post.slug}`} className="block">
                        <article className="blog-card group cursor-pointer overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-all duration-300 hover:shadow-md">
                          <BlogCardImage post={post} className="h-48" />
                          <div className="p-6">
                            <div className="mb-3 flex items-center text-sm text-slate-500">
                              <Calendar className="mr-1 h-4 w-4" />
                              <span className="mr-3">{post.date}</span>
                              <User className="mr-1 h-4 w-4" />
                              <span>{getAuthorName(post.author)}</span>
                            </div>
                            <h3 className="mb-3 text-xl font-bold text-slate-900 hover:text-slate-700">
                              {post.title}
                            </h3>
                            <p className="mb-4 line-clamp-3 text-slate-600">{post.excerpt}</p>
                            <div className="flex items-center justify-between">
                              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                                {post.category}
                              </span>
                              <span className="blog-read-more-inline">Read More →</span>
                            </div>
                          </div>
                        </article>
                      </Link>
                    ))}
                  </div>

                  {/* View All Posts Button */}
                  {allPostsExceptFeatured.length > 6 && (
                    <div className="text-center">
                      <button
                        onClick={handleViewAllPosts}
                        className="rounded-lg bg-slate-800 px-8 py-3 font-medium text-white transition-colors hover:bg-slate-900"
                      >
                        View All Posts ({allPostsExceptFeatured.length} total)
                      </button>
                    </div>
                  )}
                </section>
              </div>
            ) : showAllPosts ? (
              /* All Posts with Pagination */
              <div data-all-posts-section>
                <div className="mb-8 flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-slate-900">
                    All Posts ({allPostsExceptFeatured.length} posts)
                  </h2>
                  <button
                    onClick={() => setShowAllPosts(false)}
                    className="font-medium text-slate-600 hover:text-slate-900"
                  >
                    ← Back to Home
                  </button>
                </div>

                <div className="mb-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
                  {paginatedAllPosts.map((post) => (
                    <Link key={post.id} href={`/blog/${post.slug}`} className="block">
                      <article className="blog-card group cursor-pointer overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-all duration-300 hover:shadow-md">
                        <BlogCardImage post={post} className="h-48" />
                        <div className="p-6">
                          <div className="mb-3 flex items-center text-sm text-slate-500">
                            <Calendar className="mr-1 h-4 w-4" />
                            <span className="mr-3">{post.date}</span>
                            <User className="mr-1 h-4 w-4" />
                            <span>{getAuthorName(post.author)}</span>
                          </div>
                          <h3 className="mb-3 text-xl font-bold text-slate-900 hover:text-slate-700">
                            {post.title}
                          </h3>
                          <p className="mb-4 line-clamp-3 text-slate-600">{post.excerpt}</p>
                          <div className="flex items-center justify-between">
                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                              {post.category}
                            </span>
                            <span className="blog-read-more-inline">Read More →</span>
                          </div>
                        </div>
                      </article>
                    </Link>
                  ))}
                </div>

                {/* Pagination for All Posts */}
                {totalAllPostsPages > 1 && (
                  <Pagination
                    currentPage={allPostsPage}
                    totalPages={totalAllPostsPages}
                    onPageChange={handleAllPostsPageChange}
                    className="mt-8"
                  />
                )}
              </div>
            ) : (
              /* Filtered Results */
              <div
                className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm"
                data-results-section
              >
                <div className="mb-8 flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-slate-900">
                    Search Results ({filteredPosts.length}{' '}
                    {filteredPosts.length === 1 ? 'post' : 'posts'})
                  </h2>
                  <button
                    onClick={() => {
                      setFilters({
                        locations: [],
                        eventSizes: [],
                        searchQuery: '',
                        categories: [],
                        tags: [],
                      });
                      setCurrentPage(1);
                    }}
                    className="font-medium text-slate-600 hover:text-slate-900"
                  >
                    Clear All Filters
                  </button>
                </div>

                {paginatedPosts.length > 0 ? (
                  <>
                    <div className="mb-8 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
                      {paginatedPosts.map((post) => (
                        <Link key={post.id} href={`/blog/${post.slug}`} className="block">
                          <article className="blog-card group cursor-pointer overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-all duration-300 hover:shadow-md">
                            <BlogCardImage post={post} className="h-48" />
                            <div className="p-6">
                              <div className="mb-3 flex items-center text-sm text-slate-500">
                                <Calendar className="mr-1 h-4 w-4" />
                                <span className="mr-3">{post.date}</span>
                                <User className="mr-1 h-4 w-4" />
                                <span>{getAuthorName(post.author)}</span>
                              </div>
                              <h3 className="mb-3 text-xl font-bold text-slate-900 hover:text-slate-700">
                                {post.title}
                              </h3>
                              <p className="mb-4 line-clamp-3 text-slate-600">{post.excerpt}</p>
                              <div className="flex items-center justify-between">
                                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                                  {post.category}
                                </span>
                                <span className="blog-read-more-inline">Read More →</span>
                              </div>
                            </div>
                          </article>
                        </Link>
                      ))}
                    </div>

                    {/* Pagination for Filtered Results */}
                    {totalPages > 1 && (
                      <Pagination
                        currentPage={currentPage}
                        totalPages={totalPages}
                        onPageChange={handlePageChange}
                        className="mt-8"
                      />
                    )}
                  </>
                ) : (
                  <div className="py-12 text-center">
                    <div className="mb-4 text-lg text-slate-500">
                      No posts found matching your filters
                    </div>
                    <p className="text-slate-400">
                      Try adjusting your search terms or removing some filters
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
