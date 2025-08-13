import Link from 'next/link'
import { Calendar, User } from 'lucide-react'
// import { FreeQuoteButton } from '@/components/quote/FreeQuoteButton' // Removed floating button

export default function BlogPage() {
  const blogPosts = [
    {
      id: 1,
      title: 'The Art of Hibachi: More Than Just Cooking',
      excerpt: 'Discover the rich history and cultural significance behind hibachi cooking and why it makes for such an entertaining dining experience.',
      author: 'Chef Takeshi',
      date: 'January 20, 2025',
      readTime: '5 min read',
      slug: 'art-of-hibachi'
    },
    {
      id: 2,
      title: 'Planning the Perfect Hibachi Party',
      excerpt: 'Tips and tricks for hosting an unforgettable hibachi party in your backyard, from guest count to menu selection.',
      author: 'Sarah Chen',
      date: 'January 15, 2025',
      readTime: '7 min read',
      slug: 'planning-hibachi-party'
    },
    {
      id: 3,
      title: 'Seasonal Hibachi: Fresh Ingredients for Every Season',
      excerpt: 'Learn about how we adapt our menu throughout the year to incorporate the freshest seasonal ingredients.',
      author: 'Chef Maria',
      date: 'January 10, 2025',
      readTime: '4 min read',
      slug: 'seasonal-hibachi'
    },
    {
      id: 4,
      title: 'Corporate Events: Why Hibachi Catering Builds Team Spirit',
      excerpt: 'Explore how hibachi catering can transform your corporate events and strengthen team bonds through shared dining experiences.',
      author: 'David Kim',
      date: 'January 5, 2025',
      readTime: '6 min read',
      slug: 'corporate-hibachi'
    }
  ]

  return (
    <div className="py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">MyHibachi Blog</h1>
          <p className="text-gray-600">Stories, tips, and insights from the world of hibachi catering</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {blogPosts.map((post) => (
            <article key={post.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
              <div className="h-48 bg-gradient-to-br from-blue-500 to-purple-600"></div>
              <div className="p-6">
                <div className="flex items-center text-sm text-gray-500 mb-3">
                  <Calendar className="w-4 h-4 mr-1" />
                  <span className="mr-4">{post.date}</span>
                  <User className="w-4 h-4 mr-1" />
                  <span>{post.author}</span>
                </div>
                <h2 className="text-xl font-bold text-gray-900 mb-3">
                  <Link href={`/blog/${post.slug}`} className="hover:text-blue-600">
                    {post.title}
                  </Link>
                </h2>
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

        <div className="text-center mt-12">
          <p className="text-gray-600 mb-6">
            Want to stay updated with our latest posts and hibachi tips?
          </p>
          <a
            href="/contact"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Subscribe to Newsletter
          </a>
        </div>
      </div>
      
      {/* Floating Quote Button removed - users can get quotes from dedicated quote page */}
    </div>
  )
}
