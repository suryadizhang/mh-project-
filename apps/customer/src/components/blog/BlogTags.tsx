'use client'

import { Filter, Tag, X } from 'lucide-react'
import { useState } from 'react'

import type { BlogPost } from '@/data/blogPosts'

interface BlogTagsProps {
  posts: BlogPost[]
  onTagFilter: (tag: string) => void
  selectedTags: string[]
  onClearTags: () => void
}

export default function BlogTags({ posts, onTagFilter, selectedTags, onClearTags }: BlogTagsProps) {
  const [showAllTags, setShowAllTags] = useState(false)

  // Extract unique tags from all posts
  const allTags = Array.from(
    new Set(
      posts.flatMap(
        post => post.keywords?.slice(0, 5) || [] // Use first 5 keywords as tags
      )
    )
  ).sort()

  // Get popular tags (tags that appear in multiple posts)
  const tagCounts = allTags.reduce(
    (acc, tag) => {
      acc[tag] = posts.filter(post => post.keywords?.includes(tag)).length
      return acc
    },
    {} as Record<string, number>
  )

  const popularTags = allTags
    .filter(tag => tagCounts[tag] >= 2)
    .sort((a, b) => tagCounts[b] - tagCounts[a])

  const displayTags = showAllTags ? allTags : popularTags.slice(0, 12)

  const handleTagClick = (tag: string) => {
    onTagFilter(tag)
  }

  return (
    <div className="blog-tags-container">
      <div className="blog-tags-header">
        <div className="flex items-center gap-2">
          <Tag className="w-5 h-5 text-orange-600" />
          <h3 className="blog-tags-title">Popular Tags</h3>
        </div>

        {selectedTags.length > 0 && (
          <div className="blog-tags-selected">
            <span className="text-sm text-gray-600">
              {selectedTags.length} tag{selectedTags.length > 1 ? 's' : ''} selected
            </span>
            <button onClick={onClearTags} className="blog-tags-clear" aria-label="Clear all tags">
              <X className="w-4 h-4" />
              Clear All
            </button>
          </div>
        )}
      </div>

      <div className="blog-tags-cloud">
        {displayTags.map(tag => {
          const isSelected = selectedTags.includes(tag)
          const count = tagCounts[tag]
          const popularity = count >= 5 ? 'high' : count >= 3 ? 'medium' : 'low'

          return (
            <button
              key={tag}
              onClick={() => handleTagClick(tag)}
              className={`blog-tag blog-tag-${popularity} ${isSelected ? 'blog-tag-selected' : ''}`}
              title={`${count} post${count > 1 ? 's' : ''} with this tag`}
            >
              <span className="blog-tag-text">{tag}</span>
              <span className="blog-tag-count">{count}</span>
            </button>
          )
        })}
      </div>

      {popularTags.length > 12 && (
        <div className="blog-tags-toggle">
          <button onClick={() => setShowAllTags(!showAllTags)} className="blog-tags-toggle-btn">
            <Filter className="w-4 h-4" />
            {showAllTags ? 'Show Popular Tags' : `Show All Tags (${allTags.length})`}
          </button>
        </div>
      )}

      {selectedTags.length > 0 && (
        <div className="blog-tags-active">
          <h4 className="blog-tags-active-title">Active Filters:</h4>
          <div className="blog-tags-active-list">
            {selectedTags.map(tag => (
              <span key={tag} className="blog-tag-active">
                {tag}
                <button
                  onClick={() => onTagFilter(tag)}
                  className="blog-tag-remove"
                  aria-label={`Remove ${tag} filter`}
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
