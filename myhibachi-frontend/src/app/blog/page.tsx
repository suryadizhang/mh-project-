'use client'

import Link from 'next/link'
import { useState, useMemo } from 'react'
import { Calendar, User, Search, X } from 'lucide-react'
import Assistant from '@/components/chat/Assistant'
import BlogTags from '@/components/blog/BlogTags'
import BlogCategories from '@/components/blog/BlogCategories'
import { getFeaturedPosts, getSeasonalPosts, getRecentPosts, getEventSpecificPosts } from '@/data/blogPosts'
import '@/styles/blog.css'

export default function BlogPage() {
  const featuredPosts = getFeaturedPosts()
  const seasonalPosts = getSeasonalPosts()
  const eventSpecificPosts = getEventSpecificPosts().slice(0, 6) // Get first 6 new event posts
  const allRecentPosts = getRecentPosts(12)
  // All posts with memoization to prevent re-renders
  const allPosts = useMemo(() => [
    ...featuredPosts, 
    ...seasonalPosts, 
    ...eventSpecificPosts, 
    ...allRecentPosts
  ], [featuredPosts, seasonalPosts, eventSpecificPosts, allRecentPosts])

  // State for filtering
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState('')
  
  // Filter posts based on search, tags, and category
  const filteredPosts = useMemo(() => {
    let filtered = allPosts;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(post =>
        post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (post.content && post.content.toLowerCase().includes(searchQuery.toLowerCase())) ||
        post.keywords.some((keyword: string) => keyword.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // Apply tag filter
    if (selectedTags.length > 0) {
      filtered = filtered.filter(post =>
        selectedTags.some(tag => post.keywords.includes(tag))
      );
    }

    // Apply category filter
    if (selectedCategory && selectedCategory !== 'All') {
      filtered = filtered.filter(post => post.category === selectedCategory);
    }

    return filtered;
  }, [allPosts, searchQuery, selectedTags, selectedCategory]);

  // Check if any filters are active
  const hasActiveFilters = searchQuery || selectedTags.length > 0 || (selectedCategory && selectedCategory !== 'All');

  const handleTagFilter = (tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag]
    
    setSelectedTags(newTags)
  }

  const handleCategoryFilter = (category: string) => {
    setSelectedCategory(category)
  }

  const clearTags = () => {
    setSelectedTags([])
  }

  return (
    <div className="min-h-screen">
      {/* Hero Section with Company Background */}
      <section className="page-hero-background py-20 text-white text-center mb-24">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-5xl font-bold mb-6">My Hibachi Blog</h1>
          <p className="text-xl mb-8 text-gray-200">
            Your source for hibachi catering inspiration, seasonal menus, and event planning tips across the Bay Area, Sacramento, San Jose & beyond
          </p>
          <div className="text-lg mb-12">
            <span className="bg-orange-600 text-white px-4 py-2 rounded-full">Expert Hibachi Catering Insights</span>
          </div>
        </div>
      </section>

      {/* Search and Filter Section */}
      <div className="blog-section">
        <div className="max-w-6xl mx-auto px-4">
          <div className="blog-search-container">
            <div className="blog-search-bar">
              <div className="blog-search-input-wrapper">
                <Search className="blog-search-icon" />
                <input
                  type="text"
                  placeholder="Search hibachi guides, events, locations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="blog-search-input"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="blog-search-clear"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tags and Categories Section */}
      <div className="blog-section">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BlogTags 
              posts={allPosts}
              onTagFilter={handleTagFilter}
              selectedTags={selectedTags}
              onClearTags={clearTags}
            />
            <BlogCategories 
              posts={allPosts}
              onCategoryFilter={handleCategoryFilter}
              selectedCategory={selectedCategory}
            />
          </div>
        </div>
      </div>

      {/* Filtered Results Section */}
      {hasActiveFilters && (
        <div className="blog-section">
          <div className="max-w-6xl mx-auto px-4">
            <div className="blog-filter-results">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  Search Results ({filteredPosts.length} {filteredPosts.length === 1 ? 'post' : 'posts'})
                </h2>
                <button 
                  onClick={() => {
                    setSearchQuery('')
                    setSelectedTags([])
                    setSelectedCategory('')
                  }}
                  className="text-orange-600 hover:text-orange-700 font-medium"
                >
                  Clear All Filters
                </button>
              </div>
              
              {/* Active Filters Display */}
              <div className="flex flex-wrap gap-2 mb-6">
                {searchQuery && (
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                    Search: &ldquo;{searchQuery}&rdquo;
                    <button 
                      onClick={() => setSearchQuery('')}
                      className="ml-2 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                )}
                {selectedTags.map(tag => (
                  <span key={tag} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                    Tag: {tag}
                    <button 
                      onClick={() => handleTagFilter(tag)}
                      className="ml-2 text-green-600 hover:text-green-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
                {selectedCategory && selectedCategory !== 'All' && (
                  <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                    Category: {selectedCategory}
                    <button 
                      onClick={() => setSelectedCategory('')}
                      className="ml-2 text-purple-600 hover:text-purple-800"
                    >
                      ×
                    </button>
                  </span>
                )}
              </div>

              {/* Filtered Posts Grid */}
              {filteredPosts.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredPosts.map((post) => (
                    <article key={post.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                      <div className="h-40 bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
                        <div className="text-white text-center p-4">
                          <div className="text-sm font-medium bg-black bg-opacity-30 rounded px-2 py-1">
                            {post.serviceArea} • {post.eventType}
                          </div>
                        </div>
                      </div>
                      <div className="p-4">
                        <div className="flex items-center text-sm text-gray-500 mb-2">
                          <Calendar className="w-4 h-4 mr-1" />
                          <span className="mr-3">{post.date}</span>
                          <User className="w-4 h-4 mr-1" />
                          <span>{post.author}</span>
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-2">
                          <Link href={`/blog/${post.slug}`} className="hover:text-blue-600">
                            {post.title}
                          </Link>
                        </h3>
                        <p className="text-gray-600 text-sm mb-3 line-clamp-2">{post.excerpt}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">{post.readTime}</span>
                          <Link
                            href={`/blog/${post.slug}`}
                            className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                          >
                            Read More →
                          </Link>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-gray-500 text-lg mb-4">No posts found matching your filters</div>
                  <p className="text-gray-400">Try adjusting your search terms or removing some filters</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Featured Posts Section */}
      <div className="pt-24 pb-20 section-background" style={{backgroundColor: '#f8f9fa'}}>
        <div className="max-w-6xl mx-auto px-4">
          <div className="mb-20" style={{backgroundColor: 'white', padding: '3rem', borderRadius: '15px', boxShadow: '0 10px 30px rgba(0,0,0,0.1)'}}>
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">Must-Read Hibachi Guides</h2>
            <p className="text-lg text-gray-600 text-center max-w-3xl mx-auto">
              Popular hibachi catering guides for your local area events
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
            {featuredPosts.map((post) => (
              <article key={post.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                <div className="h-48 bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
                  <div className="text-white text-center p-4">
                    <div className="text-sm font-medium bg-black bg-opacity-30 rounded px-2 py-1 mb-2">
                      {post.serviceArea} • {post.eventType}
                    </div>
                  </div>
                </div>
                <div className="p-6">
                  <div className="flex items-center text-sm text-gray-500 mb-3">
                    <Calendar className="w-4 h-4 mr-1" />
                    <span className="mr-4">{post.date}</span>
                    <User className="w-4 h-4 mr-1" />
                    <span>{post.author}</span>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">
                    <Link href={`/blog/${post.slug}`} className="hover:text-blue-600">
                      {post.title}
                    </Link>
                  </h3>
                  <p className="text-gray-600 mb-4">{post.excerpt}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">{post.readTime}</span>
                    <Link
                      href={`/blog/${post.slug}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Read More →
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Event-Specific Posts Section */}
          <div className="blog-section-header">
            <h2 className="blog-section-title">Event-Specific Hibachi Guides</h2>
            <p className="blog-section-subtitle">
              Complete hibachi catering guides for every type of celebration and event
            </p>
          </div>

          <div className="blog-posts-grid">
            {eventSpecificPosts.map((post) => (
              <article key={post.id} className="blog-card category-event">
                <div className="blog-card-image">
                  <div className="blog-card-badges">
                    <div className="blog-card-badge">
                      🎉 {post.eventType}
                    </div>
                    <div className="blog-card-badge">
                      📍 {post.serviceArea}
                    </div>
                  </div>
                </div>
                <div className="blog-card-content">
                  <div className="blog-card-meta">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      <span className="mr-4">{post.date}</span>
                    </div>
                    <span className="blog-card-badge blog-badge-new">NEW</span>
                  </div>
                  <h3 className="blog-card-title">
                    <Link href={`/blog/${post.slug}`}>
                      {post.title}
                    </Link>
                  </h3>
                  <p className="blog-card-excerpt">{post.excerpt}</p>
                  <div className="blog-card-footer">
                    <span className="blog-card-read-time">{post.readTime}</span>
                    <Link
                      href={`/blog/${post.slug}`}
                      className="blog-card-read-more"
                    >
                      Read Guide →
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Seasonal Posts Section */}
          <div className="blog-section-header">
            <h2 className="blog-section-title">Seasonal Highlights</h2>
            <p className="blog-section-subtitle">
              Perfect timing for your hibachi celebrations throughout the year
            </p>
          </div>

          <div className="blog-posts-grid seasonal-grid">
            {seasonalPosts.map((post) => (
              <article key={post.id} className="blog-card category-seasonal">
                <div className="blog-card-image">
                  <div className="blog-card-badges">
                    <div className="blog-card-badge">
                      {post.seasonal ? '🍂 SEASONAL' : post.category}
                    </div>
                  </div>
                </div>
                <div className="blog-card-content">
                  <h3 className="blog-card-title">
                    <Link href={`/blog/${post.slug}`}>
                      {post.title}
                    </Link>
                  </h3>
                  <p className="blog-card-excerpt">{post.excerpt}</p>
                  <div className="blog-card-footer">
                    <span className="blog-card-read-time">{post.readTime}</span>
                    <Link
                      href={`/blog/${post.slug}`}
                      className="blog-card-read-more"
                    >
                      Read →
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* All Recent Posts */}
          <div className="blog-section-header">
            <h2 className="blog-section-title">Latest Hibachi Articles</h2>
            <p className="blog-section-subtitle">
              Latest hibachi catering tips, local event guides, and seasonal menu updates
            </p>
          </div>

        <div className="blog-posts-grid">
          {allRecentPosts.map((post) => (
            <article key={post.id} className="blog-card category-recent">
              <div className="blog-card-image">
                <div className="blog-card-badges">
                  <div className="blog-card-badge">
                    {post.serviceArea}
                  </div>
                  <div className="blog-card-badge">
                    {post.eventType}
                  </div>
                </div>
              </div>
              <div className="blog-card-content">
                <div className="blog-card-meta">
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    <span className="mr-4">{post.date}</span>
                  </div>
                  <div className="flex items-center">
                    <User className="w-4 h-4 mr-1" />
                    <span>{post.author}</span>
                  </div>
                </div>
                <h3 className="blog-card-title">
                  <Link href={`/blog/${post.slug}`}>
                    {post.title}
                  </Link>
                </h3>
                <p className="blog-card-excerpt">{post.excerpt}</p>
                <div className="blog-card-footer">
                  <span className="blog-card-read-time">{post.readTime}</span>
                  <Link
                    href={`/blog/${post.slug}`}
                    className="blog-card-read-more"
                  >
                    Read More →
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>

        </div>

        {/* Newsletter Section */}
        <div className="blog-newsletter">
          <h3 className="blog-newsletter-title">
            Never Miss a Hibachi Tip or Local Event Idea
          </h3>
          <p className="blog-newsletter-description">
            Get exclusive hibachi party planning tips, seasonal menu updates, and local event inspiration delivered to your inbox.
            Perfect for Bay Area, Sacramento, San Jose and surrounding areas.
          </p>
          <div className="blog-newsletter-actions">
            <Link
              href="/contact"
              className="blog-btn blog-btn-primary"
            >
              Get Hibachi Updates
            </Link>
            <Link
              href="/booking"
              className="blog-btn blog-btn-secondary"
            >
              Book Event Now
            </Link>
          </div>
        </div>
      </div>

      <Assistant page="/blog" />
    </div>
  )
}
