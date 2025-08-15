import { notFound } from 'next/navigation'
import Link from 'next/link'
import { Calendar, User, ArrowLeft, Share2 } from 'lucide-react'
import Assistant from '@/components/chat/Assistant'
import BlogStructuredData from '@/components/blog/BlogStructuredData'
import blogPosts from '@/data/blogPosts'
import { Metadata } from 'next'

interface BlogPostPageProps {
  params: {
    slug: string
  }
}

// Generate metadata for SEO
export async function generateMetadata(
  { params }: BlogPostPageProps
): Promise<Metadata> {
  const post = blogPosts.find(p => p.slug === params.slug)

  if (!post) {
    return {
      title: 'Blog Post Not Found'
    }
  }

  return {
    title: `${post.title} | My Hibachi Blog`,
    description: post.metaDescription,
    keywords: post.keywords.join(', '),
    openGraph: {
      title: post.title,
      description: post.metaDescription,
      type: 'article',
      authors: [post.author],
      publishedTime: new Date(post.date).toISOString(),
    },
    twitter: {
      card: 'summary_large_image',
      title: post.title,
      description: post.metaDescription,
    }
  }
}

// Generate static params for all blog posts
export async function generateStaticParams() {
  return blogPosts.map((post) => ({
    slug: post.slug,
  }))
}

export default function BlogPostPage({ params }: BlogPostPageProps) {
  const post = blogPosts.find(p => p.slug === params.slug)

  if (!post) {
    notFound()
  }

  // Generate full article content based on the post data
  const generateFullContent = (post: typeof blogPosts[0]) => {
    const sections = []

    // Introduction
    sections.push(`
      <p class="text-lg text-gray-700 mb-6 leading-relaxed">
        ${post.excerpt}
      </p>
    `)

    // Service Area Specific Content
    if (post.serviceArea && post.serviceArea !== 'All Areas') {
      sections.push(`
        <h2 class="text-2xl font-bold text-gray-900 mb-4">Why Choose Hibachi Catering in ${post.serviceArea}?</h2>
        <p class="text-gray-700 mb-6 leading-relaxed">
          ${post.serviceArea} offers the perfect backdrop for hibachi catering events. Our professional chefs bring restaurant-quality
          equipment and fresh ingredients directly to your location, creating an unforgettable dining experience for you and your guests.
        </p>
        <ul class="list-disc pl-6 mb-6 text-gray-700">
          <li class="mb-2">Professional mobile hibachi setup with premium equipment</li>
          <li class="mb-2">Fresh, locally-sourced ingredients when possible</li>
          <li class="mb-2">Interactive cooking show entertainment for all ages</li>
          <li class="mb-2">Customizable menu options for dietary preferences</li>
        </ul>
      `)
    }

    // Event Type Specific Content
    if (post.eventType && post.eventType !== 'General') {
      sections.push(`
        <h2 class="text-2xl font-bold text-gray-900 mb-4">Perfect for ${post.eventType} Celebrations</h2>
        <p class="text-gray-700 mb-6 leading-relaxed">
          ${post.eventType.toLowerCase()} events become extraordinary with hibachi catering. The interactive cooking show
          creates lasting memories while providing delicious, fresh-cooked meals that please every palate.
        </p>
      `)
    }

    // Seasonal content if applicable
    if (post.seasonal) {
      sections.push(`
        <h2 class="text-2xl font-bold text-gray-900 mb-4">Seasonal Menu Highlights</h2>
        <p class="text-gray-700 mb-6 leading-relaxed">
          Our seasonal menu incorporates the freshest ingredients available during this time of year. From premium seafood
          to perfectly grilled meats and fresh vegetables, every dish is prepared with attention to quality and flavor.
        </p>
      `)
    }

    // Planning tips
    sections.push(`
      <h2 class="text-2xl font-bold text-gray-900 mb-4">Planning Your Hibachi Event</h2>
      <div class="bg-orange-50 border-l-4 border-orange-400 p-6 mb-6">
        <h3 class="text-lg font-semibold text-orange-800 mb-3">Quick Planning Checklist:</h3>
        <ul class="list-disc pl-6 text-orange-700">
          <li class="mb-2">Guest count and dietary restrictions</li>
          <li class="mb-2">Outdoor space with access to power (if needed)</li>
          <li class="mb-2">Tables and chairs for guests</li>
          <li class="mb-2">Date and time preferences</li>
          <li class="mb-2">Special requests or menu customizations</li>
        </ul>
      </div>
    `)

    // Call to action
    sections.push(`
      <h2 class="text-2xl font-bold text-gray-900 mb-4">Ready to Book Your Event?</h2>
      <p class="text-gray-700 mb-6 leading-relaxed">
        Experience the excitement of professional hibachi catering at your next event. Our team handles all the cooking and equipment setup, so you can focus on enjoying time with your guests.
      </p>
      <p class="text-gray-700 mb-6 leading-relaxed">
        <a href="/menu" class="text-blue-600 hover:text-blue-800 font-medium underline">View our complete hibachi menu</a>
        to see all the delicious options available for your celebration.
      </p>
      <div class="bg-gradient-to-r from-orange-500 to-red-600 rounded-lg p-6 text-white mb-6">
        <h3 class="text-xl font-bold mb-3">Get Your Free Quote Today</h3>
        <p class="mb-4">Professional hibachi catering with premium ingredients and entertainment included.</p>
        <div class="flex flex-col sm:flex-row gap-4">
          <a href="/booking" class="bg-white text-orange-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors text-center">
            Book Now
          </a>
          <a href="/contact" class="border border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white hover:text-orange-600 transition-colors text-center">
            Ask Questions
          </a>
        </div>
      </div>
    `)

    return sections.join('')
  }

  const fullContent = generateFullContent(post)

  return (
    <div className="min-h-screen bg-gray-50">
      <BlogStructuredData post={post} />

      {/* Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Link
            href="/blog"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Blog
          </Link>
        </div>
      </div>

      {/* Article Header */}
      <article className="max-w-4xl mx-auto px-4 py-12">
        <header className="mb-8">
          <div className="flex flex-wrap gap-2 mb-4">
            <span className="bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full">
              {post.category}
            </span>
            <span className="bg-green-100 text-green-800 text-sm px-3 py-1 rounded-full">
              {post.serviceArea}
            </span>
            <span className="bg-purple-100 text-purple-800 text-sm px-3 py-1 rounded-full">
              {post.eventType}
            </span>
          </div>

          <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-6 leading-tight">
            {post.title}
          </h1>

          <div className="flex items-center justify-between flex-wrap gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-6">
              <div className="flex items-center">
                <Calendar className="w-4 h-4 mr-2" />
                <span>{post.date}</span>
              </div>
              <div className="flex items-center">
                <User className="w-4 h-4 mr-2" />
                <span>{post.author}</span>
              </div>
              <span>{post.readTime}</span>
            </div>
            <button className="flex items-center text-blue-600 hover:text-blue-800">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </button>
          </div>
        </header>

        {/* Article Content */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-8">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{ __html: fullContent }}
          />
        </div>

        {/* Related Keywords */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tags</h3>
          <div className="flex flex-wrap gap-2">
            {post.keywords.map((keyword, index) => (
              <span
                key={index}
                className="bg-gray-100 text-gray-700 text-sm px-3 py-1 rounded-full"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      </article>

      <Assistant page={`/blog/${post.slug}`} />
    </div>
  )
}
