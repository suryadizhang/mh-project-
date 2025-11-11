'use client';

import type { BlogPost } from '@my-hibachi/blog-types';
import { Filter, Tag, X } from 'lucide-react';
import { useState } from 'react';

import { cn } from '@/lib/utils';

import styles from './BlogTags.module.css';

interface BlogTagsProps {
  posts: BlogPost[];
  onTagFilter: (tag: string) => void;
  selectedTags: string[];
  onClearTags: () => void;
}

export default function BlogTags({ posts, onTagFilter, selectedTags, onClearTags }: BlogTagsProps) {
  const [showAllTags, setShowAllTags] = useState(false);

  // Extract unique tags from all posts
  const allTags = Array.from(
    new Set(
      posts.flatMap(
        (post) => post.keywords?.slice(0, 5) || [], // Use first 5 keywords as tags
      ),
    ),
  ).sort();

  // Get popular tags (tags that appear in multiple posts)
  const tagCounts = allTags.reduce(
    (acc, tag) => {
      acc[tag] = posts.filter((post) => post.keywords?.includes(tag)).length;
      return acc;
    },
    {} as Record<string, number>,
  );

  const popularTags = allTags
    .filter((tag) => tagCounts[tag] >= 2)
    .sort((a, b) => tagCounts[b] - tagCounts[a]);

  const displayTags = showAllTags ? allTags : popularTags.slice(0, 12);

  const handleTagClick = (tag: string) => {
    onTagFilter(tag);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className="flex items-center gap-2">
          <Tag className="h-5 w-5 text-orange-600" />
          <h3 className={styles.title}>Popular Tags</h3>
        </div>

        {selectedTags.length > 0 && (
          <div className={styles.selected}>
            <span className="text-sm text-gray-600">
              {selectedTags.length} tag{selectedTags.length > 1 ? 's' : ''} selected
            </span>
            <button onClick={onClearTags} className={styles.clear} aria-label="Clear all tags">
              <X className="h-4 w-4" />
              Clear All
            </button>
          </div>
        )}
      </div>

      <div className={styles.cloud}>
        {displayTags.map((tag) => {
          const isSelected = selectedTags.includes(tag);
          const count = tagCounts[tag];
          const popularity = count >= 5 ? 'high' : count >= 3 ? 'medium' : 'low';

          const popularityClass = {
            high: styles.tagHigh,
            medium: styles.tagMedium,
            low: styles.tagLow,
          }[popularity];

          return (
            <button
              key={tag}
              onClick={() => handleTagClick(tag)}
              className={cn(styles.tag, popularityClass, isSelected && styles.tagSelected)}
              title={`${count} post${count > 1 ? 's' : ''} with this tag`}
            >
              <span>{tag}</span>
              <span className={styles.tagCount}>{count}</span>
            </button>
          );
        })}
      </div>

      {popularTags.length > 12 && (
        <div className={styles.toggle}>
          <button onClick={() => setShowAllTags(!showAllTags)} className={styles.toggleBtn}>
            <Filter className="h-4 w-4" />
            {showAllTags ? 'Show Popular Tags' : `Show All Tags (${allTags.length})`}
          </button>
        </div>
      )}

      {selectedTags.length > 0 && (
        <div className={styles.active}>
          <h4 className={styles.activeTitle}>Active Filters:</h4>
          <div className={styles.activeList}>
            {selectedTags.map((tag) => (
              <span key={tag} className={styles.tagActive}>
                {tag}
                <button
                  onClick={() => onTagFilter(tag)}
                  className={styles.tagRemove}
                  aria-label={`Remove ${tag} filter`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
