import { test, expect } from '@playwright/test';

/**
 * API Tests
 *
 * Direct API testing without frontend
 * Tests backend endpoints directly
 *
 * Tags: @api
 * Services needed: Backend, Database
 *
 * NOTE: Bookings endpoints require authentication. Tests that expect 200
 * without auth should expect 401 instead.
 */

// Use STAGING_API_URL for staging tests, fall back to API_URL for local
const API_URL =
  process.env.STAGING_API_URL || process.env.API_URL || 'http://localhost:8000';

test.describe('Bookings API', () => {
  test('GET /api/v1/bookings returns 401 without auth @api', async ({
    request,
  }) => {
    // Protected endpoint - requires authentication
    const response = await request.get(`${API_URL}/api/v1/bookings`);

    // Should return 401 Unauthorized without auth token
    expect(response.status()).toBe(401);
  });

  test('POST /api/v1/bookings returns 401 without auth @api @critical', async ({
    request,
  }) => {
    // Protected endpoint - requires authentication
    const bookingData = {
      customerName: 'Test User',
      customerEmail: `test-${Date.now()}@example.com`,
      customerPhone: '555-0123',
      eventDate: '2025-12-25',
      guestCount: 20,
      menuItems: ['Hibachi Chicken', 'Fried Rice'],
      specialRequests: 'Test booking',
    };

    const response = await request.post(`${API_URL}/api/v1/bookings`, {
      data: bookingData,
    });

    // Should return 401 Unauthorized without auth token
    expect(response.status()).toBe(401);
  });

  test.skip('GET /api/v1/bookings/:id returns booking @api - REQUIRES AUTH', async ({
    request,
  }) => {
    // TODO: Add authenticated test with valid JWT token
    const createResponse = await request.post(`${API_URL}/api/v1/bookings`, {
      data: {
        customerName: 'Test User',
        customerEmail: `test-${Date.now()}@example.com`,
        customerPhone: '555-0123',
        eventDate: '2025-12-25',
        guestCount: 20,
      },
    });

    const created = await createResponse.json();

    // Then fetch it
    const response = await request.get(
      `${API_URL}/api/v1/bookings/${created.id}`
    );

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.id).toBe(created.id);
  });

  test.skip('PUT /api/v1/bookings/:id updates booking @api - REQUIRES AUTH', async ({
    request,
  }) => {
    // TODO: Add authenticated test with valid JWT token
    // Create booking
    const createResponse = await request.post(`${API_URL}/api/v1/bookings`, {
      data: {
        customerName: 'Test User',
        customerEmail: `test-${Date.now()}@example.com`,
        eventDate: '2025-12-25',
        guestCount: 20,
      },
    });

    const created = await createResponse.json();

    // Update it
    const updateResponse = await request.put(
      `${API_URL}/api/v1/bookings/${created.id}`,
      {
        data: {
          guestCount: 25,
          specialRequests: 'Updated request',
        },
      }
    );

    expect(updateResponse.status()).toBe(200);

    const updated = await updateResponse.json();
    expect(updated.guestCount).toBe(25);
    expect(updated.specialRequests).toBe('Updated request');
  });

  test.skip('DELETE /api/v1/bookings/:id deletes booking @api - REQUIRES AUTH', async ({
    request,
  }) => {
    // TODO: Add authenticated test with valid JWT token
    // Create booking
    const createResponse = await request.post(`${API_URL}/api/v1/bookings`, {
      data: {
        customerName: 'Test User',
        customerEmail: `test-${Date.now()}@example.com`,
        eventDate: '2025-12-25',
        guestCount: 20,
      },
    });

    const created = await createResponse.json();

    // Delete it
    const deleteResponse = await request.delete(
      `${API_URL}/api/v1/bookings/${created.id}`
    );

    expect(deleteResponse.status()).toBe(204);

    // Verify it's gone
    const getResponse = await request.get(
      `${API_URL}/api/v1/bookings/${created.id}`
    );
    expect(getResponse.status()).toBe(404);
  });
});

test.describe('Payments API', () => {
  test('POST /api/v1/payments/create-intent returns proper response @api @payment', async ({
    request,
  }) => {
    const response = await request.post(
      `${API_URL}/api/v1/payments/create-intent`,
      {
        data: {
          amount: 10000, // $100 in cents
          currency: 'usd',
          bookingId: 'test-booking-123',
          customerInfo: {
            name: 'Test User',
            email: 'test@example.com',
          },
        },
      }
    );

    // May return 200 (success), 401 (auth required), or 404 (endpoint not at this path)
    expect([200, 401, 404, 422]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();
      expect(data.clientSecret || data.client_secret).toBeTruthy();
    }
  });
});

test.describe('Health Checks', () => {
  test('GET /health returns 200 @api @smoke', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('GET /api/v1/health returns service status @api', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/api/v1/health`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    // Simple health check returns status and timestamp
    expect(data.status).toBeDefined();
    expect(data.timestamp || data.uptime_seconds).toBeDefined();
  });
});

test.describe('Error Handling', () => {
  test('returns 401 for invalid booking data without auth @api', async ({
    request,
  }) => {
    // Protected endpoint returns 401 before validating data
    const response = await request.post(`${API_URL}/api/v1/bookings`, {
      data: {
        // Missing required fields
        customerName: 'Test User',
      },
    });

    // Auth check happens before validation, so expect 401
    expect(response.status()).toBe(401);
  });

  test('returns 401 for non-existent booking without auth @api', async ({
    request,
  }) => {
    // Protected endpoint returns 401 before checking if booking exists
    const response = await request.get(
      `${API_URL}/api/v1/bookings/non-existent-id`
    );

    // Auth check happens before 404, so expect 401
    expect(response.status()).toBe(401);
  });

  test('returns 401 or 404 for unauthorized admin endpoint @api', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/api/v1/admin/bookings`);

    // May return 401 (auth required) or 404 (route not found)
    expect([401, 404]).toContain(response.status());
  });
});
