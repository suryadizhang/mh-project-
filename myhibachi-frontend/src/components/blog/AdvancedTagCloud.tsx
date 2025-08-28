'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { blogPosts } from '@/data/blogPosts';

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
  onTagClick
}) => {
  const [hoveredTag, setHoveredTag] = useState<string | null>(null);

  // Extract and count all tags
  const generateTagData = (): TagData[] => {
    const tagCounts = new Map<string, number>();
    
    // Count tag occurrences
    blogPosts.forEach(post => {
      post.keywords.forEach(keyword => {
        const normalizedTag = keyword.toLowerCase().trim();
        tagCounts.set(normalizedTag, (tagCounts.get(normalizedTag) || 0) + 1);
      });
    });

    // Convert to array and calculate percentages
    const totalPosts = blogPosts.length;
    const tagArray = Array.from(tagCounts.entries()).map(([tag, count]) => ({
      name: tag,
      count,
      percentage: (count / totalPosts) * 100
    }));

    // Sort by count and take top tags
    const sortedTags = tagArray
      .sort((a, b) => b.count - a.count)
      .slice(0, maxTags);

    // Calculate sizes and weights based on usage
    const maxCount = Math.max(...sortedTags.map(t => t.count));
    const minCount = Math.min(...sortedTags.map(t => t.count));

    return sortedTags.map((tag, index) => {
      // Calculate relative size
      const normalizedSize = (tag.count - minCount) / (maxCount - minCount);
      
      const size = normalizedSize > 0.8 ? '2xl' :
                   normalizedSize > 0.6 ? 'xl' :
                   normalizedSize > 0.4 ? 'lg' :
                   normalizedSize > 0.2 ? 'base' : 'sm';
      
      const weight = normalizedSize > 0.7 ? 'bold' :
                     normalizedSize > 0.5 ? 'semibold' :
                     normalizedSize > 0.3 ? 'medium' : 'normal';

      // Generate colors based on scheme
      let color = '';
      switch (colorScheme) {
        case 'gradient':
          const hue = (index * 137.5) % 360; // Golden angle distribution
          color = `hsl(${hue}, 70%, 50%)`;
          break;
        case 'categorical':
          const categories = [
            'text-slate-600', 'text-slate-700', 'text-slate-500', 'text-slate-800',
            'text-slate-400', 'text-slate-900', 'text-slate-600', 'text-slate-500'
          ];
          color = categories[index % categories.length];
          break;
        case 'monochrome':
          const intensities = ['text-slate-400', 'text-slate-500', 'text-slate-600', 'text-slate-700', 'text-slate-800'];
          color = intensities[Math.floor(normalizedSize * (intensities.length - 1))];
          break;
      }

      return {
        ...tag,
        color,
        size,
        weight
      };
    });
  };

  const tagData = generateTagData();

  const getSizeClass = (size: TagData['size']) => {
    switch (size) {
      case 'xs': return 'text-xs';
      case 'sm': return 'text-sm';
      case 'base': return 'text-base';
      case 'lg': return 'text-lg';
      case 'xl': return 'text-xl';
      case '2xl': return 'text-2xl';
    }
  };

  const getWeightClass = (weight: TagData['weight']) => {
    switch (weight) {
      case 'normal': return 'font-normal';
      case 'medium': return 'font-medium';
      case 'semibold': return 'font-semibold';
      case 'bold': return 'font-bold';
    }
  };

  const handleTagClick = (tag: string) => {
    if (onTagClick) {
      onTagClick(tag);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-slate-900">
          Popular Topics
        </h2>
        <div className="text-sm text-slate-500">
          {tagData.length} topics
        </div>
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
                className={`
                  inline-flex items-center px-3 py-1.5 rounded-md border transition-all duration-200
                  ${getSizeClass(tag.size)} ${getWeightClass(tag.weight)}
                  ${colorScheme === 'gradient' ? 'text-white border-transparent' : `${tag.color} border-slate-200`}
                  ${isHovered ? 'scale-105 shadow-md' : 'hover:scale-102'}
                  ${colorScheme === 'gradient' ? 'hover:brightness-110' : 'hover:bg-slate-50 hover:border-slate-300'}
                `}
                style={colorScheme === 'gradient' ? { 
                  backgroundColor: tag.color,
                  borderColor: tag.color 
                } : {}}
                title={`${tag.count} posts about ${tag.name}`}
              >
                <span className="capitalize">
                  {tag.name.replace(/[-_]/g, ' ')}
                </span>
                {showCount && (
                  <span className={`
                    ml-2 px-1.5 py-0.5 rounded text-xs font-medium
                    ${colorScheme === 'gradient' ? 'bg-black bg-opacity-20 text-white' : 'bg-slate-100 text-slate-600'}
                  `}>
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
              className={`
                inline-flex items-center px-3 py-1.5 rounded-md border transition-all duration-200
                ${getSizeClass(tag.size)} ${getWeightClass(tag.weight)}
                ${colorScheme === 'gradient' ? 'text-white border-transparent' : `${tag.color} border-slate-200`}
                ${isHovered ? 'scale-105 shadow-md' : 'hover:scale-102'}
                ${colorScheme === 'gradient' ? 'hover:brightness-110' : 'hover:bg-slate-50 hover:border-slate-300'}
              `}
              style={colorScheme === 'gradient' ? { 
                backgroundColor: tag.color,
                borderColor: tag.color 
              } : {}}
              title={`${tag.count} posts about ${tag.name}`}
            >
              <span className="capitalize">
                {tag.name.replace(/[-_]/g, ' ')}
              </span>
              {showCount && (
                <span className={`
                  ml-2 px-1.5 py-0.5 rounded text-xs font-medium
                  ${colorScheme === 'gradient' ? 'bg-black bg-opacity-20 text-white' : 'bg-slate-100 text-slate-600'}
                `}>
                  {tag.count}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Tag Statistics */}
      <div className="mt-6 pt-4 border-t border-slate-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-slate-700">{tagData.length}</div>
            <div className="text-xs text-slate-500">Topics</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-700">
              {Math.max(...tagData.map(t => t.count))}
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
            <div className="text-2xl font-bold text-slate-700">
              {blogPosts.length}
            </div>
            <div className="text-xs text-slate-500">Total Posts</div>
          </div>
        </div>
      </div>

      {/* Most Popular Tag Highlight */}
      {tagData.length > 0 && (
        <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
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
