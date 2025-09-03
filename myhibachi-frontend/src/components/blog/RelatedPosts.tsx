'use client'

import React from 'react'
import Link from 'next/link'
import { Calendar, User, ArrowRight } from 'lucide-react'
import { BlogPost } from '@/data/blogPosts'
import BlogCardImage from './BlogCardImage'

interface RelatedPostsProps {
  currentPost: BlogPost
  allPosts: BlogPost[]
  maxPosts?: number
}

export default function RelatedPosts({ currentPost, allPosts, maxPosts = 3 }: RelatedPostsProps) {
  const getRelatedPosts = (): BlogPost[] => {
    // Filter out the current post
    const otherPosts = allPosts.filter(post => post.id !== currentPost.id)

    // Score posts based on relevance
    const scoredPosts = otherPosts.map(post => {
      let score = 0

      // Same category gets highest score
      if (post.category === currentPost.category) {
        score += 10
      }

      // Same service area gets high score
      if (post.serviceArea === currentPost.serviceArea) {
        score += 8
      }

      // Same event type gets high score
      if (post.eventType === currentPost.eventType) {
        score += 7
      }

      // Shared keywords/tags
      const currentKeywords = currentPost.keywords || []
      const postKeywords = post.keywords || []
      const sharedKeywords = currentKeywords.filter(keyword => postKeywords.includes(keyword))
      score += sharedKeywords.length * 2

      // Same author gets moderate score
      if (post.author === currentPost.author) {
        score += 3
      }

      // Recent posts get slight bonus (within 30 days)
      const postDate = new Date(post.date)
      const currentPostDate = new Date(currentPost.date)
      const daysDiff = Math.abs(
        (postDate.getTime() - currentPostDate.getTime()) / (1000 * 60 * 60 * 24)
      )
      if (daysDiff <= 30) {
        score += 1
      }

      return { post, score }
    })

    // Sort by score and return top posts
    return scoredPosts
      .sort((a, b) => b.score - a.score)
      .slice(0, maxPosts)
      .map(item => item.post)
  }

  const relatedPosts = getRelatedPosts()

  if (relatedPosts.length === 0) {
    return null
  }

  return (
    <div className="bg-gray-50 rounded-lg p-6 mt-8">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900">Related Articles</h3>
        <Link
          href="/blog"
          className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center"
        >
          View All <ArrowRight className="w-4 h-4 ml-1" />
        </Link>
      </div>

      <div className="grid gap-4">
        {relatedPosts.map(post => (
          <article
            key={post.id}
            className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex gap-4">
              {/* Thumbnail */}
              <div className="flex-shrink-0 w-24 h-24 rounded-lg overflow-hidden">
                <BlogCardImage post={post} className="w-full h-full object-cover" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center text-xs text-gray-500 mb-2">
                  <Calendar className="w-3 h-3 mr-1" />
                  <span className="mr-3">{post.date}</span>
                  <User className="w-3 h-3 mr-1" />
                  <span>{post.author}</span>
                </div>

                <h4 className="text-base font-semibold text-gray-900 mb-2 line-clamp-2">
                  <Link
                    href={`/blog/${post.slug}`}
                    className="hover:text-blue-600 transition-colors"
                  >
                    {post.title}
                  </Link>
                </h4>

                <p className="text-sm text-gray-600 line-clamp-2 mb-2">{post.excerpt}</p>

                {/* Tags/Categories */}
                <div className="flex flex-wrap gap-1">
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {post.category}
                  </span>
                  {post.serviceArea && (
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                      {post.serviceArea}
                    </span>
                  )}
                  {post.eventType && (
                    <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                      {post.eventType}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>

      {/* Call to Action */}
      <div className="mt-6 text-center">
        <Link
          href="/blog"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Explore More Articles <ArrowRight className="w-4 h-4 ml-2" />
        </Link>
      </div>
    </div>
  )
}
