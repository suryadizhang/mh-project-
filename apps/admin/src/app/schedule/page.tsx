'use client';

import {
  AlertCircle,
  Calendar,
  Check,
  ChefHat,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock,
  Edit2,
  Filter,
  Plus,
  Save,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { bookingService, chefService, Booking } from '@/lib/api';
import { cn } from '@/lib/utils';

// =============================================================================
// Types
// =============================================================================

interface Station {
  id: string;
  name: string;
  address: string;
  timezone: string;
}

interface Chef {
  id: string;
  name: string;
  email: string;
  phone?: string;
  station_id: string;
  station_name?: string;
  avatar_url?: string;
}

interface TimeSlot {
  id: string;
  time: string; // 24hr format: "12:00", "15:00", "18:00", "21:00"
  label: string; // Display: "12:00 PM", "3:00 PM", "6:00 PM", "9:00 PM"
}

interface WeeklyTemplate {
  id: string;
  chef_id: string;
  day_of_week: number; // 0 = Sunday, 6 = Saturday
  available_slots: string[]; // Array of time slot IDs
  is_available: boolean;
  effective_from?: string; // ISO date
  effective_to?: string; // ISO date
}

interface DateOverride {
  id: string;
  chef_id: string;
  date: string; // ISO date YYYY-MM-DD
  available_slots: string[]; // Empty means fully unavailable
  is_available: boolean;
  reason?: string; // e.g., "Vacation", "Personal", "Booked"
  created_by?: string;
}

type ViewMode = 'week' | 'month';

// =============================================================================
// Constants
// =============================================================================

const STANDARD_TIME_SLOTS: TimeSlot[] = [
  { id: 'slot-12', time: '12:00', label: '12:00 PM' },
  { id: 'slot-15', time: '15:00', label: '3:00 PM' },
  { id: 'slot-18', time: '18:00', label: '6:00 PM' },
  { id: 'slot-21', time: '21:00', label: '9:00 PM' },
];

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DAYS_OF_WEEK_FULL = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
];

// =============================================================================
// Helper Functions
// =============================================================================

function getWeekDates(baseDate: Date): Date[] {
  const week: Date[] = [];
  const startOfWeek = new Date(baseDate);
  startOfWeek.setDate(baseDate.getDate() - baseDate.getDay());

  for (let i = 0; i < 7; i++) {
    const date = new Date(startOfWeek);
    date.setDate(startOfWeek.getDate() + i);
    week.push(date);
  }
  return week;
}

function getMonthDates(year: number, month: number): Date[] {
  const dates: Date[] = [];
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  // Add padding days from previous month
  const startPadding = firstDay.getDay();
  for (let i = startPadding - 1; i >= 0; i--) {
    const date = new Date(year, month, -i);
    dates.push(date);
  }

  // Add all days of current month
  for (let day = 1; day <= lastDay.getDate(); day++) {
    dates.push(new Date(year, month, day));
  }

  // Add padding days from next month to complete the grid (6 rows)
  const totalCells = 42; // 6 rows × 7 days
  while (dates.length < totalCells) {
    const date = new Date(
      year,
      month + 1,
      dates.length - lastDay.getDate() - startPadding + 1
    );
    dates.push(date);
  }

  return dates;
}

function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

function formatDateDisplay(date: Date): string {
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

function isToday(date: Date): boolean {
  const today = new Date();
  return formatDate(date) === formatDate(today);
}

function isSameMonth(date: Date, referenceDate: Date): boolean {
  return (
    date.getMonth() === referenceDate.getMonth() &&
    date.getFullYear() === referenceDate.getFullYear()
  );
}

// =============================================================================
// Mock Data (Replace with API calls)
// =============================================================================

const MOCK_STATIONS: Station[] = [
  {
    id: 'station-1',
    name: 'Fremont Station',
    address: '123 Main St, Fremont, CA',
    timezone: 'America/Los_Angeles',
  },
  {
    id: 'station-2',
    name: 'San Jose Station',
    address: '456 Oak Ave, San Jose, CA',
    timezone: 'America/Los_Angeles',
  },
  {
    id: 'station-3',
    name: 'Sacramento Station',
    address: '789 Capitol Blvd, Sacramento, CA',
    timezone: 'America/Los_Angeles',
  },
];

// NOTE: MOCK_CHEFS removed - now fetched from API via chefService.getStationChefs()

// Mock weekly templates (default availability)
const MOCK_WEEKLY_TEMPLATES: WeeklyTemplate[] = [
  // Chef Takeshi - Available Mon-Sat all slots
  ...Array.from({ length: 6 }, (_, i) => ({
    id: `wt-1-${i + 1}`,
    chef_id: 'chef-1',
    day_of_week: i + 1, // Monday = 1 through Saturday = 6
    available_slots: ['slot-12', 'slot-15', 'slot-18', 'slot-21'],
    is_available: true,
  })),
  // Chef Maria - Available Fri-Sun evening slots only
  {
    id: 'wt-2-5',
    chef_id: 'chef-2',
    day_of_week: 5,
    available_slots: ['slot-18', 'slot-21'],
    is_available: true,
  },
  {
    id: 'wt-2-6',
    chef_id: 'chef-2',
    day_of_week: 6,
    available_slots: ['slot-12', 'slot-15', 'slot-18', 'slot-21'],
    is_available: true,
  },
  {
    id: 'wt-2-0',
    chef_id: 'chef-2',
    day_of_week: 0,
    available_slots: ['slot-12', 'slot-15', 'slot-18'],
    is_available: true,
  },
];

// Mock date overrides
const MOCK_DATE_OVERRIDES: DateOverride[] = [
  {
    id: 'do-1',
    chef_id: 'chef-1',
    date: formatDate(new Date()),
    available_slots: ['slot-18', 'slot-21'],
    is_available: true,
    reason: 'Morning appointment',
  },
  {
    id: 'do-2',
    chef_id: 'chef-1',
    date: formatDate(new Date(Date.now() + 86400000 * 3)),
    available_slots: [],
    is_available: false,
    reason: 'Vacation',
  },
];

// =============================================================================
// Components
// =============================================================================

interface StationSelectorProps {
  stations: Station[];
  selectedStationId: string | null;
  onSelect: (stationId: string | null) => void;
  showAll?: boolean;
}

function StationSelector({
  stations,
  selectedStationId,
  onSelect,
  showAll = false,
}: StationSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedStation = stations.find(s => s.id === selectedStationId);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50"
      >
        <Filter className="h-4 w-4 text-gray-500" />
        {selectedStation ? selectedStation.name : 'All Stations'}
        <ChevronDown className="h-4 w-4 text-gray-400" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute left-0 top-full z-20 mt-1 w-64 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
            {showAll && (
              <button
                onClick={() => {
                  onSelect(null);
                  setIsOpen(false);
                }}
                className={cn(
                  'flex w-full items-center px-4 py-2 text-sm hover:bg-gray-100',
                  !selectedStationId && 'bg-gray-50 font-medium'
                )}
              >
                All Stations
              </button>
            )}
            {stations.map(station => (
              <button
                key={station.id}
                onClick={() => {
                  onSelect(station.id);
                  setIsOpen(false);
                }}
                className={cn(
                  'flex w-full flex-col items-start px-4 py-2 text-sm hover:bg-gray-100',
                  selectedStationId === station.id && 'bg-gray-50 font-medium'
                )}
              >
                <span>{station.name}</span>
                <span className="text-xs text-gray-500">{station.address}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

interface ChefSelectorProps {
  chefs: Chef[];
  selectedChefId: string | null;
  onSelect: (chefId: string | null) => void;
  showAll?: boolean;
}

function ChefSelector({
  chefs,
  selectedChefId,
  onSelect,
  showAll = false,
}: ChefSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedChef = chefs.find(c => c.id === selectedChefId);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50"
      >
        <ChefHat className="h-4 w-4 text-gray-500" />
        {selectedChef ? selectedChef.name : 'All Chefs'}
        <ChevronDown className="h-4 w-4 text-gray-400" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute left-0 top-full z-20 mt-1 w-64 max-h-72 overflow-y-auto rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
            {showAll && (
              <button
                onClick={() => {
                  onSelect(null);
                  setIsOpen(false);
                }}
                className={cn(
                  'flex w-full items-center px-4 py-2 text-sm hover:bg-gray-100',
                  !selectedChefId && 'bg-gray-50 font-medium'
                )}
              >
                All Chefs
              </button>
            )}
            {chefs.map(chef => (
              <button
                key={chef.id}
                onClick={() => {
                  onSelect(chef.id);
                  setIsOpen(false);
                }}
                className={cn(
                  'flex w-full flex-col items-start px-4 py-2 text-sm hover:bg-gray-100',
                  selectedChefId === chef.id && 'bg-gray-50 font-medium'
                )}
              >
                <span>{chef.name}</span>
                <span className="text-xs text-gray-500">
                  {chef.station_name || chef.email}
                </span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

interface AvailabilitySlotProps {
  slot: TimeSlot;
  isAvailable: boolean;
  isOverride: boolean;
  hasBooking?: boolean;
  onClick?: () => void;
  compact?: boolean;
}

function AvailabilitySlot({
  slot,
  isAvailable,
  isOverride,
  hasBooking,
  onClick,
  compact,
}: AvailabilitySlotProps) {
  return (
    <button
      onClick={onClick}
      disabled={hasBooking}
      className={cn(
        'flex items-center justify-center rounded text-xs font-medium transition-colors',
        compact ? 'h-6 w-full px-1' : 'h-8 w-full px-2',
        hasBooking
          ? 'cursor-not-allowed bg-blue-100 text-blue-700'
          : isAvailable
            ? isOverride
              ? 'bg-green-200 text-green-800 hover:bg-green-300 border border-green-400'
              : 'bg-green-100 text-green-700 hover:bg-green-200'
            : isOverride
              ? 'bg-red-100 text-red-600 hover:bg-red-200 border border-red-300'
              : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
      )}
      title={
        hasBooking
          ? 'Slot is booked'
          : isOverride
            ? isAvailable
              ? 'Available (override)'
              : 'Unavailable (override)'
            : isAvailable
              ? 'Available (template)'
              : 'Unavailable'
      }
    >
      {compact ? slot.time.split(':')[0] : slot.label}
      {isOverride && <span className="ml-1">*</span>}
    </button>
  );
}

interface DayCellProps {
  date: Date;
  chef: Chef;
  weeklyTemplate: WeeklyTemplate | undefined;
  dateOverride: DateOverride | undefined;
  isCurrentMonth: boolean;
  onToggleSlot: (date: Date, slotId: string) => void;
  onAddOverride: (date: Date) => void;
  compact?: boolean;
  getBookingsForSlot: (date: Date, slotId: string) => Booking[];
  onBookingClick?: (booking: Booking) => void;
}

function DayCell({
  date,
  chef,
  weeklyTemplate,
  dateOverride,
  isCurrentMonth,
  onToggleSlot,
  onAddOverride,
  compact,
  getBookingsForSlot,
  onBookingClick,
}: DayCellProps) {
  // Determine availability for each slot
  const getSlotAvailability = (
    slotId: string
  ): { isAvailable: boolean; isOverride: boolean } => {
    // Check override first
    if (dateOverride) {
      return {
        isAvailable:
          dateOverride.is_available &&
          dateOverride.available_slots.includes(slotId),
        isOverride: true,
      };
    }

    // Fall back to weekly template
    if (weeklyTemplate && weeklyTemplate.is_available) {
      return {
        isAvailable: weeklyTemplate.available_slots.includes(slotId),
        isOverride: false,
      };
    }

    return { isAvailable: false, isOverride: false };
  };

  const hasAnyOverride = !!dateOverride;
  const dayOfWeekLabel = DAYS_OF_WEEK[date.getDay()];

  return (
    <div
      className={cn(
        'min-h-24 border border-gray-100 p-1',
        !isCurrentMonth && 'bg-gray-50 opacity-60',
        isToday(date) && 'ring-2 ring-amber-400 ring-inset'
      )}
    >
      <div className="flex items-center justify-between mb-1">
        <span
          className={cn(
            'text-xs font-medium',
            isToday(date) ? 'text-amber-600' : 'text-gray-700'
          )}
        >
          {date.getDate()}
        </span>
        {hasAnyOverride && (
          <span className="text-xs text-orange-500" title="Has date override">
            ⚡
          </span>
        )}
      </div>

      <div className="space-y-0.5">
        {STANDARD_TIME_SLOTS.map(slot => {
          const { isAvailable, isOverride } = getSlotAvailability(slot.id);
          const slotBookings = getBookingsForSlot(date, slot.id);
          const hasBooking = slotBookings.length > 0;
          const firstBooking = slotBookings[0];

          return (
            <div key={slot.id} className="relative">
              <AvailabilitySlot
                slot={slot}
                isAvailable={isAvailable}
                isOverride={isOverride}
                hasBooking={hasBooking}
                onClick={() =>
                  hasBooking && onBookingClick
                    ? onBookingClick(firstBooking)
                    : onToggleSlot(date, slot.id)
                }
                compact={compact}
              />
              {hasBooking && !compact && (
                <div
                  className="absolute inset-0 flex items-center justify-center cursor-pointer"
                  onClick={() => onBookingClick?.(firstBooking)}
                  title={`${firstBooking.customer_name || 'Booking'} - ${firstBooking.chef_name ? `Chef: ${firstBooking.chef_name}` : 'No chef assigned'}`}
                >
                  <span className="text-[8px] text-white font-medium truncate px-0.5 drop-shadow-sm">
                    {slotBookings.length > 1
                      ? `${slotBookings.length} bookings`
                      : firstBooking.customer_name?.split(' ')[0] || 'Booked'}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface WeeklyTemplateEditorProps {
  chef: Chef;
  templates: WeeklyTemplate[];
  onSave: (templates: WeeklyTemplate[]) => void;
  onClose: () => void;
}

function WeeklyTemplateEditor({
  chef,
  templates,
  onSave,
  onClose,
}: WeeklyTemplateEditorProps) {
  const [editableTemplates, setEditableTemplates] = useState<WeeklyTemplate[]>(
    () => {
      // Initialize with all 7 days
      return DAYS_OF_WEEK.map((_, dayIndex) => {
        const existing = templates.find(t => t.day_of_week === dayIndex);
        return (
          existing || {
            id: `new-${chef.id}-${dayIndex}`,
            chef_id: chef.id,
            day_of_week: dayIndex,
            available_slots: [],
            is_available: false,
          }
        );
      });
    }
  );

  const toggleSlot = (dayOfWeek: number, slotId: string) => {
    setEditableTemplates(prev =>
      prev.map(template => {
        if (template.day_of_week !== dayOfWeek) return template;

        const hasSlot = template.available_slots.includes(slotId);
        const newSlots = hasSlot
          ? template.available_slots.filter(s => s !== slotId)
          : [...template.available_slots, slotId];

        return {
          ...template,
          available_slots: newSlots,
          is_available: newSlots.length > 0,
        };
      })
    );
  };

  const toggleDay = (dayOfWeek: number, enabled: boolean) => {
    setEditableTemplates(prev =>
      prev.map(template => {
        if (template.day_of_week !== dayOfWeek) return template;
        return {
          ...template,
          is_available: enabled,
          available_slots: enabled
            ? ['slot-12', 'slot-15', 'slot-18', 'slot-21']
            : [],
        };
      })
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">
              Weekly Template for {chef.name}
            </h2>
            <p className="text-sm text-gray-500">
              Set default weekly availability
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          {editableTemplates.map(template => {
            const day = DAYS_OF_WEEK_FULL[template.day_of_week];
            return (
              <div
                key={template.day_of_week}
                className="flex items-center gap-4 rounded-lg border p-3"
              >
                <div className="w-24">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={template.is_available}
                      onChange={e =>
                        toggleDay(template.day_of_week, e.target.checked)
                      }
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span className="text-sm font-medium">{day}</span>
                  </label>
                </div>
                <div className="flex flex-1 gap-2">
                  {STANDARD_TIME_SLOTS.map(slot => (
                    <button
                      key={slot.id}
                      onClick={() => toggleSlot(template.day_of_week, slot.id)}
                      disabled={!template.is_available}
                      className={cn(
                        'flex-1 rounded px-2 py-1 text-xs font-medium transition-colors',
                        !template.is_available
                          ? 'cursor-not-allowed bg-gray-100 text-gray-400'
                          : template.available_slots.includes(slot.id)
                            ? 'bg-green-100 text-green-700 hover:bg-green-200'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      )}
                    >
                      {slot.label}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => onSave(editableTemplates)}>
            <Save className="mr-2 h-4 w-4" />
            Save Template
          </Button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Booking Assignment Modal
// =============================================================================

interface BookingAssignmentModalProps {
  booking: Booking;
  chefs: Chef[];
  onClose: () => void;
  onAssign: (bookingId: string, chefId: string | null) => Promise<void>;
}

function BookingAssignmentModal({
  booking,
  chefs,
  onClose,
  onAssign,
}: BookingAssignmentModalProps) {
  const [selectedChef, setSelectedChef] = useState<string>(
    booking.chef_id || ''
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Find current chef name
  const currentChef = chefs.find(c => c.id === booking.chef_id);
  const selectedChefData = chefs.find(c => c.id === selectedChef);

  // Format booking date/time for display
  const bookingDate = booking.date
    ? new Date(booking.date).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Unknown date';

  const bookingTime = booking.time
    ? new Date(`2000-01-01T${booking.time}`).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      })
    : 'Unknown time';

  const handleAssign = async () => {
    if (!selectedChef) {
      setError('Please select a chef');
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      await onAssign(booking.id, selectedChef);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign chef');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUnassign = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await onAssign(booking.id, null);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unassign chef');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Assign Chef to Booking
            </h2>
            <p className="text-sm text-gray-500">
              {bookingDate} at {bookingTime}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isSubmitting}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Booking Details */}
        <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="font-medium text-gray-600">Customer:</span>
              <p className="text-gray-900">
                {booking.customer_name || 'Unknown'}
              </p>
            </div>
            <div>
              <span className="font-medium text-gray-600">Guests:</span>
              <p className="text-gray-900">
                {booking.guests ||
                  (booking.party_adults || 0) + (booking.party_kids || 0) ||
                  '-'}
              </p>
            </div>
            <div>
              <span className="font-medium text-gray-600">Status:</span>
              <span
                className={`ml-1 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                  booking.status === 'confirmed'
                    ? 'bg-green-100 text-green-700'
                    : booking.status === 'pending'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-gray-100 text-gray-700'
                }`}
              >
                {booking.status || 'Unknown'}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-600">Current Chef:</span>
              <p className="text-gray-900">
                {currentChef ? currentChef.name : 'Unassigned'}
              </p>
            </div>
          </div>
          {booking.location_address && (
            <div className="mt-3 border-t border-gray-200 pt-3 text-sm">
              <span className="font-medium text-gray-600">Location:</span>
              <p className="text-gray-900">{booking.location_address}</p>
            </div>
          )}
        </div>

        {/* Chef Selector */}
        <div className="mb-4">
          <label
            htmlFor="chef-select"
            className="mb-2 block text-sm font-medium text-gray-700"
          >
            Select Chef
          </label>
          <select
            id="chef-select"
            value={selectedChef}
            onChange={e => setSelectedChef(e.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
            disabled={isSubmitting}
          >
            <option value="">-- Select a chef --</option>
            {chefs.map(chef => (
              <option key={chef.id} value={chef.id}>
                {chef.name}
                {chef.id === booking.chef_id ? ' (currently assigned)' : ''}
              </option>
            ))}
          </select>
          {selectedChefData && selectedChef !== booking.chef_id && (
            <p className="mt-2 text-xs text-gray-500">
              Chef {selectedChefData.name} will receive a calendar invite for
              this booking.
            </p>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between gap-3">
          <div>
            {booking.chef_id && (
              <Button
                variant="outline"
                onClick={handleUnassign}
                disabled={isSubmitting}
                className="text-red-600 hover:bg-red-50 hover:text-red-700"
              >
                {isSubmitting ? 'Unassigning...' : 'Unassign Chef'}
              </Button>
            )}
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              onClick={handleAssign}
              disabled={isSubmitting || !selectedChef}
            >
              {isSubmitting
                ? 'Assigning...'
                : selectedChef === booking.chef_id
                  ? 'Keep Current'
                  : 'Assign Chef'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function SchedulePage() {
  const { stationContext, isSuperAdmin } = useAuth();

  // State
  const [viewMode, setViewMode] = useState<ViewMode>('week');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedStationId, setSelectedStationId] = useState<string | null>(
    null
  );
  const [selectedChefId, setSelectedChefId] = useState<string | null>(null);
  const [weeklyTemplates, setWeeklyTemplates] = useState<WeeklyTemplate[]>(
    MOCK_WEEKLY_TEMPLATES
  );
  const [dateOverrides, setDateOverrides] =
    useState<DateOverride[]>(MOCK_DATE_OVERRIDES);
  const [editingTemplate, setEditingTemplate] = useState<Chef | null>(null);
  const [loading, setLoading] = useState(false);

  // Chef data from API (replaces MOCK_CHEFS)
  const [chefs, setChefs] = useState<Chef[]>([]);
  const [chefsLoading, setChefsLoading] = useState(true);
  const [chefsError, setChefsError] = useState<string | null>(null);

  // Booking data from API
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [showBookingModal, setShowBookingModal] = useState(false);

  // Role-based filtering
  const userRole = stationContext?.role;
  const userStationId = stationContext?.station_id; // singular station
  const userChefId = stationContext?.chef_id;

  // Fetch chefs from API on mount
  useEffect(() => {
    async function fetchChefs() {
      setChefsLoading(true);
      setChefsError(null);
      try {
        const response = await chefService.getStationChefs();
        if (response.success && response.data) {
          // Map API Chef response to local Chef interface
          const mappedChefs: Chef[] = response.data.chefs.map(chef => ({
            id: chef.id,
            name: chef.name,
            email: chef.email || '',
            phone: chef.phone,
            station_id: stationContext?.station_id || '', // Use current station context
            station_name: stationContext?.station_name,
            avatar_url: chef.avatar_url,
          }));
          setChefs(mappedChefs);
        } else {
          setChefsError('Failed to load chefs');
        }
      } catch (error) {
        console.error('Error fetching chefs:', error);
        setChefsError('Failed to load chefs');
      } finally {
        setChefsLoading(false);
      }
    }

    fetchChefs();
  }, [stationContext?.station_id, stationContext?.station_name]);

  // Create a map for quick booking lookup by date and slot
  const bookingsMap = useMemo(() => {
    const map = new Map<string, Booking[]>();

    bookings.forEach(booking => {
      if (!booking.date) return;

      // Parse booking date
      const dateStr = booking.date.split('T')[0]; // Extract YYYY-MM-DD

      // Determine slot from booking time
      let slotId = '';
      if (booking.time) {
        const hour = parseInt(booking.time.split(':')[0], 10);
        if (hour >= 11 && hour <= 13) slotId = 'slot-12';
        else if (hour >= 14 && hour <= 16) slotId = 'slot-15';
        else if (hour >= 17 && hour <= 19) slotId = 'slot-18';
        else if (hour >= 20 && hour <= 22) slotId = 'slot-21';
      } else if (booking.slot) {
        slotId = booking.slot;
      }

      const key = `${dateStr}-${slotId}`;
      if (!map.has(key)) {
        map.set(key, []);
      }
      map.get(key)!.push(booking);
    });

    return map;
  }, [bookings]);

  // Helper to get bookings for a specific date and slot
  const getBookingsForSlot = useCallback(
    (date: Date, slotId: string): Booking[] => {
      const dateStr = formatDate(date);
      const key = `${dateStr}-${slotId}`;
      return bookingsMap.get(key) || [];
    },
    [bookingsMap]
  );

  // Handler for assigning/unassigning chef to booking
  const handleAssignChef = useCallback(
    async (bookingId: string, chefId: string | null) => {
      try {
        if (chefId) {
          // Assign chef
          const response = await bookingService.assignChef(bookingId, chefId);
          if (!response.success) {
            throw new Error(response.error || 'Failed to assign chef');
          }
          // Update local booking state
          setBookings(prev =>
            prev.map(b => (b.id === bookingId ? { ...b, chef_id: chefId } : b))
          );
        } else {
          // Unassign chef
          const response = await bookingService.unassignChef(bookingId);
          if (!response.success) {
            throw new Error(response.error || 'Failed to unassign chef');
          }
          // Update local booking state
          setBookings(prev =>
            prev.map(b =>
              b.id === bookingId ? { ...b, chef_id: undefined } : b
            )
          );
        }
      } catch (error) {
        console.error('Error assigning chef:', error);
        throw error;
      }
    },
    []
  );

  // Filter stations based on role
  const availableStations = useMemo(() => {
    if (isSuperAdmin()) return MOCK_STATIONS;
    if (userRole === 'STATION_MANAGER' || userRole === 'ADMIN') {
      return MOCK_STATIONS.filter(s => s.id === userStationId);
    }
    return [];
  }, [isSuperAdmin, userRole, userStationId]);

  // Filter chefs based on role and selected station
  const availableChefs = useMemo(() => {
    // Use chefs from API state (not MOCK_CHEFS)
    let filteredChefs = [...chefs];

    // If chef role, only show themselves
    if (userRole === 'CHEF' && userChefId) {
      return filteredChefs.filter(c => c.id === userChefId);
    }

    // Filter by station if not super admin
    if (!isSuperAdmin() && userStationId) {
      filteredChefs = filteredChefs.filter(c => c.station_id === userStationId);
    }

    // Filter by selected station
    if (selectedStationId) {
      filteredChefs = filteredChefs.filter(
        c => c.station_id === selectedStationId
      );
    }

    return filteredChefs;
  }, [
    chefs,
    isSuperAdmin,
    userRole,
    userChefId,
    userStationId,
    selectedStationId,
  ]);

  // Auto-select chef if user is a chef
  useEffect(() => {
    if (userRole === 'CHEF' && userChefId) {
      setSelectedChefId(userChefId);
    }
  }, [userRole, userChefId]);

  // Get dates based on view mode
  const displayDates = useMemo(() => {
    if (viewMode === 'week') {
      return getWeekDates(currentDate);
    }
    return getMonthDates(currentDate.getFullYear(), currentDate.getMonth());
  }, [viewMode, currentDate]);

  // Fetch bookings for the displayed date range
  useEffect(() => {
    async function fetchBookings() {
      if (!displayDates.length) return;

      setBookingsLoading(true);
      try {
        const dateFrom = formatDate(displayDates[0]);
        const dateTo = formatDate(displayDates[displayDates.length - 1]);

        const response = await bookingService.getBookings({
          dateFrom,
          dateTo,
          status: 'confirmed', // Only show confirmed bookings on calendar
          limit: 200, // Get all bookings for the range
        });

        if (response?.data?.items) {
          setBookings(response.data.items);
        }
      } catch (error) {
        console.error('Error fetching bookings:', error);
      } finally {
        setBookingsLoading(false);
      }
    }

    fetchBookings();
  }, [displayDates]);

  // Navigation handlers
  const goToPrevious = () => {
    const newDate = new Date(currentDate);
    if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() - 7);
    } else {
      newDate.setMonth(newDate.getMonth() - 1);
    }
    setCurrentDate(newDate);
  };

  const goToNext = () => {
    const newDate = new Date(currentDate);
    if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() + 7);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // Toggle slot availability (creates override)
  const handleToggleSlot = useCallback(
    (date: Date, slotId: string) => {
      const dateStr = formatDate(date);

      setDateOverrides(prev => {
        const existing = prev.find(
          o => o.chef_id === selectedChefId && o.date === dateStr
        );

        if (existing) {
          // Update existing override
          const hasSlot = existing.available_slots.includes(slotId);
          const newSlots = hasSlot
            ? existing.available_slots.filter(s => s !== slotId)
            : [...existing.available_slots, slotId];

          return prev.map(o =>
            o.id === existing.id
              ? {
                  ...o,
                  available_slots: newSlots,
                  is_available: newSlots.length > 0,
                }
              : o
          );
        }

        // Create new override
        const newOverride: DateOverride = {
          id: `do-${Date.now()}`,
          chef_id: selectedChefId!,
          date: dateStr,
          available_slots: [slotId],
          is_available: true,
          reason: 'Manual adjustment',
        };

        return [...prev, newOverride];
      });
    },
    [selectedChefId]
  );

  // Save weekly template
  const handleSaveTemplate = (templates: WeeklyTemplate[]) => {
    setWeeklyTemplates(prev => {
      const otherChefTemplates = prev.filter(
        t => t.chef_id !== editingTemplate?.id
      );
      return [...otherChefTemplates, ...templates];
    });
    setEditingTemplate(null);
    // TODO: API call to save templates
  };

  // Title for current period
  const periodTitle = useMemo(() => {
    if (viewMode === 'week') {
      const start = displayDates[0];
      const end = displayDates[6];
      return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    }
    return currentDate.toLocaleDateString('en-US', {
      month: 'long',
      year: 'numeric',
    });
  }, [viewMode, displayDates, currentDate]);

  // Selected chef for display
  const selectedChef = availableChefs.find(c => c.id === selectedChefId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {userRole === 'CHEF' ? 'My Availability' : 'Chef Availability'}
          </h1>
          <p className="text-gray-600">
            {userRole === 'CHEF'
              ? 'Manage your weekly schedule and availability'
              : 'Manage chef schedules and availability across stations'}
          </p>
        </div>

        {selectedChef && userRole !== 'CHEF' && (
          <Button onClick={() => setEditingTemplate(selectedChef)}>
            <Edit2 className="mr-2 h-4 w-4" />
            Edit Weekly Template
          </Button>
        )}
      </div>

      {/* Filters Row */}
      <div className="flex flex-wrap items-center gap-4 rounded-lg bg-white p-4 shadow-sm border border-gray-200">
        {/* Station Filter - For SUPER_ADMIN, or STATION_MANAGER/ADMIN with multiple stations */}
        {(isSuperAdmin() ||
          ((userRole === 'STATION_MANAGER' || userRole === 'ADMIN') &&
            (stationContext?.station_count ?? 0) > 1)) && (
          <StationSelector
            stations={availableStations}
            selectedStationId={selectedStationId}
            onSelect={setSelectedStationId}
            showAll={isSuperAdmin()}
          />
        )}

        {/* Chef Filter - Not shown for CHEF role */}
        {userRole !== 'CHEF' &&
          (chefsLoading ? (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600"></div>
              Loading chefs...
            </div>
          ) : chefsError ? (
            <div className="text-sm text-red-500">{chefsError}</div>
          ) : (
            <ChefSelector
              chefs={availableChefs}
              selectedChefId={selectedChefId}
              onSelect={setSelectedChefId}
              showAll={availableChefs.length > 1}
            />
          ))}

        {/* View Mode Toggle */}
        <div className="flex rounded-lg border border-gray-300 p-1">
          <button
            onClick={() => setViewMode('week')}
            className={cn(
              'rounded px-3 py-1.5 text-sm font-medium transition-colors',
              viewMode === 'week'
                ? 'bg-gray-900 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            )}
          >
            Week
          </button>
          <button
            onClick={() => setViewMode('month')}
            className={cn(
              'rounded px-3 py-1.5 text-sm font-medium transition-colors',
              viewMode === 'month'
                ? 'bg-gray-900 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            )}
          >
            Month
          </button>
        </div>

        {/* Navigation */}
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={goToPrevious}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={goToToday}>
            Today
          </Button>
          <Button variant="outline" size="sm" onClick={goToNext}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <span className="font-medium text-gray-900">{periodTitle}</span>
      </div>

      {/* No Chef Selected Warning */}
      {!selectedChefId && userRole !== 'CHEF' && (
        <div className="flex items-center gap-3 rounded-lg bg-amber-50 border border-amber-200 p-4">
          <AlertCircle className="h-5 w-5 text-amber-600" />
          <p className="text-amber-800">
            Please select a chef to view or edit their availability.
          </p>
        </div>
      )}

      {/* Calendar Grid */}
      {selectedChefId && (
        <div className="rounded-lg bg-white shadow-sm border border-gray-200 overflow-hidden">
          {/* Day Headers */}
          <div className="grid grid-cols-7 border-b border-gray-200 bg-gray-50">
            {DAYS_OF_WEEK.map((day, i) => (
              <div key={day} className="p-2 text-center">
                <span className="text-sm font-medium text-gray-600">{day}</span>
                {viewMode === 'week' && (
                  <div
                    className={cn(
                      'text-lg font-semibold',
                      isToday(displayDates[i])
                        ? 'text-amber-600'
                        : 'text-gray-900'
                    )}
                  >
                    {displayDates[i].getDate()}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Calendar Body */}
          <div
            className={cn(
              'grid grid-cols-7',
              viewMode === 'month' && 'min-h-[600px]'
            )}
          >
            {displayDates.map((date, index) => {
              const dateStr = formatDate(date);
              const template = weeklyTemplates.find(
                t =>
                  t.chef_id === selectedChefId &&
                  t.day_of_week === date.getDay()
              );
              const override = dateOverrides.find(
                o => o.chef_id === selectedChefId && o.date === dateStr
              );

              return (
                <DayCell
                  key={dateStr}
                  date={date}
                  chef={selectedChef!}
                  weeklyTemplate={template}
                  dateOverride={override}
                  isCurrentMonth={isSameMonth(date, currentDate)}
                  onToggleSlot={handleToggleSlot}
                  onAddOverride={() => {}}
                  compact={viewMode === 'month'}
                  getBookingsForSlot={getBookingsForSlot}
                  onBookingClick={booking => {
                    setSelectedBooking(booking);
                    setShowBookingModal(true);
                  }}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 rounded-lg bg-gray-50 p-4 text-sm">
        <span className="font-medium text-gray-700">Legend:</span>
        <div className="flex items-center gap-2">
          <div className="h-4 w-8 rounded bg-green-100"></div>
          <span className="text-gray-600">Available (template)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-4 w-8 rounded bg-green-200 border border-green-400"></div>
          <span className="text-gray-600">Available (override)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-4 w-8 rounded bg-gray-100"></div>
          <span className="text-gray-600">Unavailable</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-4 w-8 rounded bg-red-100 border border-red-300"></div>
          <span className="text-gray-600">Unavailable (override)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-4 w-8 rounded bg-blue-100"></div>
          <span className="text-gray-600">Booked</span>
        </div>
      </div>

      {/* Selected Chef Info */}
      {selectedChef && (
        <div className="rounded-lg bg-white p-4 shadow-sm border border-gray-200">
          <h3 className="font-semibold text-gray-900">Selected Chef</h3>
          <div className="mt-2 flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100">
              <ChefHat className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">{selectedChef.name}</p>
              <p className="text-sm text-gray-500">
                {selectedChef.station_name}
              </p>
              <p className="text-sm text-gray-500">{selectedChef.email}</p>
            </div>
          </div>
        </div>
      )}

      {/* Weekly Template Editor Modal */}
      {editingTemplate && (
        <WeeklyTemplateEditor
          chef={editingTemplate}
          templates={weeklyTemplates.filter(
            t => t.chef_id === editingTemplate.id
          )}
          onSave={handleSaveTemplate}
          onClose={() => setEditingTemplate(null)}
        />
      )}

      {/* Booking Assignment Modal */}
      {showBookingModal && selectedBooking && (
        <BookingAssignmentModal
          booking={selectedBooking}
          chefs={availableChefs}
          onAssign={handleAssignChef}
          onClose={() => {
            setShowBookingModal(false);
            setSelectedBooking(null);
          }}
        />
      )}
    </div>
  );
}
