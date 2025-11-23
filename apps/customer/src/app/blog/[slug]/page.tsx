import type { BlogPost } from '@my-hibachi/blog-types';
import { ArrowLeft, Calendar, Share2, User } from 'lucide-react';
import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import BlogStructuredData from '@/components/blog/BlogStructuredData';
import Assistant from '@/components/chat/Assistant';
import { blogService } from '@/lib/blog/blogService';
import { BreadcrumbSchema, LocalBusinessSchema } from '@/components/seo/TechnicalSEO';

interface BlogPostPageProps {
  params: Promise<{ slug: string }>;
}

// Generate metadata for SEO
export async function generateMetadata({ params }: BlogPostPageProps): Promise<Metadata> {
  const { slug } = await params;
  const post = await blogService.getPostBySlug(slug);

  if (!post) {
    return {
      title: 'Blog Post Not Found',
    };
  }

  const authorName = typeof post.author === 'string' ? post.author : post.author?.name || 'My Hibachi Team';

  return {
    title: `${post.title} | My Hibachi Blog`,
    description: post.metaDescription,
    keywords: post.keywords.join(', '),
    openGraph: {
      title: post.title,
      description: post.metaDescription,
      type: 'article',
      authors: [authorName],
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
  const posts = await blogService.getAllPosts();
  return posts.map((post: BlogPost) => ({
    slug: post.slug,
  }));
}

export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const { slug } = await params;
  const post = await blogService.getPostBySlug(slug);

  if (!post) {
    notFound();
  }

  // Get related posts based on event type and service area
  const relatedByEvent = (await blogService.getPostsByEventType(post.eventType))
    .filter((p: BlogPost) => p.id !== post.id)
    .slice(0, 2);

  const relatedByArea = (await blogService.getPostsByServiceArea(post.serviceArea))
    .filter((p: BlogPost) => p.id !== post.id && !relatedByEvent.includes(p))
    .slice(0, 1);

  const relatedPosts = [...relatedByEvent, ...relatedByArea].slice(0, 3);

  // Use actual MDX content from the post
  // Convert markdown to HTML for display
  const formatContent = (content: string) => {
    // Convert markdown to HTML
    const html = content
      .replace(/^### (.*$)/gim, '<h3 class="text-xl font-semibold text-gray-900 mb-3 mt-6">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-2xl font-bold text-gray-900 mb-4 mt-8">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-3xl font-bold text-gray-900 mb-6 mt-8">$1</h1>')
      // Convert bold
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
      // Convert italic
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Convert links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:text-blue-800 underline">$1</a>')
      // Convert unordered lists
      .replace(/^\- (.*$)/gim, '<li class="mb-2">$1</li>')
      // Convert blockquotes (testimonials)
      .replace(/^_"(.*)"_ - (.*)$/gim, '<blockquote class="border-l-4 border-orange-400 pl-4 italic text-gray-700 my-6">"$1" <footer class="mt-2 text-sm text-gray-600">— $2</footer></blockquote>')
      // Wrap paragraphs
      .split('\n\n')
      .map(para => {
        if (para.trim() && !para.startsWith('<h') && !para.startsWith('<li') && !para.startsWith('<blockquote')) {
          return `<p class="text-gray-700 mb-6 leading-relaxed">${para}</p>`;
        }
        return para;
      })
      .join('\n');

    return html;
  };

  const fullContent = post.content && post.content !== 'No content available'
    ? formatContent(post.content)
    : `<p class="text-lg text-gray-700 mb-6 leading-relaxed">${post.excerpt}</p><p class="text-gray-700">Full article content coming soon. Please check back later!</p>`;

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
                <span>{typeof post.author === 'string' ? post.author : post.author?.name || 'My Hibachi Team'}</span>
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
