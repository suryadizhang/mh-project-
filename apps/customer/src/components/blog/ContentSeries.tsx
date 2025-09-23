'use client';

import { BookOpen, Calendar, ChevronRight, Tag, Users } from 'lucide-react';
import Link from 'next/link';
import React, { useState } from 'react';

import { BlogPost } from '@/data/blogPosts';

import BlogCardImage from './BlogCardImage';

interface ContentSeries {
  id: string;
  title: string;
  description: string;
  posts: BlogPost[];
  category: string;
  difficulty?: 'Beginner' | 'Intermediate' | 'Advanced';
  estimatedTime?: string;
}

interface ContentSeriesProps {
  posts: BlogPost[];
  maxSeries?: number;
  className?: string;
}

export default function ContentSeries({
  posts,
  maxSeries = 6,
  className = '',
}: ContentSeriesProps) {
  const [selectedSeries, setSelectedSeries] = useState<string | null>(null);

  const generateSeries = (): ContentSeries[] => {
    const series: ContentSeries[] = [];

    // Wedding Series
    const weddingPosts = posts.filter(
      (post) =>
        post.keywords?.some(
          (keyword) =>
            keyword.toLowerCase().includes('wedding') ||
            keyword.toLowerCase().includes('reception'),
        ) || post.title.toLowerCase().includes('wedding'),
    );
    if (weddingPosts.length >= 2) {
      series.push({
        id: 'wedding-guide',
        title: 'Complete Wedding Hibachi Guide',
        description:
          'Everything you need to plan the perfect hibachi wedding reception, from intimate ceremonies to grand celebrations.',
        posts: weddingPosts.slice(0, 6),
        category: 'Wedding Events',
        difficulty: 'Intermediate',
        estimatedTime: '45 min read',
      });
    }

    // Corporate Events Series
    const corporatePosts = posts.filter(
      (post) =>
        post.keywords?.some(
          (keyword) =>
            keyword.toLowerCase().includes('corporate') ||
            keyword.toLowerCase().includes('team building') ||
            keyword.toLowerCase().includes('business'),
        ) || post.eventType?.toLowerCase().includes('corporate'),
    );
    if (corporatePosts.length >= 2) {
      series.push({
        id: 'corporate-events',
        title: 'Corporate Hibachi Events Mastery',
        description:
          'Professional guide to hosting successful corporate hibachi events, team building, and business entertainment.',
        posts: corporatePosts.slice(0, 5),
        category: 'Corporate Events',
        difficulty: 'Advanced',
        estimatedTime: '30 min read',
      });
    }

    // Family Celebrations Series
    const familyPosts = posts.filter(
      (post) =>
        post.keywords?.some(
          (keyword) =>
            keyword.toLowerCase().includes('family') ||
            keyword.toLowerCase().includes('birthday') ||
            keyword.toLowerCase().includes('anniversary') ||
            keyword.toLowerCase().includes('reunion'),
        ),
    );
    if (familyPosts.length >= 3) {
      series.push({
        id: 'family-celebrations',
        title: 'Family Hibachi Celebrations',
        description:
          'Create memorable family moments with hibachi catering for birthdays, anniversaries, and special gatherings.',
        posts: familyPosts.slice(0, 7),
        category: 'Family Events',
        difficulty: 'Beginner',
        estimatedTime: '25 min read',
      });
    }

    // Seasonal Events Series
    const seasonalPosts = posts.filter(
      (post) =>
        post.seasonal ||
        post.keywords?.some((keyword) =>
          ['spring', 'summer', 'fall', 'winter', 'holiday', 'christmas', 'thanksgiving'].includes(
            keyword.toLowerCase(),
          ),
        ),
    );
    if (seasonalPosts.length >= 3) {
      series.push({
        id: 'seasonal-hibachi',
        title: 'Seasonal Hibachi Planning',
        description:
          'Year-round hibachi event planning with seasonal menus, decorations, and celebration ideas.',
        posts: seasonalPosts.slice(0, 8),
        category: 'Seasonal Events',
        difficulty: 'Intermediate',
        estimatedTime: '40 min read',
      });
    }

    // Bay Area Locations Series
    const bayAreaPosts = posts.filter(
      (post) => post.serviceArea && !['All Areas', 'General'].includes(post.serviceArea),
    );
    if (bayAreaPosts.length >= 4) {
      series.push({
        id: 'bay-area-locations',
        title: 'Bay Area Hibachi Locations Guide',
        description:
          'Location-specific hibachi catering guides for San Francisco, Silicon Valley, Peninsula, and surrounding areas.',
        posts: bayAreaPosts.slice(0, 10),
        category: 'Location Guides',
        difficulty: 'Beginner',
        estimatedTime: '35 min read',
      });
    }

    // Tech Events Series
    const techPosts = posts.filter(
      (post) =>
        post.keywords?.some(
          (keyword) =>
            keyword.toLowerCase().includes('tech') ||
            keyword.toLowerCase().includes('silicon valley') ||
            keyword.toLowerCase().includes('startup'),
        ) || post.serviceArea?.toLowerCase().includes('silicon valley'),
    );
    if (techPosts.length >= 2) {
      series.push({
        id: 'tech-events',
        title: 'Silicon Valley Tech Events',
        description:
          'Hibachi catering for tech companies, startups, and Silicon Valley corporate culture.',
        posts: techPosts.slice(0, 5),
        category: 'Tech Events',
        difficulty: 'Advanced',
        estimatedTime: '20 min read',
      });
    }

    return series.slice(0, maxSeries);
  };

  const contentSeries = generateSeries();

  const handleSeriesClick = (seriesId: string) => {
    setSelectedSeries(selectedSeries === seriesId ? null : seriesId);
  };

  if (contentSeries.length === 0) {
    return null;
  }

  return (
    <div className={`rounded-lg border border-gray-200 bg-white shadow-sm ${className}`}>
      <div className="p-6">
        <div className="mb-6 flex items-center space-x-2">
          <BookOpen className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Content Series</h3>
          <span className="text-sm text-gray-500">({contentSeries.length} collections)</span>
        </div>

        <div className="space-y-4">
          {contentSeries.map((series) => (
            <div key={series.id} className="overflow-hidden rounded-lg border border-gray-200">
              {/* Series Header */}
              <button
                onClick={() => handleSeriesClick(series.id)}
                className="w-full p-4 text-left transition-colors hover:bg-gray-50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="mb-2 flex items-center space-x-2">
                      <h4 className="text-base font-semibold text-gray-900">{series.title}</h4>
                      <span className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-800">
                        {series.posts.length} posts
                      </span>
                      {series.difficulty && (
                        <span
                          className={`rounded px-2 py-1 text-xs ${
                            series.difficulty === 'Beginner'
                              ? 'bg-green-100 text-green-800'
                              : series.difficulty === 'Intermediate'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {series.difficulty}
                        </span>
                      )}
                    </div>
                    <p className="mb-2 text-sm text-gray-600">{series.description}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <div className="flex items-center">
                        <Tag className="mr-1 h-3 w-3" />
                        <span>{series.category}</span>
                      </div>
                      {series.estimatedTime && (
                        <div className="flex items-center">
                          <Calendar className="mr-1 h-3 w-3" />
                          <span>{series.estimatedTime}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <ChevronRight
                    className={`h-5 w-5 text-gray-400 transition-transform ${
                      selectedSeries === series.id ? 'rotate-90' : ''
                    }`}
                  />
                </div>
              </button>

              {/* Expanded Series Content */}
              {selectedSeries === series.id && (
                <div className="border-t border-gray-200 bg-gray-50 p-4">
                  <div className="grid gap-3">
                    {series.posts.map((post, index) => (
                      <div
                        key={post.id}
                        className="flex items-center space-x-3 rounded-lg border border-gray-200 bg-white p-3"
                      >
                        {/* Step Number */}
                        <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-800">
                          {index + 1}
                        </div>

                        {/* Thumbnail */}
                        <div className="h-12 w-12 flex-shrink-0 overflow-hidden rounded-lg">
                          <BlogCardImage post={post} className="h-full w-full object-cover" />
                        </div>

                        {/* Content */}
                        <div className="min-w-0 flex-1">
                          <h5 className="line-clamp-1 text-sm font-medium text-gray-900">
                            <Link
                              href={`/blog/${post.slug}`}
                              className="transition-colors hover:text-blue-600"
                            >
                              {post.title}
                            </Link>
                          </h5>
                          <p className="line-clamp-1 text-xs text-gray-500">{post.excerpt}</p>
                        </div>

                        {/* Read Time */}
                        <div className="flex-shrink-0 text-xs text-gray-400">{post.readTime}</div>
                      </div>
                    ))}
                  </div>

                  {/* Series CTA */}
                  <div className="mt-4 text-center">
                    <Link
                      href={`/blog?series=${series.id}`}
                      className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm text-white transition-colors hover:bg-blue-700"
                    >
                      <BookOpen className="mr-2 h-4 w-4" />
                      Start This Series
                    </Link>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Browse All Series */}
        <div className="mt-6 border-t border-gray-200 pt-4 text-center">
          <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center">
              <Users className="mr-1 h-4 w-4" />
              <span>{posts.length} total articles</span>
            </div>
            <div className="flex items-center">
              <BookOpen className="mr-1 h-4 w-4" />
              <span>{contentSeries.length} series available</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
