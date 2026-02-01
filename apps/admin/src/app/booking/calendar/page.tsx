/**
 * Calendar Page - Main route for booking calendar views
 * Integrates weekly and monthly calendar views with drag-drop booking management
 */

'use client';

import { AlertCircle, CalendarIcon } from 'lucide-react';
import React, { useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';

import { Button } from '@/components/ui/button';

import { CalendarHeader } from './components/CalendarHeader';
import { MonthlyCalendar } from './components/MonthlyCalendar';
import { WeeklyCalendar } from './components/WeeklyCalendar';
import { useCalendarData } from './hooks/useCalendarData';
import type {
  CalendarBooking,
  CalendarView,
  DayColumn,
} from './types/calendar.types';

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<CalendarView>('week');
  const [selectedBooking, setSelectedBooking] =
    useState<CalendarBooking | null>(null);
  const [selectedDay, setSelectedDay] = useState<DayColumn | null>(null);

  // Get auth context for role-based filtering
  const { stationContext } = useAuth();

  // Determine filters based on user role
  // STATION_MANAGER/ADMIN: See only their station's bookings
  // CHEF: See only their assigned events
  // SUPER_ADMIN/CUSTOMER_SUPPORT: See all bookings (no filter)
  const stationId =
    stationContext?.role === 'STATION_MANAGER' ||
    stationContext?.role === 'ADMIN'
      ? stationContext.station_id
      : null;
  const chefId =
    stationContext?.role === 'CHEF' ? stationContext.chef_id : null;

  // Fetch calendar data with role-based filters
  const { bookings, weekView, monthView, loading, error, refetch } =
    useCalendarData({
      view,
      currentDate,
      stationId,
      chefId,
    });

  // Handle booking click - could open modal/sidebar
  const handleBookingClick = (booking: CalendarBooking) => {
    setSelectedBooking(booking);
    // TODO: Open booking details modal
    console.log('Booking clicked:', booking);
  };

  // Handle day click in month view - could show day details
  const handleDayClick = (day: DayColumn) => {
    setSelectedDay(day);
    // TODO: Open day details modal with all bookings
    console.log('Day clicked:', day);
  };

  // Handle view change
  const handleViewChange = (newView: CalendarView) => {
    setView(newView);
  };

  // Handle date change
  const handleDateChange = (newDate: Date) => {
    setCurrentDate(newDate);
  };

  // Error state
  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="text-red-600 mb-4">
            <AlertCircle className="w-16 h-16 mx-auto mb-4" />
            <h3 className="text-xl font-semibold">Error Loading Calendar</h3>
            <p className="text-sm text-gray-600 mt-2">{error}</p>
          </div>
          <Button onClick={refetch} className="mt-6">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading && !weekView && !monthView) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading calendar...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-4 sm:px-6 py-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <CalendarIcon className="w-5 h-5 sm:w-6 sm:h-6" />
              Booking Calendar
            </h1>
            <p className="text-xs sm:text-sm text-gray-600 mt-1">
              Manage and reschedule bookings{' '}
              {view === 'week' ? 'with drag-and-drop' : ''}
            </p>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-4 sm:gap-6 w-full sm:w-auto justify-between sm:justify-end">
            <div className="text-center">
              <div className="text-xl sm:text-2xl font-bold text-gray-900">
                {bookings.length}
              </div>
              <div className="text-xs text-gray-600">Total</div>
            </div>
            <div className="text-center">
              <div className="text-xl sm:text-2xl font-bold text-green-600">
                {bookings.filter(b => b.status === 'confirmed').length}
              </div>
              <div className="text-xs text-gray-600">Confirmed</div>
            </div>
            <div className="text-center">
              <div className="text-xl sm:text-2xl font-bold text-yellow-600">
                {bookings.filter(b => b.status === 'pending').length}
              </div>
              <div className="text-xs text-gray-600">Pending</div>
            </div>
          </div>
        </div>
      </div>

      {/* Calendar Header with Navigation */}
      <CalendarHeader
        currentDate={currentDate}
        view={view}
        onDateChange={handleDateChange}
        onViewChange={handleViewChange}
        onRefresh={refetch}
        isLoading={loading}
      />

      {/* Calendar View */}
      <div className="flex-1 overflow-hidden p-3 sm:p-6">
        {view === 'week' && weekView && (
          <WeeklyCalendar
            weekView={weekView}
            onBookingClick={handleBookingClick}
            onRefresh={refetch}
          />
        )}

        {view === 'month' && monthView && (
          <MonthlyCalendar
            monthView={monthView}
            onBookingClick={handleBookingClick}
            onDayClick={handleDayClick}
            onRefresh={refetch}
          />
        )}
      </div>

      {/* Loading Indicator */}
      {loading && (weekView || monthView) && (
        <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg border border-gray-200 px-4 py-3 flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-sm text-gray-600">Updating...</span>
        </div>
      )}

      {/* TODO: Add Booking Details Modal */}
      {/* TODO: Add Day Details Modal */}
      {/* TODO: Add Booking Creation/Edit Modal */}
    </div>
  );
}
