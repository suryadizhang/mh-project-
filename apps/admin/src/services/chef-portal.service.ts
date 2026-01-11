/**
 * Chef Portal API Service
 *
 * Handles all backend communication for chef self-service operations.
 * Uses the unified API client from @/lib/api.
 *
 * Endpoints:
 * - Chef Self-Service: /api/v1/chef-portal/me/*
 * - Station Manager: /api/v1/chef-portal/station/*
 *
 * See: routers/v1/chef_portal.py for backend implementation
 *
 * Note: All functions return ApiResponse<T> wrapper from the api client.
 * Consumers should check response.success and access response.data.
 */

import { api, ApiResponse } from '@/lib/api';
import type {
  ChefProfile,
  ChefAvailabilitySlot,
  ChefAvailabilityCreate,
  ChefAvailabilityUpdate,
  ChefWeeklyAvailability,
  BulkAvailabilityUpdate,
  TimeOffRequest,
  TimeOffRequestCreate,
  TimeOffRequestList,
  TimeOffApprovalRequest,
  StationChefList,
} from '@/types/chef-portal';

// ============================================================================
// Chef Self-Service Endpoints (CHEF role)
// ============================================================================

/**
 * Get current chef's profile.
 * GET /api/v1/chef-portal/me
 */
export async function getMyChefProfile(): Promise<ApiResponse<ChefProfile>> {
  return api.get<ChefProfile>('/api/v1/chef-portal/me');
}

/**
 * Get current chef's weekly availability.
 * GET /api/v1/chef-portal/me/availability
 */
export async function getMyAvailability(): Promise<
  ApiResponse<ChefWeeklyAvailability>
> {
  return api.get<ChefWeeklyAvailability>('/api/v1/chef-portal/me/availability');
}

/**
 * Add a single availability slot.
 * POST /api/v1/chef-portal/me/availability
 */
export async function addAvailabilitySlot(
  slot: ChefAvailabilityCreate
): Promise<ApiResponse<ChefAvailabilitySlot>> {
  return api.post<ChefAvailabilitySlot>(
    '/api/v1/chef-portal/me/availability',
    slot as unknown as Record<string, unknown>
  );
}

/**
 * Update an existing availability slot.
 * PUT /api/v1/chef-portal/me/availability/{slot_id}
 */
export async function updateAvailabilitySlot(
  slotId: string,
  update: ChefAvailabilityUpdate
): Promise<ApiResponse<ChefAvailabilitySlot>> {
  return api.put<ChefAvailabilitySlot>(
    `/api/v1/chef-portal/me/availability/${slotId}`,
    update as unknown as Record<string, unknown>
  );
}

/**
 * Delete an availability slot.
 * DELETE /api/v1/chef-portal/me/availability/{slot_id}
 */
export async function deleteAvailabilitySlot(
  slotId: string
): Promise<ApiResponse<void>> {
  return api.delete<void>(`/api/v1/chef-portal/me/availability/${slotId}`);
}

/**
 * Bulk update weekly availability (replace or merge).
 * PUT /api/v1/chef-portal/me/availability/bulk
 */
export async function bulkUpdateAvailability(
  update: BulkAvailabilityUpdate
): Promise<ApiResponse<ChefWeeklyAvailability>> {
  return api.put<ChefWeeklyAvailability>(
    '/api/v1/chef-portal/me/availability/bulk',
    update as unknown as Record<string, unknown>
  );
}

/**
 * Get current chef's time-off requests.
 * GET /api/v1/chef-portal/me/timeoff
 */
export async function getMyTimeOffRequests(): Promise<
  ApiResponse<TimeOffRequestList>
> {
  return api.get<TimeOffRequestList>('/api/v1/chef-portal/me/timeoff');
}

/**
 * Submit a new time-off request.
 * POST /api/v1/chef-portal/me/timeoff
 */
export async function submitTimeOffRequest(
  request: TimeOffRequestCreate
): Promise<ApiResponse<TimeOffRequest>> {
  return api.post<TimeOffRequest>(
    '/api/v1/chef-portal/me/timeoff',
    request as unknown as Record<string, unknown>
  );
}

/**
 * Cancel a pending time-off request.
 * DELETE /api/v1/chef-portal/me/timeoff/{request_id}
 */
export async function cancelTimeOffRequest(
  requestId: string
): Promise<ApiResponse<void>> {
  return api.delete<void>(`/api/v1/chef-portal/me/timeoff/${requestId}`);
}

// ============================================================================
// Station Manager Endpoints (STATION_MANAGER / SUPER_ADMIN roles)
// ============================================================================

/**
 * List all chefs in the station.
 * GET /api/v1/chef-portal/station/chefs
 */
export async function getStationChefs(): Promise<ApiResponse<StationChefList>> {
  return api.get<StationChefList>('/api/v1/chef-portal/station/chefs');
}

/**
 * View a specific chef's availability (manager view).
 * GET /api/v1/chef-portal/station/chefs/{chef_id}/availability
 */
export async function getChefAvailability(
  chefId: string
): Promise<ApiResponse<ChefWeeklyAvailability>> {
  return api.get<ChefWeeklyAvailability>(
    `/api/v1/chef-portal/station/chefs/${chefId}/availability`
  );
}

/**
 * List pending time-off requests for all chefs in station.
 * GET /api/v1/chef-portal/station/timeoff/pending
 */
export async function getPendingTimeOffRequests(): Promise<
  ApiResponse<TimeOffRequestList>
> {
  return api.get<TimeOffRequestList>(
    '/api/v1/chef-portal/station/timeoff/pending'
  );
}

/**
 * Approve or deny a time-off request.
 * POST /api/v1/chef-portal/station/timeoff/{request_id}/approve
 */
export async function processTimeOffRequest(
  requestId: string,
  approval: TimeOffApprovalRequest
): Promise<ApiResponse<TimeOffRequest>> {
  return api.post<TimeOffRequest>(
    `/api/v1/chef-portal/station/timeoff/${requestId}/approve`,
    approval as unknown as Record<string, unknown>
  );
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Check if current user has chef portal access.
 * Returns the chef profile if accessible, null otherwise.
 */
export async function checkChefPortalAccess(): Promise<ChefProfile | null> {
  try {
    const response = await getMyChefProfile();
    if (response.success && response.data) {
      return response.data;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Get all availability for a specific day of the week.
 */
export function filterAvailabilityByDay(
  availability: ChefWeeklyAvailability,
  day: string
): ChefAvailabilitySlot[] {
  return availability.slots.filter(
    slot => slot.day_of_week.toLowerCase() === day.toLowerCase()
  );
}

/**
 * Format time string for display (HH:MM:SS -> HH:MM AM/PM).
 */
export function formatTimeForDisplay(timeStr: string): string {
  const [hours, minutes] = timeStr.split(':');
  const hour = parseInt(hours, 10);
  const ampm = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
}
