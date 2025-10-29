/**
 * Calendar Header Component
 * Navigation, view switching, and date display
 */

'use client';

import React from 'react';
import { format, addWeeks, addMonths, subWeeks, subMonths } from 'date-fns';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { CalendarView } from '../types/calendar.types';

interface CalendarHeaderProps {
  currentDate: Date;
  view: CalendarView;
  onDateChange: (date: Date) => void;
  onViewChange: (view: CalendarView) => void;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export function CalendarHeader({
  currentDate,
  view,
  onDateChange,
  onViewChange,
  onRefresh,
  isLoading = false,
}: CalendarHeaderProps) {
  const handlePrevious = () => {
    if (view === 'week') {
      onDateChange(subWeeks(currentDate, 1));
    } else {
      onDateChange(subMonths(currentDate, 1));
    }
  };

  const handleNext = () => {
    if (view === 'week') {
      onDateChange(addWeeks(currentDate, 1));
    } else {
      onDateChange(addMonths(currentDate, 1));
    }
  };

  const handleToday = () => {
    onDateChange(new Date());
  };

  const getDateRangeText = () => {
    if (view === 'week') {
      // Show week range
      const weekStart = new Date(currentDate);
      weekStart.setDate(currentDate.getDate() - currentDate.getDay());
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekStart.getDate() + 6);

      const sameMonth = weekStart.getMonth() === weekEnd.getMonth();
      
      if (sameMonth) {
        return `${format(weekStart, 'MMM d')} - ${format(weekEnd, 'd, yyyy')}`;
      } else {
        return `${format(weekStart, 'MMM d')} - ${format(weekEnd, 'MMM d, yyyy')}`;
      }
    } else {
      return format(currentDate, 'MMMM yyyy');
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left side - Date info and navigation */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <CalendarIcon className="w-5 h-5 text-gray-600" />
            <h2 className="text-xl font-bold text-gray-900">
              {getDateRangeText()}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrevious}
              className="px-2"
              title="Previous"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleToday}
              className="px-3"
            >
              Today
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleNext}
              className="px-2"
              title="Next"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading}
              className="px-3"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          )}
        </div>

        {/* Right side - View switcher */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600 mr-2">View:</span>
          <div className="inline-flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => onViewChange('week')}
              className={`
                px-4 py-2 text-sm font-medium transition-colors
                ${view === 'week'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
            >
              Week
            </button>
            <button
              onClick={() => onViewChange('month')}
              className={`
                px-4 py-2 text-sm font-medium border-l border-gray-200 transition-colors
                ${view === 'month'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
            >
              Month
            </button>
          </div>
        </div>
      </div>

      {/* Optional: Show current week number or additional info */}
      {view === 'week' && (
        <div className="mt-2 text-xs text-gray-500">
          Week {format(currentDate, 'w')} of {format(currentDate, 'yyyy')}
        </div>
      )}
    </div>
  );
}
