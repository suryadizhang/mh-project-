'use client';

import Link from 'next/link';
import React, { useEffect, useState, useMemo } from 'react';
import type { BlogPost } from '@my-hibachi/blog-types';

import { useAllPosts } from '@/hooks/useBlogAPI';

interface TagData {
  name: string;
  count: number;
  percentage: number;
  color: string;
  size: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl';
  weight: 'normal' | 'medium' | 'semibold' | 'bold';
}

interface AdvancedTagCloudProps {
  maxTags?: number;
  showCount?: boolean;
  interactive?: boolean;
  colorScheme?: 'gradient' | 'categorical' | 'monochrome';
  onTagClick?: (tag: string) => void;
}

const AdvancedTagCloud: React.FC<AdvancedTagCloudProps> = ({
  maxTags = 25,
  showCount = true,
  interactive = true,
  colorScheme = 'gradient',
  onTagClick,
}) => {
  const [hoveredTag, setHoveredTag] = useState<string | null>(null);
  const [tags, setTags] = useState<TagData[]>([]);

  // Use cached hook for all posts
  const { data, isLoading: loading } = useAllPosts();
  const allPosts = useMemo(() => data?.posts ?? [], [data]);

  // Calculate tags when posts are loaded
  useEffect(() => {
    if (allPosts.length === 0) return;

    try {
      const posts = allPosts;
      // Count tag occurrences
      const tagCounts = new Map<string, number>();
      posts.forEach((post: BlogPost) => {
        post.keywords.forEach((keyword: string) => {
          const normalizedTag = keyword.toLowerCase().trim();
          tagCounts.set(normalizedTag, (tagCounts.get(normalizedTag) || 0) + 1);
        });
      });

      // Convert to array and calculate percentages
      const totalPosts = posts.length;
      const tagArray: TagData[] = Array.from(tagCounts.entries())
        .map(([tag, count]) => ({
          name: tag,
          count,
          percentage: (count / totalPosts) * 100,
          color: '',
          size: 'base' as TagData['size'],
          weight: 'normal' as TagData['weight'],
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, maxTags);

      // Calculate tag sizes and weights based on count
      const maxCount = Math.max(...tagArray.map(t => t.count));
      const minCount = Math.min(...tagArray.map(t => t.count));
      const range = maxCount - minCount || 1;

      tagArray.forEach(tag => {
        const normalized = (tag.count - minCount) / range;

        // Set size
        if (normalized > 0.8) tag.size = '2xl';
        else if (normalized > 0.6) tag.size = 'xl';
        else if (normalized > 0.4) tag.size = 'lg';
        else if (normalized > 0.2) tag.size = 'base';
        else tag.size = 'sm';

        // Set weight
        if (normalized > 0.7) tag.weight = 'bold';
        else if (normalized > 0.5) tag.weight = 'semibold';
        else if (normalized > 0.3) tag.weight = 'medium';
        else tag.weight = 'normal';

        // Set color based on scheme
        tag.color = getTagColor(tag.name, colorScheme);
      });

      setTags(tagArray);
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  }, [allPosts, maxTags, colorScheme]);

  // Extract and count all tags (kept for backwards compatibility)
  const generateTagData = (): TagData[] => {
    return tags;
  };

  // Color generation helper
  const getTagColor = (tagName: string, scheme: string) => {
    const hash = tagName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);

    switch (scheme) {
      case 'gradient':
        const hue = (hash * 137.5) % 360; // Golden angle distribution
        return `hsl(${hue}, 70%, 50%)`;
      case 'categorical':
        const categories = [
          'text-blue-600', 'text-purple-600', 'text-pink-600',
          'text-red-600', 'text-orange-600', 'text-yellow-600',
          'text-green-600', 'text-teal-600', 'text-cyan-600'
        ];
        return categories[hash % categories.length];
      case 'monochrome':
        const intensities = [
          'text-slate-400', 'text-slate-500', 'text-slate-600',
          'text-slate-700', 'text-slate-800'
        ];
        return intensities[hash % intensities.length];
      default:
        return 'text-slate-600';
    }
  };

  const tagData = generateTagData();

  const getSizeClass = (size: TagData['size']) => {
    switch (size) {
      case 'xs':
        return 'text-xs';
      case 'sm':
        return 'text-sm';
      case 'base':
        return 'text-base';
      case 'lg':
        return 'text-lg';
      case 'xl':
        return 'text-xl';
      case '2xl':
        return 'text-2xl';
    }
  };

  const getWeightClass = (weight: TagData['weight']) => {
    switch (weight) {
      case 'normal':
        return 'font-normal';
      case 'medium':
        return 'font-medium';
      case 'semibold':
        return 'font-semibold';
      case 'bold':
        return 'font-bold';
    }
  };

  const handleTagClick = (tag: string) => {
    if (onTagClick) {
      onTagClick(tag);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-900">Popular Topics</h2>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="text-sm text-slate-500">Loading topics...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">Popular Topics</h2>
        <div className="text-sm text-slate-500">{tagData.length} topics</div>
      </div>

      <div className="flex flex-wrap gap-2 leading-relaxed">
        {tagData.map((tag) => {
          const isHovered = hoveredTag === tag.name;

          if (interactive) {
            return (
              <button
                key={tag.name}
                onClick={() => handleTagClick(tag.name)}
                onMouseEnter={() => setHoveredTag(tag.name)}
                onMouseLeave={() => setHoveredTag(null)}
                className={`inline-flex items-center rounded-md border px-3 py-1.5 transition-all duration-200 ${getSizeClass(
                  tag.size,
                )} ${getWeightClass(tag.weight)} ${
                  colorScheme === 'gradient'
                    ? 'border-transparent text-white'
                    : `${tag.color} border-slate-200`
                } ${isHovered ? 'scale-105 shadow-md' : 'hover:scale-102'} ${
                  colorScheme === 'gradient'
                    ? 'hover:brightness-110'
                    : 'hover:border-slate-300 hover:bg-slate-50'
                } `}
                style={
                  colorScheme === 'gradient'
                    ? {
                        backgroundColor: tag.color,
                        borderColor: tag.color,
                      }
                    : {}
                }
                title={`${tag.count} posts about ${tag.name}`}
              >
                <span className="capitalize">{tag.name.replace(/[-_]/g, ' ')}</span>
                {showCount && (
                  <span
                    className={`ml-2 rounded px-1.5 py-0.5 text-xs font-medium ${
                      colorScheme === 'gradient'
                        ? 'bg-opacity-20 bg-black text-white'
                        : 'bg-slate-100 text-slate-600'
                    } `}
                  >
                    {tag.count}
                  </span>
                )}
              </button>
            );
          }

          return (
            <Link
              key={tag.name}
              href={`/blog?tag=${encodeURIComponent(tag.name)}`}
              onMouseEnter={() => setHoveredTag(tag.name)}
              onMouseLeave={() => setHoveredTag(null)}
              className={`inline-flex items-center rounded-md border px-3 py-1.5 transition-all duration-200 ${getSizeClass(
                tag.size,
              )} ${getWeightClass(tag.weight)} ${
                colorScheme === 'gradient'
                  ? 'border-transparent text-white'
                  : `${tag.color} border-slate-200`
              } ${isHovered ? 'scale-105 shadow-md' : 'hover:scale-102'} ${
                colorScheme === 'gradient'
                  ? 'hover:brightness-110'
                  : 'hover:border-slate-300 hover:bg-slate-50'
              } `}
              style={
                colorScheme === 'gradient'
                  ? {
                      backgroundColor: tag.color,
                      borderColor: tag.color,
                    }
                  : {}
              }
              title={`${tag.count} posts about ${tag.name}`}
            >
              <span className="capitalize">{tag.name.replace(/[-_]/g, ' ')}</span>
              {showCount && (
                <span
                  className={`ml-2 rounded px-1.5 py-0.5 text-xs font-medium ${
                    colorScheme === 'gradient'
                      ? 'bg-opacity-20 bg-black text-white'
                      : 'bg-slate-100 text-slate-600'
                  } `}
                >
                  {tag.count}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Tag Statistics */}
      <div className="mt-6 border-t border-slate-200 pt-4">
        <div className="grid grid-cols-2 gap-4 text-center md:grid-cols-4">
          <div>
            <div className="text-2xl font-bold text-slate-700">{tagData.length}</div>
            <div className="text-xs text-slate-500">Topics</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-700">
              {Math.max(...tagData.map((t) => t.count))}
            </div>
            <div className="text-xs text-slate-500">Most Used</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-700">
              {Math.round(tagData.reduce((sum, t) => sum + t.count, 0) / tagData.length)}
            </div>
            <div className="text-xs text-slate-500">Avg Usage</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-700">{allPosts.length}</div>
            <div className="text-xs text-slate-500">Total Posts</div>
          </div>
        </div>
      </div>

      {/* Most Popular Tag Highlight */}
      {tagData.length > 0 && (
        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm text-slate-600">Most Popular Topic:</span>
              <span className="ml-2 font-semibold text-slate-900 capitalize">
                {tagData[0].name.replace(/[-_]/g, ' ')}
              </span>
            </div>
            <div className="text-sm text-slate-500">
              {tagData[0].count} posts ({tagData[0].percentage.toFixed(1)}%)
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedTagCloud;
