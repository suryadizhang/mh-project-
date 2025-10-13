'use client'

import '@/styles/blog.css'

import { Calendar, User } from 'lucide-react'
import Link from 'next/link'
import { useMemo, useState } from 'react'

import AdvancedFilters, { type FilterState } from '@/components/blog/AdvancedFilters'
import BlogCardImage from '@/components/blog/BlogCardImage'
import Pagination from '@/components/blog/Pagination'
import Assistant from '@/components/chat/Assistant'
import {
  getEventSpecificPosts,
  getFeaturedPosts,
  getRecentPosts,
  getSeasonalPosts
} from '@/data/blogPosts'

// Constants for pagination
const POSTS_PER_PAGE = 9

export default function BlogPage() {
  const featuredPosts = getFeaturedPosts()
  const seasonalPosts = getSeasonalPosts()
  const eventSpecificPosts = getEventSpecificPosts().slice(0, 6)
  const allRecentPosts = getRecentPosts(84) // Get all posts

  // All posts with memoization - ensure unique posts and consistent ordering
  const allPosts = useMemo(() => {
    const combinedPosts = [
      ...featuredPosts,
      ...seasonalPosts,
      ...eventSpecificPosts,
      ...allRecentPosts
    ]

    // Remove duplicates by ID and sort by ID for consistent ordering
    const uniquePosts = combinedPosts.filter(
      (post, index, self) => index === self.findIndex(p => p.id === post.id)
    )

    return uniquePosts.sort((a, b) => a.id - b.id)
  }, [featuredPosts, seasonalPosts, eventSpecificPosts, allRecentPosts])

  // Advanced filter state
  const [filters, setFilters] = useState<FilterState>({
    locations: [],
    eventSizes: [],
    searchQuery: '',
    tags: [],
    categories: []
  })

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)

  // Filter posts based on advanced filters
  const filteredPosts = useMemo(() => {
    return allPosts.filter(post => {
      // Locations filter
      if (
        filters.locations.length > 0 &&
        !filters.locations.some(
          (loc: string) =>
            post.serviceArea.toLowerCase().includes(loc.toLowerCase()) ||
            post.title.toLowerCase().includes(loc.toLowerCase()) ||
            post.keywords.some((keyword: string) => keyword.toLowerCase().includes(loc.toLowerCase()))
        )
      )
        return false

      // Event sizes filter
      if (
        filters.eventSizes.length > 0 &&
        !filters.eventSizes.some(
          (size: string) =>
            post.eventType.toLowerCase().includes(size.toLowerCase()) ||
            post.title.toLowerCase().includes(size.toLowerCase())
        )
      )
        return false

      // Search query filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase()
        const searchableText = [
          post.title,
          post.excerpt,
          post.author,
          post.category,
          post.serviceArea,
          post.eventType,
          ...post.keywords
        ]
          .join(' ')
          .toLowerCase()

        if (!searchableText.includes(query)) return false
      }

      // Tags filter
      if (
        filters.tags.length > 0 &&
        !filters.tags.some((tag: string) =>
          post.keywords.some((keyword: string) => keyword.toLowerCase().includes(tag.toLowerCase()))
        )
      )
        return false

      // Categories filter
      if (filters.categories.length > 0 && !filters.categories.includes(post.category)) return false

      return true
    })
  }, [allPosts, filters])

  // Pagination logic for all posts (not filtered)
  const allPostsExceptFeatured = allPosts.filter(post => !post.featured)
  const totalAllPostsPages = Math.ceil(allPostsExceptFeatured.length / POSTS_PER_PAGE)
  const [allPostsPage, setAllPostsPage] = useState(1)
  const startAllPostsIndex = (allPostsPage - 1) * POSTS_PER_PAGE
  const paginatedAllPosts = allPostsExceptFeatured.slice(
    startAllPostsIndex,
    startAllPostsIndex + POSTS_PER_PAGE
  )

  // Pagination logic for filtered posts
  const totalPages = Math.ceil(filteredPosts.length / POSTS_PER_PAGE)
  const startIndex = (currentPage - 1) * POSTS_PER_PAGE
  const paginatedPosts = filteredPosts.slice(startIndex, startIndex + POSTS_PER_PAGE)

  // Check if we're in "view all posts" mode
  const [showAllPosts, setShowAllPosts] = useState(false)

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return !!(
      filters.locations.length > 0 ||
      filters.eventSizes.length > 0 ||
      filters.searchQuery ||
      filters.categories.length > 0
    )
  }, [filters])

  const handleAdvancedFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters)
    setCurrentPage(1)
  }

  const handleAllPostsPageChange = (page: number) => {
    setAllPostsPage(page)
    // Scroll to top of results
    document.querySelector('[data-all-posts-section]')?.scrollIntoView({
      behavior: 'smooth'
    })
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)

    // Scroll to top of results
    document.querySelector('[data-results-section]')?.scrollIntoView({
      behavior: 'smooth'
    })
  }

  const handleViewAllPosts = () => {
    setShowAllPosts(true)
    setAllPostsPage(1)
  }

  return (
    <div className="min-h-screen bg-white" data-page="blog">
      {/* Clean Hero Section */}
      <section className="bg-slate-50 border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 py-16 text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">My Hibachi Blog</h1>
          <p className="text-lg text-slate-600 mb-8 max-w-2xl mx-auto">
            Professional insights, culinary expertise, and event planning guidance for premium
            hibachi catering
          </p>
        </div>
      </section>

      {/* Advanced Filters - Collapsed by default */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <AdvancedFilters
          posts={allPosts}
          onFiltersChange={handleAdvancedFiltersChange}
          activeFilters={filters}
        />
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 pb-16">
        {!hasActiveFilters && !showAllPosts ? (
          /* Clean Default Layout */
          <div>
            {/* Featured Posts */}
            <section className="mb-16">
              <h2 className="text-2xl font-bold text-slate-900 mb-8">Featured Posts</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {allPosts
                  .filter(post => post.featured)
                  .slice(0, 3)
                  .map(post => (
                    <Link key={post.id} href={`/blog/${post.slug}`} className="block">
                      <article className="blog-card group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer">
                        <BlogCardImage post={post} className="h-48" />
                        <div className="p-6">
                          <div className="flex items-center text-sm text-slate-500 mb-3">
                            <Calendar className="w-4 h-4 mr-1" />
                            <span className="mr-3">{post.date}</span>
                            <User className="w-4 h-4 mr-1" />
                            <span>{post.author}</span>
                          </div>
                          <h3 className="text-xl font-bold text-slate-900 mb-3 hover:text-slate-700">
                            {post.title}
                          </h3>
                          <p className="text-slate-600 mb-4 line-clamp-3">{post.excerpt}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1 rounded-full">
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
              <h2 className="text-2xl font-bold text-slate-900 mb-8">Recent Posts</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
                {allPostsExceptFeatured.slice(0, 6).map(post => (
                  <Link key={post.id} href={`/blog/${post.slug}`} className="block">
                    <article className="blog-card group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer">
                      <BlogCardImage post={post} className="h-48" />
                      <div className="p-6">
                        <div className="flex items-center text-sm text-slate-500 mb-3">
                          <Calendar className="w-4 h-4 mr-1" />
                          <span className="mr-3">{post.date}</span>
                          <User className="w-4 h-4 mr-1" />
                          <span>{post.author}</span>
                        </div>
                        <h3 className="text-xl font-bold text-slate-900 mb-3 hover:text-slate-700">
                          {post.title}
                        </h3>
                        <p className="text-slate-600 mb-4 line-clamp-3">{post.excerpt}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1 rounded-full">
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
                    className="bg-slate-800 hover:bg-slate-900 text-white px-8 py-3 rounded-lg font-medium transition-colors"
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
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-slate-900">
                All Posts ({allPostsExceptFeatured.length} posts)
              </h2>
              <button
                onClick={() => setShowAllPosts(false)}
                className="text-slate-600 hover:text-slate-900 font-medium"
              >
                ← Back to Home
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
              {paginatedAllPosts.map(post => (
                <Link key={post.id} href={`/blog/${post.slug}`} className="block">
                  <article className="blog-card group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer">
                    <BlogCardImage post={post} className="h-48" />
                    <div className="p-6">
                      <div className="flex items-center text-sm text-slate-500 mb-3">
                        <Calendar className="w-4 h-4 mr-1" />
                        <span className="mr-3">{post.date}</span>
                        <User className="w-4 h-4 mr-1" />
                        <span>{post.author}</span>
                      </div>
                      <h3 className="text-xl font-bold text-slate-900 mb-3 hover:text-slate-700">
                        {post.title}
                      </h3>
                      <p className="text-slate-600 mb-4 line-clamp-3">{post.excerpt}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1 rounded-full">
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
            className="bg-white rounded-lg border border-slate-200 shadow-sm p-8"
            data-results-section
          >
            <div className="flex items-center justify-between mb-8">
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
                    tags: []
                  })
                  setCurrentPage(1)
                }}
                className="text-slate-600 hover:text-slate-900 font-medium"
              >
                Clear All Filters
              </button>
            </div>

            {paginatedPosts.length > 0 ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-8">
                  {paginatedPosts.map(post => (
                    <Link key={post.id} href={`/blog/${post.slug}`} className="block">
                      <article className="blog-card group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer">
                        <BlogCardImage post={post} className="h-48" />
                        <div className="p-6">
                          <div className="flex items-center text-sm text-slate-500 mb-3">
                            <Calendar className="w-4 h-4 mr-1" />
                            <span className="mr-3">{post.date}</span>
                            <User className="w-4 h-4 mr-1" />
                            <span>{post.author}</span>
                          </div>
                          <h3 className="text-xl font-bold text-slate-900 mb-3 hover:text-slate-700">
                            {post.title}
                          </h3>
                          <p className="text-slate-600 mb-4 line-clamp-3">{post.excerpt}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1 rounded-full">
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
              <div className="text-center py-12">
                <div className="text-slate-500 text-lg mb-4">
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

      <Assistant page="/blog" />
    </div>
  )
}
