'use client'

import React from 'react'
import Link from 'next/link'
import { blogPosts } from '@/data/blogPosts'

interface TrendingPost {
  id: number
  title: string
  slug: string
  category: string
  publishedAt: string
  readingTime: number
  views: number
  trend: 'up' | 'down' | 'stable'
  trendPercentage: number
}

interface TrendingPostsProps {
  timeframe?: 'week' | 'month' | 'all'
  maxPosts?: number
  showTrend?: boolean
  compact?: boolean
}

const TrendingPosts: React.FC<TrendingPostsProps> = ({
  timeframe = 'week',
  maxPosts = 5,
  showTrend = true,
  compact = false
}) => {
  // Generate trending data based on post ID for consistency
  const generateTrendingData = (posts: typeof blogPosts): TrendingPost[] => {
    return posts.map(post => {
      const baseViews = ((post.id * 47) % 1000) + 500 // 500-1500 base views
      const timeMultiplier = timeframe === 'week' ? 0.3 : timeframe === 'month' ? 0.7 : 1
      const views = Math.floor(baseViews * timeMultiplier)

      // Deterministic trend calculation
      const trendSeed = (post.id * 23) % 100
      const trend: 'up' | 'down' | 'stable' =
        trendSeed > 70 ? 'up' : trendSeed < 30 ? 'down' : 'stable'

      const trendPercentage = ((post.id * 13) % 50) + 5 // 5-55% change

      // Extract reading time number from string like "6 min read"
      const readingTimeMatch = post.readTime.match(/\d+/)
      const readingTime = readingTimeMatch ? parseInt(readingTimeMatch[0]) : 5

      return {
        id: post.id,
        title: post.title,
        slug: post.slug,
        category: post.category,
        publishedAt: post.date,
        readingTime,
        views,
        trend,
        trendPercentage
      }
    })
  }

  const trendingPosts = generateTrendingData(blogPosts)
    .sort((a, b) => b.views - a.views)
    .slice(0, maxPosts)

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return (
          <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )
      case 'down':
        return (
          <svg className="w-3 h-3 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )
      case 'stable':
        return (
          <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
              clipRule="evenodd"
            />
          </svg>
        )
    }
  }

  const getTimeframeLabel = () => {
    switch (timeframe) {
      case 'week':
        return 'This Week'
      case 'month':
        return 'This Month'
      case 'all':
        return 'All Time'
    }
  }

  if (compact) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-900">Trending Now</h3>
          <span className="text-xs text-slate-500">{getTimeframeLabel()}</span>
        </div>

        <div className="space-y-2">
          {trendingPosts.map((post, index) => (
            <div key={post.id} className="flex items-center space-x-2">
              <span className="flex-shrink-0 w-5 h-5 bg-slate-100 text-slate-600 rounded-full flex items-center justify-center text-xs font-medium">
                {index + 1}
              </span>
              <Link
                href={`/blog/${post.slug}`}
                className="flex-1 text-xs text-slate-700 hover:text-slate-900 line-clamp-2 transition-colors"
              >
                {post.title}
              </Link>
              {showTrend && (
                <div className="flex items-center space-x-1">
                  {getTrendIcon(post.trend)}
                  <span
                    className={`text-xs ${
                      post.trend === 'up'
                        ? 'text-emerald-600'
                        : post.trend === 'down'
                          ? 'text-red-600'
                          : 'text-slate-400'
                    }`}
                  >
                    {post.trendPercentage}%
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>

        <Link
          href="/blog"
          className="block mt-3 text-xs text-slate-600 hover:text-slate-900 font-medium transition-colors"
        >
          View All Posts →
        </Link>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-slate-900">Trending Posts</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-slate-500">{getTimeframeLabel()}</span>
          <div className="flex items-center space-x-1 bg-slate-100 rounded-lg p-1">
            <button
              className={`px-2 py-1 text-xs rounded ${timeframe === 'week' ? 'bg-white shadow-sm' : ''}`}
            >
              Week
            </button>
            <button
              className={`px-2 py-1 text-xs rounded ${timeframe === 'month' ? 'bg-white shadow-sm' : ''}`}
            >
              Month
            </button>
            <button
              className={`px-2 py-1 text-xs rounded ${timeframe === 'all' ? 'bg-white shadow-sm' : ''}`}
            >
              All
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {trendingPosts.map((post, index) => (
          <div
            key={post.id}
            className="flex items-center space-x-4 p-3 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <div className="flex-shrink-0">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  index === 0
                    ? 'bg-amber-100 text-amber-800'
                    : index === 1
                      ? 'bg-slate-100 text-slate-700'
                      : index === 2
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-blue-100 text-blue-700'
                }`}
              >
                {index + 1}
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <Link href={`/blog/${post.slug}`} className="block group">
                <h3 className="text-sm font-medium text-slate-900 group-hover:text-slate-700 line-clamp-2 transition-colors">
                  {post.title}
                </h3>
                <div className="flex items-center space-x-3 mt-1">
                  <span className="text-xs text-slate-500">{post.category}</span>
                  <span className="text-xs text-slate-400">•</span>
                  <span className="text-xs text-slate-500">{post.readingTime} min read</span>
                  <span className="text-xs text-slate-400">•</span>
                  <span className="text-xs text-slate-500">
                    {post.views.toLocaleString()} views
                  </span>
                </div>
              </Link>
            </div>

            {showTrend && (
              <div className="flex-shrink-0 flex items-center space-x-2">
                <div className="flex items-center space-x-1">
                  {getTrendIcon(post.trend)}
                  <span
                    className={`text-sm font-medium ${
                      post.trend === 'up'
                        ? 'text-emerald-600'
                        : post.trend === 'down'
                          ? 'text-red-600'
                          : 'text-slate-400'
                    }`}
                  >
                    {post.trendPercentage}%
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-200">
        <Link
          href="/blog"
          className="inline-flex items-center text-sm text-slate-600 hover:text-slate-900 font-medium transition-colors"
        >
          View All Blog Posts
          <svg className="ml-1 w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </Link>
      </div>
    </div>
  )
}

export default TrendingPosts
