'use client';

import type { BlogPost } from '@my-hibachi/blog-types';
import { ChevronRight, Folder, Grid, List } from 'lucide-react';
import { useState } from 'react';

interface BlogCategoriesProps {
  posts: BlogPost[];
  onCategoryFilter: (category: string) => void;
  selectedCategory: string;
}

export default function BlogCategories({
  posts,
  onCategoryFilter,
  selectedCategory,
}: BlogCategoriesProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Get categories with post counts
  const categoryData = posts.reduce(
    (acc, post) => {
      const category = post.category || 'Uncategorized';
      if (!acc[category]) {
        acc[category] = {
          name: category,
          count: 0,
          posts: [],
          description: getCategoryDescription(category),
        };
      }
      acc[category].count++;
      acc[category].posts.push(post);
      return acc;
    },
    {} as Record<string, { name: string; count: number; posts: BlogPost[]; description: string }>,
  );

  const categories = Object.values(categoryData).sort((a, b) => b.count - a.count);

  function getCategoryDescription(category: string): string {
    const descriptions: Record<string, string> = {
      'Event Planning': 'Complete guides for planning hibachi events',
      Seasonal: 'Seasonal menus and holiday celebrations',
      Corporate: 'Business events and team building',
      Wedding: 'Wedding receptions and romantic dining',
      Birthday: 'Birthday parties and celebrations',
      Holiday: 'Holiday parties and seasonal events',
      'Location Specific': 'City and region-specific guides',
      'Tips & Guides': 'Expert hibachi tips and how-tos',
      Uncategorized: 'General hibachi catering content',
    };
    return descriptions[category] || 'Hibachi catering insights and guides';
  }

  function getCategoryIcon(category: string) {
    const icons: Record<string, string> = {
      'Event Planning': '🎉',
      Seasonal: '🍂',
      Corporate: '🏢',
      Wedding: '💍',
      Birthday: '🎂',
      Holiday: '🎄',
      'Location Specific': '📍',
      'Tips & Guides': '💡',
      Uncategorized: '📝',
    };
    return icons[category] || '📄';
  }

  return (
    <div className="blog-categories-container">
      <div className="blog-categories-header">
        <div className="flex items-center gap-2">
          <Folder className="h-5 w-5 text-orange-600" />
          <h3 className="blog-categories-title">Browse by Category</h3>
        </div>

        <div className="blog-categories-view-toggle">
          <button
            onClick={() => setViewMode('grid')}
            className={`blog-view-btn ${viewMode === 'grid' ? 'active' : ''}`}
            aria-label="Grid view"
          >
            <Grid className="h-4 w-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`blog-view-btn ${viewMode === 'list' ? 'active' : ''}`}
            aria-label="List view"
          >
            <List className="h-4 w-4" />
          </button>
        </div>
      </div>

      {selectedCategory !== 'All' && (
        <div className="blog-categories-breadcrumb">
          <button onClick={() => onCategoryFilter('All')} className="blog-breadcrumb-link">
            All Categories
          </button>
          <ChevronRight className="h-4 w-4 text-gray-400" />
          <span className="blog-breadcrumb-current">{selectedCategory}</span>
        </div>
      )}

      <div className={`blog-categories-grid ${viewMode === 'list' ? 'blog-categories-list' : ''}`}>
        <button
          onClick={() => onCategoryFilter('All')}
          className={`blog-category-card ${
            selectedCategory === 'All' ? 'blog-category-selected' : ''
          }`}
        >
          <div className="blog-category-icon">🗂️</div>
          <div className="blog-category-content">
            <h4 className="blog-category-name">All Categories</h4>
            <p className="blog-category-description">Browse all hibachi guides</p>
            <span className="blog-category-count">{posts.length} posts</span>
          </div>
        </button>

        {categories.map((category) => (
          <button
            key={category.name}
            onClick={() => onCategoryFilter(category.name)}
            className={`blog-category-card ${
              selectedCategory === category.name ? 'blog-category-selected' : ''
            }`}
          >
            <div className="blog-category-icon">{getCategoryIcon(category.name)}</div>
            <div className="blog-category-content">
              <h4 className="blog-category-name">{category.name}</h4>
              <p className="blog-category-description">{category.description}</p>
              <span className="blog-category-count">
                {category.count} post{category.count !== 1 ? 's' : ''}
              </span>
            </div>
            {viewMode === 'list' && (
              <ChevronRight className="blog-category-arrow h-5 w-5 text-gray-400" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
