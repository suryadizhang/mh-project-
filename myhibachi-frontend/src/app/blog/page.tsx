'use client'

import Link from 'next/link'
import { Calendar, User } from 'lucide-react'
import Assistant from '@/components/chat/Assistant'
import BlogSearch from '@/components/blog/BlogSearch'
import { getFeaturedPosts, getSeasonalPosts, getRecentPosts, getEventSpecificPosts } from '@/data/blogPosts'
import type { BlogPost } from '@/data/blogPosts'
import '@/styles/blog.css'

export default function BlogPage() {
  const featuredPosts = getFeaturedPosts()
  const seasonalPosts = getSeasonalPosts()
  const eventSpecificPosts = getEventSpecificPosts().slice(0, 6) // Get first 6 new event posts
  const allRecentPosts = getRecentPosts(12)
  const allPosts = [...featuredPosts, ...seasonalPosts, ...eventSpecificPosts, ...allRecentPosts]
  
  const handleFilteredPosts = (filtered: BlogPost[]) => {
    // TODO: Implement search results display
    console.log('Filtered posts:', filtered.length)
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
          <BlogSearch posts={allPosts} onFilteredPosts={handleFilteredPosts} />
        </div>
      </div>

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
