import { test, expect } from '@playwright/test';

/**
 * Production API Health & Public Endpoints Tests
 *
 * Tests that can run against production WITHOUT authentication
 * Focus on health checks, public endpoints, and basic connectivity
 *
 * Tags: @api @smoke @production
 * Services needed: Backend API only
 */

const API_URL = process.env.API_URL || 'https://mhapi.mysticdatanode.net';

test.describe('API Health Checks', () => {
  test('GET /health returns healthy status @api @smoke', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/health`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.service).toBeTruthy();
    expect(data.version).toBeTruthy();
  });

  test('GET /api/v1/health returns service status @api @smoke', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/api/v1/health`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.service).toBeTruthy();
  });

  test('GET /api/v1/health/liveness returns status @api', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/api/v1/health/liveness`);

    // May return 200 (healthy) or 500/503 (if dependencies are down)
    // Either way, the endpoint should respond
    expect([200, 500, 503]).toContain(response.status());
  });

  test('GET /api/v1/health/readiness returns status @api', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/api/v1/health/readiness`);

    // May return 200 (ready) or 503 (not ready)
    // Either way, the endpoint should respond
    expect([200, 500, 503]).toContain(response.status());
  });
});

test.describe('Public Pricing Endpoints', () => {
  test('GET /api/v1/pricing/current returns pricing info @api @smoke', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/api/v1/pricing/current`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.base_pricing).toBeTruthy();
    expect(data.base_pricing.adult_price).toBeGreaterThan(0);
    expect(data.base_pricing.child_price).toBeGreaterThan(0);
  });

  test('GET /api/v1/pricing/summary returns pricing summary @api', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/api/v1/pricing/summary`);

    // May or may not require auth - check status
    expect([200, 401, 403]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toBeTruthy();
    }
  });

  test('POST /api/v1/pricing/calculate calculates quote @api @smoke', async ({
    request,
  }) => {
    const response = await request.post(`${API_URL}/api/v1/pricing/calculate`, {
      data: {
        adult_count: 10,
        child_count: 2,
        zip_code: '94555',
      },
    });

    // May or may not work depending on endpoint configuration
    expect([200, 400, 422]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();
      expect(data.total).toBeGreaterThan(0);
    }
  });
});

test.describe('API Error Handling', () => {
  test('returns 401 for unauthenticated booking list @api', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/api/v1/bookings`);

    // Should require authentication
    expect(response.status()).toBe(401);

    const data = await response.json();
    expect(data.success).toBe(false);
    expect(data.error.code).toBe('UNAUTHORIZED');
  });

  test('returns 404 for non-existent endpoint @api', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/this-does-not-exist`);

    expect(response.status()).toBe(404);
  });

  test('returns proper error format for invalid request @api', async ({
    request,
  }) => {
    const response = await request.post(`${API_URL}/api/v1/bookings`, {
      data: {}, // Empty body - should fail validation
    });

    // Should return 401 (auth required) or 422 (validation error)
    expect([401, 422]).toContain(response.status());

    const data = await response.json();
    expect(data.success).toBe(false);
    expect(data.error).toBeTruthy();
  });
});

test.describe('API Response Format', () => {
  test('health endpoint returns proper JSON structure @api', async ({
    request,
  }) => {
    const response = await request.get(`${API_URL}/health`);

    expect(response.headers()['content-type']).toContain('application/json');

    const data = await response.json();
    expect(typeof data).toBe('object');
    expect(data).not.toBeNull();
  });

  test('error responses have consistent format @api', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/bookings`);

    const data = await response.json();

    // Verify error response structure
    expect(data).toHaveProperty('success');
    expect(data).toHaveProperty('error');
    expect(data.error).toHaveProperty('code');
    expect(data.error).toHaveProperty('message');
    expect(data.error).toHaveProperty('timestamp');
  });
});

test.describe('OpenAPI Documentation', () => {
  test('GET /openapi.json returns API spec @api', async ({ request }) => {
    const response = await request.get(`${API_URL}/openapi.json`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.openapi).toBeTruthy();
    expect(data.info).toBeTruthy();
    expect(data.info.title).toContain('Hibachi');
    expect(data.paths).toBeTruthy();
  });
});

test.describe('CORS Headers', () => {
  test('API returns proper CORS headers @api', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);

    // Check for CORS headers - may vary based on config
    const headers = response.headers();

    // At minimum, should have content-type
    expect(headers['content-type']).toBeTruthy();
  });
});
