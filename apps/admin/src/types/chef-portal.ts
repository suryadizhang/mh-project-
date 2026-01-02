/**
 * Chef Portal Types
 *
 * TypeScript interfaces for chef self-service operations.
 * Mirrors backend Pydantic schemas from: schemas/chef_portal.py
 *
 * Authorization:
 * - Chefs can only modify their OWN availability
 * - Station managers can view/manage chefs in their station
 * - Super admins have full access
 *
 * See: routers/v1/chef_portal.py for API endpoints
 */

// ============================================================================
// Enums (matching database enums)
// ============================================================================

export type DayOfWeek =
  | 'monday'
  | 'tuesday'
  | 'wednesday'
  | 'thursday'
  | 'friday'
  | 'saturday'
  | 'sunday';

export type TimeOffType = 'vacation' | 'sick' | 'personal' | 'unpaid';

export type TimeOffStatus = 'pending' | 'approved' | 'denied' | 'cancelled';

export type ChefStatus = 'active' | 'inactive' | 'on_leave' | 'suspended';

// ============================================================================
// Chef Profile Types
// ============================================================================

export interface ChefProfile {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  specialty: string;
  status: ChefStatus;
  rating: number | null;
  total_bookings: number;
  completed_bookings: number;
  hired_date: string | null; // ISO date string
}

// ============================================================================
// Availability Types
// ============================================================================

export interface ChefAvailabilitySlot {
  id: string;
  chef_id: string;
  day_of_week: DayOfWeek;
  start_time: string; // HH:MM:SS format
  end_time: string; // HH:MM:SS format
  is_available: boolean;
  created_at: string; // ISO datetime string
}

export interface ChefAvailabilityCreate {
  day_of_week: DayOfWeek;
  start_time: string; // HH:MM:SS format
  end_time: string; // HH:MM:SS format
  is_available?: boolean;
}

export interface ChefAvailabilityUpdate {
  start_time?: string;
  end_time?: string;
  is_available?: boolean;
}

export interface ChefWeeklyAvailability {
  chef_id: string;
  chef_name: string;
  slots: ChefAvailabilitySlot[];
}

export interface BulkAvailabilityUpdate {
  slots: ChefAvailabilityCreate[];
  replace_existing?: boolean;
}

// ============================================================================
// Time-Off Types
// ============================================================================

export interface TimeOffRequest {
  id: string;
  chef_id: string;
  start_date: string; // ISO date string
  end_date: string; // ISO date string
  type: TimeOffType;
  reason: string | null;
  status: TimeOffStatus;
  approved_by: string | null;
  requested_at: string; // ISO datetime string
  processed_at: string | null; // ISO datetime string
}

export interface TimeOffRequestCreate {
  start_date: string; // YYYY-MM-DD format
  end_date: string; // YYYY-MM-DD format
  type: TimeOffType;
  reason?: string;
}

export interface TimeOffRequestList {
  requests: TimeOffRequest[];
  total: number;
}

export interface TimeOffApprovalRequest {
  status: 'approved' | 'denied';
  notes?: string;
}

// ============================================================================
// Station Manager View Types
// ============================================================================

export interface StationChefSummary {
  id: string;
  name: string;
  email: string;
  specialty: string;
  status: ChefStatus;
  rating: number | null;
  pending_timeoff_count: number;
}

export interface StationChefList {
  station_id: string;
  station_name: string;
  chefs: StationChefSummary[];
  total: number;
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export interface ChefPortalApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
