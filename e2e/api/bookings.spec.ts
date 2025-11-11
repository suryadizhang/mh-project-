import { test, expect } from '@playwright/test';

/**
 * API Tests
 * 
 * Direct API testing without frontend
 * Tests backend endpoints directly
 * 
 * Tags: @api
 * Services needed: Backend, Database
 */

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('Bookings API', () => {
  test('GET /api/v1/bookings returns 200 @api', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/bookings`);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });
  
  test('POST /api/v1/bookings creates booking @api @critical', async ({ request }) => {
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
    
    expect(response.status()).toBe(201);
    
    const data = await response.json();
    expect(data.id).toBeTruthy();
    expect(data.customerName).toBe(bookingData.customerName);
    expect(data.customerEmail).toBe(bookingData.customerEmail);
  });
  
  test('GET /api/v1/bookings/:id returns booking @api', async ({ request }) => {
    // First create a booking
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
    const response = await request.get(`${API_URL}/api/v1/bookings/${created.id}`);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.id).toBe(created.id);
  });
  
  test('PUT /api/v1/bookings/:id updates booking @api', async ({ request }) => {
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
    const updateResponse = await request.put(`${API_URL}/api/v1/bookings/${created.id}`, {
      data: {
        guestCount: 25,
        specialRequests: 'Updated request',
      },
    });
    
    expect(updateResponse.status()).toBe(200);
    
    const updated = await updateResponse.json();
    expect(updated.guestCount).toBe(25);
    expect(updated.specialRequests).toBe('Updated request');
  });
  
  test('DELETE /api/v1/bookings/:id deletes booking @api', async ({ request }) => {
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
    const deleteResponse = await request.delete(`${API_URL}/api/v1/bookings/${created.id}`);
    
    expect(deleteResponse.status()).toBe(204);
    
    // Verify it's gone
    const getResponse = await request.get(`${API_URL}/api/v1/bookings/${created.id}`);
    expect(getResponse.status()).toBe(404);
  });
});

test.describe('Payments API', () => {
  test('POST /api/v1/payments/create-intent creates payment intent @api @payment', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/payments/create-intent`, {
      data: {
        amount: 10000, // $100 in cents
        currency: 'usd',
        bookingId: 'test-booking-123',
        customerInfo: {
          name: 'Test User',
          email: 'test@example.com',
        },
      },
    });
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.clientSecret).toBeTruthy();
    expect(data.paymentIntentId).toBeTruthy();
  });
});

test.describe('Health Checks', () => {
  test('GET /health returns 200 @api @smoke', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });
  
  test('GET /api/v1/health returns service status @api', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/health`);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.database).toBeTruthy();
    expect(data.redis).toBeTruthy();
  });
});

test.describe('Error Handling', () => {
  test('returns 400 for invalid booking data @api', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/bookings`, {
      data: {
        // Missing required fields
        customerName: 'Test User',
      },
    });
    
    expect(response.status()).toBe(400);
    
    const data = await response.json();
    expect(data.detail).toBeTruthy();
  });
  
  test('returns 404 for non-existent booking @api', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/bookings/non-existent-id`);
    
    expect(response.status()).toBe(404);
  });
  
  test('returns 401 for unauthorized admin endpoint @api', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/admin/bookings`);
    
    expect(response.status()).toBe(401);
  });
});
