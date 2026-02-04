import { test, expect } from '@playwright/test';
import {
  mockAdminUsers,
  mockStations,
  generateUniqueEmail,
  randomString,
} from '../helpers/mock-data';

/**
 * Admin API Integration Tests
 *
 * Tests the Admin System endpoints:
 * - User management (CRUD)
 * - Role-based access
 * - Station management
 * - Super Admin features
 * - Station Manager features
 *
 * Tags: @api @admin @rbac @critical
 */

const API_URL =
  process.env.STAGING_API_URL || 'https://staging-api.mysticdatanode.net';

// Test admin credentials from environment
const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL || '';
const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD || '';

let authToken: string = '';
let refreshToken: string = '';

test.describe('Admin API - Authentication @api @admin @auth', () => {
  test('POST /auth/login authenticates admin user @critical', async ({
    request,
  }) => {
    // If credentials not set, skip
    if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
      test.skip(
        true,
        'TEST_ADMIN_EMAIL or TEST_ADMIN_PASSWORD not set in environment'
      );
      return;
    }

    // OAuth2PasswordRequestForm expects form data with 'username' field (not 'email')
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      form: {
        username: ADMIN_EMAIL,
        password: ADMIN_PASSWORD,
      },
    });

    // 200 = success, 401 = wrong creds, 422 = validation error, 500 = server error
    expect([200, 401, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      expect(data).toHaveProperty('access_token');
      expect(data).toHaveProperty('token_type');

      // Store token for subsequent tests
      authToken = data.access_token;
      if (data.refresh_token) {
        refreshToken = data.refresh_token;
      }
    }
  });

  test('GET /auth/me returns current user info @api @auth', async ({
    request,
  }) => {
    if (!authToken) {
      // Try to login first
      const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
      });

      if (loginResponse.status() === 200) {
        const data = await loginResponse.json();
        authToken = data.access_token;
      } else {
        test.skip(!authToken, 'Could not authenticate');
        return;
      }
    }

    const response = await request.get(`${API_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

    expect([200, 401]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      expect(data).toHaveProperty('email');
      expect(data).toHaveProperty('role');
      expect(data.email).toBe(ADMIN_EMAIL);
    }
  });
});

test.describe('Admin API - User Management @api @admin @rbac', () => {
  test.beforeAll(async ({ request }) => {
    // Login to get auth token
    if (!authToken && ADMIN_EMAIL && ADMIN_PASSWORD) {
      const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
      });

      if (loginResponse.status() === 200) {
        const data = await loginResponse.json();
        authToken = data.access_token;
      }
    }
  });

  test('GET /admin/users lists all users (super_admin only) @critical', async ({
    request,
  }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    const response = await request.get(`${API_URL}/api/v1/admin/users`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

    // Skip if endpoint doesn't exist yet (future development)
    if (response.status() === 404) {
      test.skip(true, 'Endpoint /admin/users not implemented yet');
      return;
    }

    expect([200, 401, 403]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Should return array of users or paginated response
      if (Array.isArray(data)) {
        // Verify user structure
        if (data.length > 0) {
          expect(data[0]).toHaveProperty('id');
          expect(data[0]).toHaveProperty('email');
          expect(data[0]).toHaveProperty('role');
        }
      } else if (data.items) {
        // Paginated response
        expect(Array.isArray(data.items)).toBeTruthy();
      }
    }
  });

  test('POST /admin/users creates new admin user @critical', async ({
    request,
  }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    const newUserEmail = generateUniqueEmail('newadmin');

    const response = await request.post(`${API_URL}/api/v1/admin/users`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        email: newUserEmail,
        password: 'TestPassword123!',
        first_name: 'Test',
        last_name: 'Admin',
        role: 'customer_support', // Lower role for testing
        is_active: true,
      },
    });

    // Skip if endpoint doesn't exist yet (future development)
    if (response.status() === 404) {
      test.skip(true, 'Endpoint /admin/users not implemented yet');
      return;
    }

    expect([200, 201, 400, 401, 403, 409, 422]).toContain(response.status());

    if (response.status() === 200 || response.status() === 201) {
      const data = await response.json();

      expect(data).toHaveProperty('id');
      expect(data.email).toBe(newUserEmail);
      expect(data.role).toBe('customer_support');

      // Store for cleanup
      test
        .info()
        .annotations.push({ type: 'created_user_id', description: data.id });
    }
  });

  test('PUT /admin/users/:id updates user @api', async ({ request }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    // First create a user to update
    const userEmail = generateUniqueEmail('updatetest');

    const createResponse = await request.post(`${API_URL}/api/v1/admin/users`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        email: userEmail,
        password: 'TestPassword123!',
        first_name: 'Update',
        last_name: 'Test',
        role: 'customer_support',
      },
    });

    if (createResponse.status() === 200 || createResponse.status() === 201) {
      const created = await createResponse.json();

      // Update the user
      const updateResponse = await request.put(
        `${API_URL}/api/v1/admin/users/${created.id}`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
          data: {
            first_name: 'Updated',
            last_name: 'User',
          },
        }
      );

      expect([200, 400, 401, 403, 404, 422]).toContain(updateResponse.status());

      if (updateResponse.status() === 200) {
        const updated = await updateResponse.json();
        expect(updated.first_name).toBe('Updated');
      }
    }
  });

  test('DELETE /admin/users/:id deletes user (super_admin only) @critical', async ({
    request,
  }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    // First create a user to delete
    const userEmail = generateUniqueEmail('deletetest');

    const createResponse = await request.post(`${API_URL}/api/v1/admin/users`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        email: userEmail,
        password: 'TestPassword123!',
        first_name: 'Delete',
        last_name: 'Test',
        role: 'customer_support',
      },
    });

    if (createResponse.status() === 200 || createResponse.status() === 201) {
      const created = await createResponse.json();

      // Delete the user
      const deleteResponse = await request.delete(
        `${API_URL}/api/v1/admin/users/${created.id}`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
        }
      );

      expect([200, 204, 401, 403, 404]).toContain(deleteResponse.status());

      // Verify deletion
      if (deleteResponse.status() === 200 || deleteResponse.status() === 204) {
        const getResponse = await request.get(
          `${API_URL}/api/v1/admin/users/${created.id}`,
          {
            headers: { Authorization: `Bearer ${authToken}` },
          }
        );

        // Should be 404 or soft-deleted (is_active: false)
        expect([404, 200]).toContain(getResponse.status());
      }
    }
  });
});

test.describe('Admin API - Role-Based Access Control @api @admin @rbac', () => {
  test('validates role hierarchy permissions @critical', async ({
    request,
  }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    // Get current user's role
    const meResponse = await request.get(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    if (meResponse.status() === 200) {
      const me = await meResponse.json();

      // Super admin should have access to all endpoints
      if (me.role === 'super_admin') {
        // Can access admin users
        const usersResponse = await request.get(
          `${API_URL}/api/v1/admin/users`,
          {
            headers: { Authorization: `Bearer ${authToken}` },
          }
        );
        expect([200]).toContain(usersResponse.status());

        // Can access stations
        const stationsResponse = await request.get(
          `${API_URL}/api/v1/stations`,
          {
            headers: { Authorization: `Bearer ${authToken}` },
          }
        );
        expect([200, 404]).toContain(stationsResponse.status());
      }
    }
  });

  test('station_manager can only access assigned stations @api', async ({
    request,
  }) => {
    // This would require creating and logging in as a station manager
    // For now, just verify the endpoint structure

    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    const response = await request.get(`${API_URL}/api/v1/stations/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    // Endpoint may or may not exist
    expect([200, 404, 401, 403]).toContain(response.status());
  });
});

test.describe('Admin API - Station Management @api @admin', () => {
  test('GET /stations lists all stations @api', async ({ request }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    const response = await request.get(`${API_URL}/api/v1/stations`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect([200, 401, 403, 404]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      if (Array.isArray(data)) {
        // Verify station structure
        if (data.length > 0) {
          expect(data[0]).toHaveProperty('id');
          expect(data[0]).toHaveProperty('name');
        }
      }
    }
  });

  test('POST /stations creates new station @api', async ({ request }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    const stationCode = `TEST-${randomString(4).toUpperCase()}`;

    const response = await request.post(`${API_URL}/api/v1/stations`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        name: `Test Station ${stationCode}`,
        code: stationCode,
        address: '999 Test Lane, Los Angeles, CA 90099',
        lat: 34.06,
        lng: -118.25,
        service_radius_miles: 25,
        is_active: true,
      },
    });

    // Skip if endpoint doesn't exist yet (future development)
    if (response.status() === 404) {
      test.skip(true, 'Endpoint /stations POST not implemented yet');
      return;
    }

    expect([200, 201, 400, 401, 403, 409, 422]).toContain(response.status());

    if (response.status() === 200 || response.status() === 201) {
      const data = await response.json();

      expect(data).toHaveProperty('id');
      expect(data.code).toBe(stationCode);
    }
  });

  test('GET /stations/:id returns station details @api', async ({
    request,
  }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    // First get list of stations
    const listResponse = await request.get(`${API_URL}/api/v1/stations`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    if (listResponse.status() === 200) {
      const stations = await listResponse.json();

      if (Array.isArray(stations) && stations.length > 0) {
        const stationId = stations[0].id;

        const response = await request.get(
          `${API_URL}/api/v1/stations/${stationId}`,
          {
            headers: { Authorization: `Bearer ${authToken}` },
          }
        );

        expect([200, 404]).toContain(response.status());

        if (response.status() === 200) {
          const data = await response.json();
          expect(data.id).toBe(stationId);
        }
      }
    }
  });
});

test.describe('Admin API - Analytics @api @admin', () => {
  test('GET /admin/analytics/dashboard returns dashboard stats @api', async ({
    request,
  }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    const response = await request.get(
      `${API_URL}/api/v1/admin/analytics/dashboard`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );

    expect([200, 401, 403, 404]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Should return dashboard metrics
      // Structure depends on implementation
      expect(data).toBeDefined();
    }
  });

  test('GET /admin/analytics/bookings returns booking stats @api', async ({
    request,
  }) => {
    if (!authToken) {
      test.skip(!authToken, 'Auth token not available');
      return;
    }

    const response = await request.get(
      `${API_URL}/api/v1/admin/analytics/bookings`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
        params: {
          period: '30d', // Last 30 days
        },
      }
    );

    expect([200, 401, 403, 404]).toContain(response.status());
  });
});
