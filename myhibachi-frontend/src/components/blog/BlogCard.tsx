'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Calendar, User, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import type { BlogPost } from '@/data/blogPosts'

interface BlogCardProps {
  post: BlogPost
  category: 'featured' | 'seasonal' | 'event' | 'recent'
}

export default function BlogCard({ post, category }: BlogCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const categoryStyles = {
    featured: 'category-featured',
    seasonal: 'category-seasonal',
    event: 'category-event',
    recent: 'category-recent'
  }

  return (
    <article className={`blog-card ${categoryStyles[category]}`}>
      <div className="blog-card-image">
        <div className="blog-card-badges">
          <div className="blog-card-badge">
            {post.serviceArea} • {post.eventType}
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
            <span className="mr-4">{post.author}</span>
          </div>
          <div className="flex items-center">
            <Clock className="w-4 h-4 mr-1" />
            <span>{post.readTime}</span>
          </div>
        </div>

        <h3 className="blog-card-title">
          <Link href={`/blog/${post.slug}`}>{post.title}</Link>
        </h3>

        <div className="blog-card-excerpt-wrapper">
          <p className={`blog-card-excerpt ${isExpanded ? 'expanded' : ''}`}>
            {post.excerpt}
            {post.content && isExpanded && (
              <span className="blog-card-preview">{post.content.substring(0, 200)}...</span>
            )}
          </p>

          {post.content && post.content.length > 200 && (
            <button onClick={() => setIsExpanded(!isExpanded)} className="blog-card-expand">
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Show Less
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Preview
                </>
              )}
            </button>
          )}
        </div>

        {/* Tags */}
        {post.keywords && post.keywords.length > 0 && (
          <div className="blog-card-tags">
            {post.keywords.slice(0, 3).map((tag, index) => (
              <span key={index} className="blog-card-tag">
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="blog-card-footer">
          <div className="blog-card-stats">
            <span className="blog-card-read-time">{post.readTime}</span>
            {post.featured && <span className="blog-card-featured-badge">⭐ Featured</span>}
          </div>
          <Link href={`/blog/${post.slug}`} className="blog-card-read-more">
            Read Guide →
          </Link>
        </div>
      </div>
    </article>
  )
}
