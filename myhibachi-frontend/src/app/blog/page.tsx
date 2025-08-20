import Link from 'next/link'
import { Calendar, User } from 'lucide-react'
import Assistant from '@/components/chat/Assistant'
import { getFeaturedPosts, getSeasonalPosts, getRecentPosts, getEventSpecificPosts } from '@/data/blogPosts'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'My Hibachi Blog | Event Catering Guides for Bay Area, Sacramento & San Jose',
  description: 'Complete hibachi catering guides for every event: birthdays, weddings, corporate events, pool parties, and more. Expert tips for Bay Area, Sacramento, San Jose celebrations.',
  keywords: 'hibachi blog, bay area catering, sacramento hibachi, san jose events, hibachi tips, party planning, seasonal menus, mobile hibachi chef, event catering guides, birthday hibachi, wedding hibachi, corporate hibachi',
  openGraph: {
    title: 'My Hibachi Blog | Event Catering Guides for Bay Area, Sacramento & San Jose',
    description: 'Complete hibachi catering guides for every event: birthdays, weddings, corporate events, pool parties, and more.',
    type: 'website'
  }
}

export default function BlogPage() {
  const featuredPosts = getFeaturedPosts()
  const seasonalPosts = getSeasonalPosts()
  const eventSpecificPosts = getEventSpecificPosts().slice(0, 6) // Get first 6 new event posts
  const allRecentPosts = getRecentPosts(12)

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
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">Event-Specific Hibachi Guides</h2>
            <p className="text-lg text-gray-600 text-center max-w-3xl mx-auto mb-8">
              Complete hibachi catering guides for every type of celebration and event
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {eventSpecificPosts.map((post) => (
              <article key={post.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                <div className="h-40 bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <div className="text-white text-center p-4">
                    <div className="text-sm font-medium bg-black bg-opacity-30 rounded px-2 py-1 mb-2">
                      🎉 {post.eventType}
                    </div>
                    <div className="text-xs bg-black bg-opacity-30 rounded px-2 py-1">
                      📍 {post.serviceArea}
                    </div>
                  </div>
                </div>
                <div className="p-5">
                  <div className="flex items-center text-sm text-gray-500 mb-3">
                    <Calendar className="w-4 h-4 mr-1" />
                    <span className="mr-4">{post.date}</span>
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">NEW</span>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 mb-3">
                    <Link href={`/blog/${post.slug}`} className="hover:text-blue-600">
                      {post.title}
                    </Link>
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">{post.excerpt}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">{post.readTime}</span>
                    <Link
                      href={`/blog/${post.slug}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Read Guide →
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Seasonal Posts Section */}
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">Seasonal Highlights</h2>
            <p className="text-lg text-gray-600 text-center max-w-3xl mx-auto">
              Perfect timing for your hibachi celebrations throughout the year
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {seasonalPosts.map((post) => (
              <article key={post.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                <div className="h-32 bg-gradient-to-br from-green-500 to-blue-600 flex items-center justify-center">
                  <div className="text-white text-center">
                    <div className="text-xs font-medium bg-black bg-opacity-30 rounded px-2 py-1">
                      {post.seasonal ? '🍂 SEASONAL' : post.category}
                    </div>
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    <Link href={`/blog/${post.slug}`} className="hover:text-blue-600">
                      {post.title}
                    </Link>
                  </h3>
                  <p className="text-gray-600 text-sm mb-3">{post.excerpt}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">{post.readTime}</span>
                    <Link
                      href={`/blog/${post.slug}`}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      Read →
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* All Recent Posts */}
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">Latest Hibachi Articles</h2>
            <p className="text-lg text-gray-600 text-center max-w-3xl mx-auto">
              Latest hibachi catering tips, local event guides, and seasonal menu updates
            </p>
          </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {allRecentPosts.map((post) => (
            <article key={post.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
              <div className="h-48 bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                <div className="text-white text-center p-4">
                  <div className="text-sm font-medium bg-black bg-opacity-30 rounded px-2 py-1 mb-1">
                    {post.serviceArea}
                  </div>
                  <div className="text-xs bg-black bg-opacity-30 rounded px-2 py-1">
                    {post.eventType}
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

        </div>

        {/* Newsletter Section */}
        <div className="text-center mt-16 bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            Never Miss a Hibachi Tip or Local Event Idea
          </h3>
          <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
            Get exclusive hibachi party planning tips, seasonal menu updates, and local event inspiration delivered to your inbox.
            Perfect for Bay Area, Sacramento, San Jose and surrounding areas.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center max-w-md mx-auto">
            <Link
              href="/contact"
              className="inline-flex items-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 transition-colors"
            >
              Get Hibachi Updates
            </Link>
            <Link
              href="/booking"
              className="inline-flex items-center px-8 py-3 border-2 border-orange-600 text-base font-medium rounded-md text-orange-600 bg-white hover:bg-orange-50 transition-colors"
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
