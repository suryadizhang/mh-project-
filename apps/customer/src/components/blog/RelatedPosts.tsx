'use client';

import type { BlogPost } from '@my-hibachi/blog-types';
import { ArrowRight, Calendar, User } from 'lucide-react';
import Link from 'next/link';
import React from 'react';

import { getAuthorName } from '@/lib/blog/helpers';

import BlogCardImage from './BlogCardImage';

interface RelatedPostsProps {
  currentPost: BlogPost;
  allPosts: BlogPost[];
  maxPosts?: number;
}

export default function RelatedPosts({ currentPost, allPosts, maxPosts = 3 }: RelatedPostsProps) {
  const getRelatedPosts = (): BlogPost[] => {
    // Filter out the current post
    const otherPosts = allPosts.filter((post) => post.id !== currentPost.id);

    // Score posts based on relevance
    const scoredPosts = otherPosts.map((post) => {
      let score = 0;

      // Same category gets highest score
      if (post.category === currentPost.category) {
        score += 10;
      }

      // Same service area gets high score
      if (post.serviceArea === currentPost.serviceArea) {
        score += 8;
      }

      // Same event type gets high score
      if (post.eventType === currentPost.eventType) {
        score += 7;
      }

      // Shared keywords/tags
      const currentKeywords = currentPost.keywords || [];
      const postKeywords = post.keywords || [];
      const sharedKeywords = currentKeywords.filter((keyword: string) =>
        postKeywords.includes(keyword),
      );
      score += sharedKeywords.length * 2;

      // Same author gets moderate score
      if (post.author === currentPost.author) {
        score += 3;
      }

      // Recent posts get slight bonus (within 30 days)
      const postDate = new Date(post.date);
      const currentPostDate = new Date(currentPost.date);
      const daysDiff = Math.abs(
        (postDate.getTime() - currentPostDate.getTime()) / (1000 * 60 * 60 * 24),
      );
      if (daysDiff <= 30) {
        score += 1;
      }

      return { post, score };
    });

    // Sort by score and return top posts
    return scoredPosts
      .sort((a, b) => b.score - a.score)
      .slice(0, maxPosts)
      .map((item) => item.post);
  };

  const relatedPosts = getRelatedPosts();

  if (relatedPosts.length === 0) {
    return null;
  }

  return (
    <div className="mt-8 rounded-lg bg-gray-50 p-6">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-xl font-bold text-gray-900">Related Articles</h3>
        <Link
          href="/blog"
          className="flex items-center text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          View All <ArrowRight className="ml-1 h-4 w-4" />
        </Link>
      </div>

      <div className="grid gap-4">
        {relatedPosts.map((post) => (
          <article
            key={post.id}
            className="rounded-lg border border-gray-200 bg-white p-4 transition-shadow hover:shadow-md"
          >
            <div className="flex gap-4">
              {/* Thumbnail */}
              <div className="h-24 w-24 flex-shrink-0 overflow-hidden rounded-lg">
                <BlogCardImage post={post} className="h-full w-full object-cover" />
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex items-center text-xs text-gray-500">
                  <Calendar className="mr-1 h-3 w-3" />
                  <span className="mr-3">{post.date}</span>
                  <User className="mr-1 h-3 w-3" />
                  <span>{getAuthorName(post.author)}</span>
                </div>

                <h4 className="mb-2 line-clamp-2 text-base font-semibold text-gray-900">
                  <Link
                    href={`/blog/${post.slug}`}
                    className="transition-colors hover:text-blue-600"
                  >
                    {post.title}
                  </Link>
                </h4>

                <p className="mb-2 line-clamp-2 text-sm text-gray-600">{post.excerpt}</p>

                {/* Tags/Categories */}
                <div className="flex flex-wrap gap-1">
                  <span className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-800">
                    {post.category}
                  </span>
                  {post.serviceArea && (
                    <span className="rounded bg-green-100 px-2 py-1 text-xs text-green-800">
                      {post.serviceArea}
                    </span>
                  )}
                  {post.eventType && (
                    <span className="rounded bg-purple-100 px-2 py-1 text-xs text-purple-800">
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
          className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
        >
          Explore More Articles <ArrowRight className="ml-2 h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
