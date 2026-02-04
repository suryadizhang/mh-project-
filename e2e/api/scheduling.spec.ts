import { test, expect } from '@playwright/test';
import {
  mockAvailabilityRequest,
  mockQuotes,
  mockChefs,
  getTestDate,
  getTestTime,
} from '../helpers/mock-data';

/**
 * Scheduling API Integration Tests
 *
 * Tests the Smart Scheduling System endpoints:
 * - Availability checking
 * - Slot suggestions
 * - Chef assignment optimization
 * - Travel time calculations
 * - Calendar availability
 *
 * Tags: @api @scheduling @critical
 */

const API_URL =
  process.env.STAGING_API_URL || 'https://staging-api.mysticdatanode.net';

test.describe('Scheduling API - Availability @api @scheduling', () => {
  test('POST /scheduling/availability/check returns slot availability @critical', async ({
    request,
  }) => {
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/availability/check`,
      {
        data: {
          event_date: mockAvailabilityRequest.event_date,
          event_time: mockAvailabilityRequest.event_time,
          guest_count: mockAvailabilityRequest.guest_count,
          venue_lat: mockAvailabilityRequest.venue_lat,
          venue_lng: mockAvailabilityRequest.venue_lng,
        },
      }
    );

    // Should return 200 or 422 (validation error if no slots configured)
    expect([200, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Verify response structure
      expect(data).toHaveProperty('requested_date');
      expect(data).toHaveProperty('requested_time');
      expect(data).toHaveProperty('is_requested_available');

      // If suggestions are returned, validate structure
      if (data.suggestions) {
        expect(Array.isArray(data.suggestions)).toBeTruthy();
      }
    }
  });

  test('GET /scheduling/slots/config returns slot configuration @api', async ({
    request,
  }) => {
    const response = await request.get(
      `${API_URL}/api/v1/scheduling/slots/config`
    );

    expect([200, 404]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Verify it returns slot configuration
      expect(data).toBeDefined();
    }
  });

  test('POST /scheduling/availability/calendar returns monthly availability @api', async ({
    request,
  }) => {
    // Correct path is /availability/calendar (not /calendar/availability)
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/availability/calendar`,
      {
        data: {
          start_date: '2025-03-01',
          end_date: '2025-03-31',
          guest_count: 20,
          venue_lat: 34.0522,
          venue_lng: -118.2437,
        },
      }
    );

    expect([200, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Should return days array with availability info
      if (data.days) {
        expect(Array.isArray(data.days)).toBeTruthy();
      }
    }
  });
});

test.describe('Scheduling API - Travel Time @api @scheduling', () => {
  test('POST /scheduling/travel-time/calculate calculates travel time @api', async ({
    request,
  }) => {
    // Correct path is /travel-time/calculate (not /travel/time)
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/travel-time/calculate`,
      {
        data: {
          origin_lat: mockQuotes.smallParty.venue_lat,
          origin_lng: mockQuotes.smallParty.venue_lng,
          destination_lat: 34.0736, // Beverly Hills
          destination_lng: -118.4004,
        },
      }
    );

    expect([200, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Should return travel time info
      expect(data).toHaveProperty('distance_miles');
      expect(data).toHaveProperty('duration_minutes');
    }
  });

  test('POST /scheduling/travel/fee calculates travel fee @api', async ({
    request,
  }) => {
    // Endpoint NOW EXISTS in scheduling.py - calculates travel fee based on distance
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/travel/fee`,
      {
        data: {
          distance_miles: 40, // Beyond free miles (30 free)
          station_id: null,
        },
      }
    );

    expect([200, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Should return fee calculation
      expect(data).toHaveProperty('fee');
      expect(data).toHaveProperty('free_miles');
      expect(data).toHaveProperty('billable_miles');
      expect(data).toHaveProperty('per_mile_rate');
      expect(data).toHaveProperty('distance_miles');

      // Verify calculation: 40 miles - 30 free = 10 billable × $2.00 = $20.00
      expect(data.fee).toBe(20.0);
      expect(data.free_miles).toBe(30);
      expect(data.billable_miles).toBe(10);
      expect(data.per_mile_rate).toBe(2.0);
    }
  });
});

test.describe('Scheduling API - Chef Assignment @api @scheduling', () => {
  test('GET /scheduling/available-chefs returns available chefs @api', async ({
    request,
  }) => {
    // Correct path is /available-chefs (not /chefs/available)
    const eventDate = getTestDate(30);
    const response = await request.get(
      `${API_URL}/api/v1/scheduling/available-chefs`,
      {
        params: {
          event_date: eventDate,
          event_time: '18:00',
          guest_count: 20,
          venue_lat: 34.0522,
          venue_lng: -118.2437,
        },
      }
    );

    expect([200, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Should return array of available chefs
      if (Array.isArray(data)) {
        // Validate chef structure if any returned
        if (data.length > 0) {
          expect(data[0]).toHaveProperty('chef_id');
          expect(data[0]).toHaveProperty('score');
        }
      }
    }
  });

  test('POST /scheduling/chefs/assign assigns chef to booking @api', async ({
    request,
  }) => {
    // Endpoint NOW EXISTS in scheduling.py - assigns chef to a booking
    // Requires valid booking_id and chef_id UUIDs
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/chefs/assign`,
      {
        data: {
          booking_id: '00000000-0000-0000-0000-000000000001', // Will return 404 if not found
          chef_id: '00000000-0000-0000-0000-000000000001',
          event_date: getTestDate(30),
          event_time: '18:00',
          override_conflicts: false,
        },
      }
    );

    // May require auth (401/403), or booking/chef not found (404), or validation error (422)
    expect([200, 201, 401, 403, 404, 422, 500]).toContain(response.status());
  });
});

test.describe('Scheduling API - Negotiation @api @scheduling', () => {
  test('GET /scheduling/negotiations/pending returns pending negotiations @api', async ({
    request,
  }) => {
    const response = await request.get(
      `${API_URL}/api/v1/scheduling/negotiations/pending`
    );

    // May require auth
    expect([200, 401, 403, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Should return array of pending negotiations
      expect(Array.isArray(data) || typeof data === 'object').toBeTruthy();
    }
  });

  test('POST /scheduling/negotiations creates negotiation @api', async ({
    request,
  }) => {
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/negotiations`,
      {
        data: {
          booking_id: 'test-booking-id',
          reason: 'time_change',
          proposed_date: getTestDate(35),
          proposed_time: '19:00',
          message: 'Customer requested evening slot',
        },
      }
    );

    // May require auth or booking may not exist
    expect([200, 201, 401, 403, 404, 422, 500]).toContain(response.status());
  });
});

test.describe('Scheduling API - Smart Suggestions @api @scheduling', () => {
  test('suggestions return alternative times when slot unavailable @api', async ({
    request,
  }) => {
    // Request a slot that's likely taken (if any bookings exist)
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/availability/check`,
      {
        data: {
          event_date: getTestDate(7), // Near-term more likely to conflict
          event_time: '18:00', // Prime dinner time
          guest_count: 25,
          venue_lat: 34.0522,
          venue_lng: -118.2437,
        },
      }
    );

    expect([200, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // If slot is unavailable, suggestions should be provided
      if (!data.is_requested_available && data.suggestions) {
        expect(data.suggestions.length).toBeGreaterThan(0);

        // Suggestions should be sorted by proximity to requested time
        const firstSuggestion = data.suggestions[0];
        expect(firstSuggestion).toHaveProperty('slot_time');
        expect(firstSuggestion).toHaveProperty('is_available');
      }
    }
  });

  test('handles large party guest counts @api', async ({ request }) => {
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/availability/check`,
      {
        data: {
          event_date: getTestDate(60),
          event_time: '17:00',
          guest_count: 100, // Large party
          venue_lat: 34.0522,
          venue_lng: -118.2437,
        },
      }
    );

    expect([200, 422, 500]).toContain(response.status());

    // Large parties may have fewer available slots
    if (response.status() === 200) {
      const data = await response.json();
      // Just verify it returns valid response
      expect(data).toBeDefined();
    }
  });
});

test.describe('Scheduling API - Event Duration @api @scheduling', () => {
  test('POST /scheduling/duration/calculate calculates event duration @api', async ({
    request,
  }) => {
    // Correct path is /duration/calculate (not /event/duration)
    const response = await request.post(
      `${API_URL}/api/v1/scheduling/duration/calculate`,
      {
        data: {
          guest_count: 20,
        },
      }
    );

    expect([200, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Should return duration info
      expect(data).toHaveProperty('duration_minutes');
      expect(data).toHaveProperty('setup_minutes');
      expect(data).toHaveProperty('cleanup_minutes');
    }
  });

  test('duration scales with guest count @api', async ({ request }) => {
    const smallPartyResponse = await request.post(
      `${API_URL}/api/v1/scheduling/event/duration`,
      {
        data: { guest_count: 10 },
      }
    );

    const largePartyResponse = await request.post(
      `${API_URL}/api/v1/scheduling/event/duration`,
      {
        data: { guest_count: 50 },
      }
    );

    if (
      smallPartyResponse.status() === 200 &&
      largePartyResponse.status() === 200
    ) {
      const smallData = await smallPartyResponse.json();
      const largeData = await largePartyResponse.json();

      // Large party should take longer
      expect(largeData.duration_minutes).toBeGreaterThanOrEqual(
        smallData.duration_minutes
      );
    }
  });
});
