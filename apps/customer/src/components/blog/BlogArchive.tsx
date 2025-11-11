'use client';

import { Archive, Calendar, ChevronDown, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import React, { useMemo, useState } from 'react';

import type { BlogPost } from '@my-hibachi/blog-types';

interface BlogArchiveProps {
  posts: BlogPost[];
  onArchiveFilter?: (year: number, month?: number) => void;
  className?: string;
}

interface ArchiveItem {
  year: number;
  month: number;
  monthName: string;
  count: number;
  posts: BlogPost[];
}

interface YearlyArchive {
  year: number;
  count: number;
  months: ArchiveItem[];
}

const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

export default function BlogArchive({ posts, onArchiveFilter, className = '' }: BlogArchiveProps) {
  const [expandedYears, setExpandedYears] = useState<Set<number>>(new Set());

  const archiveData = useMemo(() => {
    const grouped = posts.reduce((acc, post) => {
      const date = new Date(post.date);
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const monthName = MONTH_NAMES[date.getMonth()];

      if (!acc[year]) {
        acc[year] = {};
      }
      if (!acc[year][month]) {
        acc[year][month] = {
          year,
          month,
          monthName,
          count: 0,
          posts: [],
        };
      }

      acc[year][month].count++;
      acc[year][month].posts.push(post);

      return acc;
    }, {} as Record<number, Record<number, ArchiveItem>>);

    // Convert to sorted yearly archives
    const yearlyArchives: YearlyArchive[] = Object.keys(grouped)
      .map(Number)
      .sort((a, b) => b - a) // Sort years descending
      .map((year) => {
        const months = Object.values(grouped[year]).sort((a, b) => b.month - a.month); // Recent months first
        return {
          year,
          count: months.reduce((sum, month) => sum + month.count, 0),
          months,
        };
      });

    return yearlyArchives;
  }, [posts]);

  const toggleYear = (year: number) => {
    const newExpanded = new Set(expandedYears);
    if (newExpanded.has(year)) {
      newExpanded.delete(year);
    } else {
      newExpanded.add(year);
    }
    setExpandedYears(newExpanded);
  };

  const handleYearClick = (year: number) => {
    if (onArchiveFilter) {
      onArchiveFilter(year);
    }
  };

  const handleMonthClick = (year: number, month: number) => {
    if (onArchiveFilter) {
      onArchiveFilter(year, month);
    }
  };

  if (archiveData.length === 0) {
    return (
      <div className={`rounded-lg border border-gray-200 bg-white p-6 ${className}`}>
        <div className="mb-4 flex items-center space-x-2">
          <Archive className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Blog Archive</h3>
        </div>
        <p className="text-sm text-gray-500">No archived posts available.</p>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border border-gray-200 bg-white shadow-sm ${className}`}>
      <div className="p-6">
        <div className="mb-6 flex items-center space-x-2">
          <Archive className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Blog Archive</h3>
          <span className="text-sm text-gray-500">({posts.length} total posts)</span>
        </div>

        <div className="space-y-3">
          {archiveData.map((yearData) => (
            <div
              key={yearData.year}
              className="border-b border-gray-100 pb-3 last:border-b-0 last:pb-0"
            >
              {/* Year Header */}
              <div className="flex items-center justify-between">
                <button
                  onClick={() => handleYearClick(yearData.year)}
                  className="flex items-center space-x-2 font-medium text-gray-900 transition-colors hover:text-blue-600"
                >
                  <Calendar className="h-4 w-4" />
                  <span>{yearData.year}</span>
                  <span className="text-sm font-normal text-gray-500">
                    ({yearData.count} posts)
                  </span>
                </button>

                <button
                  onClick={() => toggleYear(yearData.year)}
                  className="p-1 text-gray-400 transition-colors hover:text-gray-600"
                  aria-label={`${expandedYears.has(yearData.year) ? 'Collapse' : 'Expand'} ${
                    yearData.year
                  }`}
                >
                  {expandedYears.has(yearData.year) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </button>
              </div>

              {/* Months (when expanded) */}
              {expandedYears.has(yearData.year) && (
                <div className="mt-3 ml-6 space-y-2">
                  {yearData.months.map((monthData) => (
                    <div key={monthData.month} className="flex items-center justify-between">
                      <button
                        onClick={() => handleMonthClick(monthData.year, monthData.month)}
                        className="flex items-center space-x-2 text-sm text-gray-700 transition-colors hover:text-blue-600"
                      >
                        <span>{monthData.monthName}</span>
                        <span className="text-xs text-gray-500">({monthData.count} posts)</span>
                      </button>

                      {/* Recent posts preview */}
                      <div className="text-xs text-gray-400">
                        {monthData.posts
                          .slice(0, 2)
                          .map((post) => post.title.slice(0, 20))
                          .join(', ')}
                        {monthData.posts.length > 2 && '...'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Quick Stats */}
        <div className="mt-6 border-t border-gray-200 pt-6">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{archiveData.length}</div>
              <div className="text-gray-500">Years</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {archiveData.reduce((sum, year) => sum + year.months.length, 0)}
              </div>
              <div className="text-gray-500">Months</div>
            </div>
          </div>
        </div>

        {/* Browse All Link */}
        <div className="mt-4 border-t border-gray-200 pt-4 text-center">
          <Link
            href="/blog"
            className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            Browse All Posts
            <ChevronRight className="ml-1 h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
