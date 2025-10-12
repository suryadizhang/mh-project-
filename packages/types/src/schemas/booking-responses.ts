import { z } from 'zod';
import { BookingSchema, BookingLocationSchema, MenuItemSchema } from '../index';

/**
 * Booking API Response Schemas
 * 
 * ✅ VERIFIED AGAINST ACTUAL FRONTEND USAGE (BookUs/page.tsx)
 * 
 * These schemas match the ACTUAL API responses currently used in production.
 * Future standardization to include timestamp/requestId fields planned for Phase 2B/2C.
 */

/**
 * Schema for GET /api/v1/bookings/booked-dates
 * Returns an array of dates that have bookings
 * 
 * ✅ ACTUAL RESPONSE FORMAT (verified from BookUs/page.tsx line 99-113):
 * {
 *   success?: boolean,  // Optional, may not always be present
 *   data: {
 *     bookedDates: ["2025-10-15T00:00:00.000Z", "2025-10-16T00:00:00.000Z", ...]
 *   }
 * }
 * 
 * Used by:
 * - apps/customer/src/hooks/useBooking.ts
 * - apps/customer/src/components/BookingFormContainer.tsx
 * - apps/customer/src/app/(pages)/BookUs/page.tsx (Line 99-113: result.data.bookedDates)
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     bookedDates: ["2025-10-15", "2025-10-16", "2025-10-22"]
 *   }
 * }
 */
export const BookedDatesResponseSchema = z.object({
  success: z
    .boolean()
    .optional()
    .describe('Request success status (optional, may not always be present)'),
  data: z.object({
    bookedDates: z
      .array(z.string())
      .describe('Array of booked dates (ISO date strings or YYYY-MM-DD format)'),
  }).describe('Response data containing booked dates'),
  error: z.string().optional().describe('Error message if success is false'),
});

export type BookedDatesResponse = z.infer<typeof BookedDatesResponseSchema>;

/**
 * Schema for GET /api/v1/bookings/availability
 * Returns available time slots for a specific date
 * 
 * ✅ ACTUAL RESPONSE FORMAT (verified from BookUs/page.tsx line 127-157):
 * {
 *   success: boolean,
 *   data: {
 *     timeSlots: [
 *       {
 *         time: "17:00",
 *         available: 5,
 *         maxCapacity: 10,
 *         booked: 5,
 *         isAvailable: true
 *       },
 *       ...
 *     ]
 *   }
 * }
 * 
 * Used by:
 * - apps/customer/src/hooks/useBooking.ts
 * - apps/customer/src/app/(pages)/BookUs/page.tsx (Line 127-157: response.data.timeSlots)
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     timeSlots: [
 *       { time: "17:00", available: 5, maxCapacity: 10, booked: 5, isAvailable: true },
 *       { time: "18:00", available: 3, maxCapacity: 10, booked: 7, isAvailable: true },
 *       { time: "19:00", available: 0, maxCapacity: 10, booked: 10, isAvailable: false }
 *     ]
 *   }
 * }
 */
export const AvailabilityResponseSchema = z.object({
  success: z.boolean().describe('Request success status'),
  data: z.object({
    timeSlots: z
      .array(
        z.object({
          time: z.string().describe('Time slot in HH:MM format (e.g., "17:00")'),
          available: z
            .number()
            .int()
            .nonnegative()
            .describe('Number of available slots at this time'),
          maxCapacity: z
            .number()
            .int()
            .positive()
            .describe('Maximum capacity for this time slot'),
          booked: z
            .number()
            .int()
            .nonnegative()
            .describe('Number of slots already booked'),
          isAvailable: z
            .boolean()
            .describe('Whether this time slot has any availability'),
        })
      )
      .describe('Array of time slot objects with availability information'),
  }).describe('Time slot availability data'),
  error: z.string().optional().describe('Error message if success is false'),
});

export type AvailabilityResponse = z.infer<typeof AvailabilityResponseSchema>;

/**
 * Schema for GET /api/v1/bookings/available-times (DEPRECATED/NOT USED)
 * 
 * ⚠️ NOTE: This schema is for backward compatibility only.
 * The actual endpoint used is GET /api/v1/bookings/availability
 * which returns timeSlots array (see AvailabilityResponseSchema)
 * 
 * @deprecated Use AvailabilityResponseSchema instead
 */
export const AvailableTimesResponseSchema = z.object({
  success: z.boolean().describe('Request success status'),
  data: z.object({
    date: z
      .string()
      .describe('The date for which times are being checked'),
    times: z
      .array(
        z.object({
          time: z.string().describe('Time in HH:MM format (24-hour)'),
          available: z.boolean().describe('Whether this time slot is available'),
          slot: z.string().optional().describe('Human-readable time slot'),
          reason: z.string().optional().describe('Reason if unavailable'),
        })
      )
      .describe('Array of available time slots'),
    count: z.number().int().nonnegative().optional().describe('Total time slots'),
  }).describe('Available times data'),
  error: z.string().optional().describe('Error message if success is false'),
});

export type AvailableTimesResponse = z.infer<typeof AvailableTimesResponseSchema>;

/**
 * Schema for POST /api/v1/bookings/availability
 * Creates a new booking and returns the booking details
 * 
 * ✅ ACTUAL RESPONSE FORMAT (verified from BookUs/page.tsx line 235-269):
 * {
 *   success: boolean,
 *   data: {
 *     bookingId: "book_abc123",
 *     code?: "SLOT_FULL" | "BOOKING_ERROR" | ...
 *   },
 *   error?: string
 * }
 * 
 * Used by:
 * - apps/customer/src/app/(pages)/BookUs/page.tsx (Line 235-269: response.data.bookingId, response.data.code)
 * 
 * @example Success:
 * {
 *   success: true,
 *   data: {
 *     bookingId: "book_abc123def456"
 *   }
 * }
 * 
 * @example Failure (slot full):
 * {
 *   success: false,
 *   data: {
 *     code: "SLOT_FULL"
 *   },
 *   error: "The selected time slot is no longer available"
 * }
 */
export const BookingSubmitResponseSchema = z.object({
  success: z.boolean().describe('Request success status'),
  data: z
    .object({
      bookingId: z
        .string()
        .optional()
        .describe('Created booking ID (present on success)'),
      code: z
        .string()
        .optional()
        .describe('Error code for specific failure scenarios (e.g., "SLOT_FULL", "BOOKING_ERROR")'),
    })
    .optional()
    .describe('Booking submission data'),
  error: z.string().optional().describe('Error message if success is false'),
});

export type BookingSubmitResponse = z.infer<typeof BookingSubmitResponseSchema>;

/**
 * Schema for GET /api/v1/bookings (list all bookings)
 * Returns a paginated list of bookings for the authenticated user
 * 
 * ⚠️ NOTE: This schema is for FUTURE USE. Not currently implemented in frontend.
 * Designed based on REST best practices for when booking list functionality is added.
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     items: [
 *       { id: "...", eventDate: "2025-10-15T00:00:00.000Z", status: "confirmed", ... },
 *       { id: "...", eventDate: "2025-10-20T00:00:00.000Z", status: "pending", ... }
 *     ],
 *     total: 15,
 *     page: 1,
 *     pageSize: 10,
 *     totalPages: 2
 *   }
 * }
 */
export const BookingListResponseSchema = z.object({
  success: z.boolean().describe('Request success status'),
  data: z.object({
    items: z
      .array(BookingSchema)
      .describe('Array of booking objects for the current page'),
    total: z
      .number()
      .int()
      .nonnegative()
      .describe('Total number of bookings across all pages'),
    page: z
      .number()
      .int()
      .positive()
      .describe('Current page number (1-indexed)'),
    pageSize: z
      .number()
      .int()
      .positive()
      .max(100)
      .describe('Number of items per page'),
    totalPages: z
      .number()
      .int()
      .nonnegative()
      .describe('Total number of pages available'),
    hasNext: z
      .boolean()
      .optional()
      .describe('Optional: Whether there is a next page'),
    hasPrevious: z
      .boolean()
      .optional()
      .describe('Optional: Whether there is a previous page'),
  }).describe('Paginated booking list data'),
  error: z.string().optional().describe('Error message if success is false'),
});

export type BookingListResponse = z.infer<typeof BookingListResponseSchema>;

/**
 * Schema for GET /api/v1/bookings/:id (get single booking)
 * Returns details for a specific booking
 * 
 * ⚠️ NOTE: This schema is for FUTURE USE. Not currently implemented in frontend.
 * Designed based on REST best practices for when booking detail functionality is added.
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     booking: { id: "...", eventDate: "2025-10-15T00:00:00.000Z", ... },
 *     confirmationCode: "MHBC-2025-001234",
 *     canModify: true,
 *     canCancel: true,
 *     modifications: []
 *   }
 * }
 */
export const BookingDetailResponseSchema = z.object({
  success: z.boolean().describe('Request success status'),
  data: z.object({
    booking: BookingSchema.describe('The booking object'),
    confirmationCode: z
      .string()
      .min(1)
      .max(50)
      .describe('Confirmation code for the booking'),
    canModify: z
      .boolean()
      .describe('Whether the booking can be modified'),
    canCancel: z
      .boolean()
      .describe('Whether the booking can be cancelled'),
    modifications: z
      .array(
        z.object({
          modifiedAt: z
            .string()
            .datetime()
            .describe('Timestamp of modification'),
          modifiedBy: z
            .string()
            .describe('User who made the modification'),
          changes: z
            .record(z.any())
            .describe('Object containing changed fields'),
        })
      )
      .optional()
      .describe('Optional: History of modifications'),
  }).describe('Booking detail data'),
  error: z.string().optional().describe('Error message if success is false'),
});

export type BookingDetailResponse = z.infer<typeof BookingDetailResponseSchema>;

/**
 * Export all schemas for easy import
 */
export const BookingResponseSchemas = {
  BookedDates: BookedDatesResponseSchema,
  Availability: AvailabilityResponseSchema,
  AvailableTimes: AvailableTimesResponseSchema,
  BookingSubmit: BookingSubmitResponseSchema,
  BookingList: BookingListResponseSchema,
  BookingDetail: BookingDetailResponseSchema,
} as const;
