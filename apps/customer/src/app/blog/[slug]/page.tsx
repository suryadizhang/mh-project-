import { ArrowLeft, Calendar, Share2, User } from 'lucide-react';
import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import BlogStructuredData from '@/components/blog/BlogStructuredData';
import Assistant from '@/components/chat/Assistant';
import { BreadcrumbSchema, LocalBusinessSchema } from '@/components/seo/TechnicalSEO';
import blogPosts, { getPostsByEventType, getPostsByServiceArea, type BlogPost } from '@/data/blogPosts';

interface BlogPostPageProps {
  params: Promise<{ slug: string }>;
}

// Generate metadata for SEO
export async function generateMetadata({ params }: BlogPostPageProps): Promise<Metadata> {
  const { slug } = await params;
  const post = blogPosts.find((p: BlogPost) => p.slug === slug);

  if (!post) {
    return {
      title: 'Blog Post Not Found',
    };
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
    },
  };
}

// Generate static params for all blog posts
export async function generateStaticParams() {
  return blogPosts.map((post: BlogPost) => ({
    slug: post.slug,
  }));
}

export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const { slug } = await params;
  const post = blogPosts.find((p: BlogPost) => p.slug === slug);

  if (!post) {
    notFound();
  }

  // Get related posts based on event type and service area
  const relatedByEvent = getPostsByEventType(post.eventType)
    .filter((p: BlogPost) => p.id !== post.id)
    .slice(0, 2);

  const relatedByArea = getPostsByServiceArea(post.serviceArea)
    .filter((p: BlogPost) => p.id !== post.id && !relatedByEvent.includes(p))
    .slice(0, 1);

  const relatedPosts = [...relatedByEvent, ...relatedByArea].slice(0, 3);

  // Generate full article content based on the post data
  const generateFullContent = (post: BlogPost) => {
    const sections = [];

    // Introduction
    sections.push(`
      <p class="text-lg text-gray-700 mb-6 leading-relaxed">
        ${post.excerpt}
      </p>
    `);

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
      `);
    }

    // Event Type Specific Content
    if (post.eventType && post.eventType !== 'General') {
      sections.push(`
        <h2 class="text-2xl font-bold text-gray-900 mb-4">Perfect for ${
          post.eventType
        } Celebrations</h2>
        <p class="text-gray-700 mb-6 leading-relaxed">
          ${post.eventType.toLowerCase()} events become extraordinary with hibachi catering. The interactive cooking show
          creates lasting memories while providing delicious, fresh-cooked meals that please every palate.
        </p>
      `);
    }

    // Seasonal content if applicable
    if (post.seasonal) {
      sections.push(`
        <h2 class="text-2xl font-bold text-gray-900 mb-4">Seasonal Menu Highlights</h2>
        <p class="text-gray-700 mb-6 leading-relaxed">
          Our seasonal menu incorporates the freshest ingredients available during this time of year. From premium seafood
          to perfectly grilled meats and fresh vegetables, every dish is prepared with attention to quality and flavor.
        </p>
      `);
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
    `);

    // Call to action with internal links
    sections.push(`
      <h2 class="text-2xl font-bold text-gray-900 mb-4">Ready to Book Your Event?</h2>
      <p class="text-gray-700 mb-6 leading-relaxed">
        Experience the excitement of professional hibachi catering at your next event. Our team handles all the cooking and equipment setup, so you can focus on enjoying time with your guests.
      </p>
      <p class="text-gray-700 mb-6 leading-relaxed">
        <a href="/menu" class="text-blue-600 hover:text-blue-800 font-medium underline">View our complete hibachi menu</a>
        to see all the delicious options available for your celebration, or explore our
        <a href="/blog" class="text-blue-600 hover:text-blue-800 font-medium underline">other catering guides</a>
        for more event inspiration.
      </p>
      <div class="bg-gradient-to-r from-orange-500 to-red-600 rounded-lg p-6 text-white mb-6">
        <h3 class="text-xl font-bold mb-3">Get Your Free Quote Today</h3>
        <p class="mb-4">Professional hibachi catering with premium ingredients and entertainment included.</p>
        <div class="flex flex-col sm:flex-row gap-4">
          <a href="/BookUs" class="bg-white text-orange-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors text-center">
            Book Now
          </a>
          <a href="/contact" class="border border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white hover:text-orange-600 transition-colors text-center">
            Ask Questions
          </a>
        </div>
      </div>
    `);

    return sections.join('');
  };

  const fullContent = generateFullContent(post);

  return (
    <div className="min-h-screen bg-gray-50">
      <BlogStructuredData post={post} />

      {/* Enhanced SEO Schema Markup */}
      <BreadcrumbSchema
        items={[
          { name: 'Home', url: '/' },
          { name: 'Blog', url: '/blog' },
          { name: post.title, url: `/blog/${post.slug}` },
        ]}
      />

      {post.serviceArea && post.serviceArea !== 'All Areas' && (
        <LocalBusinessSchema
          location={post.serviceArea}
          eventType={post.eventType}
          description={post.metaDescription}
          url={`https://myhibachi.com/blog/${post.slug}`}
        />
      )}

      {/* Navigation */}
      <div className="border-b bg-white">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <Link
            href="/blog"
            className="inline-flex items-center font-medium text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Blog
          </Link>
        </div>
      </div>

      {/* Article Header */}
      <article className="mx-auto max-w-4xl px-4 py-12">
        <header className="mb-8">
          <div className="mb-4 flex flex-wrap gap-2">
            <span className="rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800">
              {post.category}
            </span>
            <span className="rounded-full bg-green-100 px-3 py-1 text-sm text-green-800">
              {post.serviceArea}
            </span>
            <span className="rounded-full bg-purple-100 px-3 py-1 text-sm text-purple-800">
              {post.eventType}
            </span>
          </div>

          <h1 className="mb-6 text-4xl leading-tight font-bold text-gray-900 lg:text-5xl">
            {post.title}
          </h1>

          <div className="flex flex-wrap items-center justify-between gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-6">
              <div className="flex items-center">
                <Calendar className="mr-2 h-4 w-4" />
                <span>{post.date}</span>
              </div>
              <div className="flex items-center">
                <User className="mr-2 h-4 w-4" />
                <span>{post.author}</span>
              </div>
              <span>{post.readTime}</span>
            </div>
            <button className="flex items-center text-blue-600 hover:text-blue-800">
              <Share2 className="mr-2 h-4 w-4" />
              Share
            </button>
          </div>
        </header>

        {/* Article Content */}
        <div className="mb-8 rounded-lg bg-white p-8 shadow-sm">
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{ __html: fullContent }}
          />
        </div>

        {/* Related Keywords */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Tags</h3>
          <div className="flex flex-wrap gap-2">
            {post.keywords.map((keyword: string, index: number) => (
              <span
                key={index}
                className="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-700"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>

        {/* Related Posts */}
        {relatedPosts.length > 0 && (
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Related Hibachi Catering Guides
            </h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {relatedPosts.map((relatedPost) => (
                <Link key={relatedPost.id} href={`/blog/${relatedPost.slug}`} className="block">
                  <article className="cursor-pointer rounded-lg border border-gray-200 p-4 transition-shadow hover:shadow-md">
                    <div className="mb-2">
                      <span className="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800">
                        {relatedPost.eventType}
                      </span>
                    </div>
                    <h4 className="mb-2 font-semibold text-gray-900 hover:text-blue-600">
                      {relatedPost.title}
                    </h4>
                    <p className="mb-3 text-sm text-gray-600">
                      {relatedPost.excerpt.slice(0, 100)}...
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">{relatedPost.readTime}</span>
                      <span className="text-sm font-medium text-blue-600 hover:text-blue-800">
                        Read →
                      </span>
                    </div>
                  </article>
                </Link>
              ))}
            </div>
          </div>
        )}
      </article>

      <Assistant page={`/blog/${post.slug}`} />
    </div>
  );
}
