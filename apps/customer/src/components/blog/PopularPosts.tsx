'use client'

import type { BlogPost } from '@my-hibachi/blog-types';
import { Calendar, Eye, Star, TrendingUp } from 'lucide-react'
import Link from 'next/link'
import React from 'react'

import BlogCardImage from './BlogCardImage'

interface PopularPostsProps {
  posts: BlogPost[]
  maxPosts?: number
  timeframe?: 'week' | 'month' | 'year' | 'all'
  className?: string
}

export default function PopularPosts({
  posts,
  maxPosts = 5,
  timeframe = 'all',
  className = ''
}: PopularPostsProps) {
  // Simulate popularity metrics (in a real app, this would come from analytics)
  const getPopularityScore = (post: BlogPost): number => {
    let score = 0

    // Featured posts get higher score
    if (post.featured) score += 50

    // Recent posts get bonus points
    const postDate = new Date(post.date)
    const now = new Date()
    const daysSincePost = (now.getTime() - postDate.getTime()) / (1000 * 60 * 60 * 24)

    // Apply timeframe filter
    switch (timeframe) {
      case 'week':
        if (daysSincePost > 7) return 0
        break
      case 'month':
        if (daysSincePost > 30) return 0
        break
      case 'year':
        if (daysSincePost > 365) return 0
        break
    }

    // Recent posts get higher scores (decay over time)
    if (daysSincePost < 7) score += 30
    else if (daysSincePost < 30) score += 20
    else if (daysSincePost < 90) score += 10

    // Keyword density (more keywords = more searchable)
    score += (post.keywords?.length || 0) * 2

    // Longer content might be more comprehensive
    const contentLength = post.content?.length || post.excerpt.length
    if (contentLength > 1000) score += 15
    else if (contentLength > 500) score += 10
    else if (contentLength > 200) score += 5

    // Event-specific posts might be more popular
    if (post.eventType && post.eventType !== 'General') score += 10

    // Local area posts might be more relevant
    if (post.serviceArea && post.serviceArea !== 'All Areas') score += 8

    // Add deterministic variance based on post ID to simulate engagement
    const postId = typeof post.id === 'number' ? post.id : parseInt(String(post.id), 10) || 0
    score += postId % 20

    return score
  }

  const popularPosts = posts
    .map(post => ({
      post,
      score: getPopularityScore(post)
    }))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, maxPosts)
    .map(item => item.post)

  const getTimeframeLabel = () => {
    switch (timeframe) {
      case 'week':
        return 'This Week'
      case 'month':
        return 'This Month'
      case 'year':
        return 'This Year'
      default:
        return 'All Time'
    }
  }

  if (popularPosts.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <TrendingUp className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Popular Posts</h3>
        </div>
        <p className="text-gray-500 text-sm">No popular posts for this timeframe.</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Popular Posts</h3>
          </div>
          <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {getTimeframeLabel()}
          </span>
        </div>

        <div className="space-y-4">
          {popularPosts.map((post, index) => (
            <article key={post.id} className="group">
              <div className="flex gap-3">
                {/* Rank Number */}
                <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-bold">
                  {index + 1}
                </div>

                {/* Thumbnail */}
                <div className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden">
                  <BlogCardImage
                    post={post}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-semibold text-gray-900 mb-1 line-clamp-2">
                    <Link
                      href={`/blog/${post.slug}`}
                      className="hover:text-blue-600 transition-colors"
                    >
                      {post.title}
                    </Link>
                  </h4>

                  <div className="flex items-center text-xs text-gray-500 mb-2">
                    <Calendar className="w-3 h-3 mr-1" />
                    <span>{post.date}</span>
                    {post.featured && (
                      <>
                        <span className="mx-1">•</span>
                        <Star className="w-3 h-3 mr-1 text-yellow-500" />
                        <span>Featured</span>
                      </>
                    )}
                  </div>

                  {/* Engagement Metrics (simulated) */}
                  <div className="flex items-center space-x-3 text-xs text-gray-400">
                    <div className="flex items-center">
                      <Eye className="w-3 h-3 mr-1" />
                      <span>{((Number(post.id) * 37) % 900) + 100}</span>
                    </div>
                    <div className="flex items-center">
                      <TrendingUp className="w-3 h-3 mr-1" />
                      <span className="text-green-600">+{((Number(post.id) * 23) % 40) + 10}%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Categories/Tags */}
              <div className="mt-2 ml-11 flex flex-wrap gap-1">
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  {post.category}
                </span>
                {post.serviceArea && (
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                    {post.serviceArea}
                  </span>
                )}
              </div>

              {/* Separator (except for last item) */}
              {index < popularPosts.length - 1 && <hr className="my-4 border-gray-100" />}
            </article>
          ))}
        </div>

        {/* View All Link */}
        <div className="mt-6 pt-4 border-t border-gray-200 text-center">
          <Link href="/blog" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All Popular Posts →
          </Link>
        </div>
      </div>
    </div>
  )
}
