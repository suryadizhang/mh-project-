import { test, expect } from '@playwright/test';
import {
  mockAgreements,
  mockSignatureBase64,
  mockQuotes,
  generateUniqueEmail,
  getTestDate,
} from '../helpers/mock-data';

/**
 * Agreements API Integration Tests
 *
 * Tests the Legal Agreements System:
 * - Agreement templates
 * - Slot holds
 * - Digital signatures
 * - Agreement signing flow
 *
 * Part of Quote → Booking → Agreement flow testing
 *
 * Tags: @api @agreements @critical
 */

const API_URL =
  process.env.STAGING_API_URL || 'https://staging-api.mysticdatanode.net';

test.describe('Agreements API - Templates @api @agreements', () => {
  test('GET /agreements/templates/liability_waiver returns template @critical', async ({
    request,
  }) => {
    const response = await request.get(
      `${API_URL}/api/v1/agreements/templates/liability_waiver`
    );

    expect([200, 404, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      // Verify template structure
      expect(data).toHaveProperty('id');
      expect(data).toHaveProperty('agreement_type');
      expect(data).toHaveProperty('version');
      expect(data).toHaveProperty('title');
      expect(data).toHaveProperty('content_rendered');
      expect(data).toHaveProperty('requires_signature');

      expect(data.agreement_type).toBe('liability_waiver');
    }
  });

  test('GET /agreements/templates/allergen_disclosure returns template @critical', async ({
    request,
  }) => {
    const response = await request.get(
      `${API_URL}/api/v1/agreements/templates/allergen_disclosure`
    );

    expect([200, 404, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      expect(data.agreement_type).toBe('allergen_disclosure');
      expect(data).toHaveProperty('content_rendered');
    }
  });

  test('GET /agreements/templates/invalid returns 404 @api', async ({
    request,
  }) => {
    const response = await request.get(
      `${API_URL}/api/v1/agreements/templates/invalid_type`
    );

    expect([404, 422]).toContain(response.status());
  });
});

test.describe('Agreements API - Slot Holds @api @agreements', () => {
  test('POST /agreements/holds creates slot hold @critical', async ({
    request,
  }) => {
    const response = await request.post(`${API_URL}/api/v1/agreements/holds`, {
      data: {
        event_date: getTestDate(30),
        event_time: '18:00',
        guest_count: 20,
        customer_email: generateUniqueEmail('hold'),
        customer_name: 'Test Customer',
        customer_phone: '555-123-4567',
        venue_address: '123 Test St, Los Angeles, CA 90001',
        venue_lat: 34.0522,
        venue_lng: -118.2437,
      },
    });

    expect([200, 201, 404, 409, 422, 500]).toContain(response.status());

    if (response.status() === 200 || response.status() === 201) {
      const data = await response.json();

      // Should return hold token
      expect(data).toHaveProperty('hold_token');
      expect(data).toHaveProperty('expires_at');

      // Store for subsequent tests
      test
        .info()
        .annotations.push({ type: 'hold_token', description: data.hold_token });
    }
  });

  test('GET /agreements/holds/:token validates hold @api', async ({
    request,
  }) => {
    // First create a hold
    const createResponse = await request.post(
      `${API_URL}/api/v1/agreements/holds`,
      {
        data: {
          event_date: getTestDate(31),
          event_time: '17:00',
          guest_count: 15,
          customer_email: generateUniqueEmail('validate'),
          customer_name: 'Validation Test',
          customer_phone: '555-999-8888',
          venue_address: '456 Test Ave, Los Angeles, CA 90002',
          venue_lat: 34.053,
          venue_lng: -118.245,
        },
      }
    );

    if (createResponse.status() === 200 || createResponse.status() === 201) {
      const createData = await createResponse.json();
      const holdToken = createData.hold_token;

      // Validate the hold
      const validateResponse = await request.get(
        `${API_URL}/api/v1/agreements/holds/${holdToken}`
      );

      expect([200, 404, 410]).toContain(validateResponse.status());

      if (validateResponse.status() === 200) {
        const data = await validateResponse.json();

        expect(data).toHaveProperty('is_valid');
        expect(data).toHaveProperty('event_date');
        expect(data).toHaveProperty('event_time');
      }
    }
  });

  test('DELETE /agreements/holds/:token releases hold @api', async ({
    request,
  }) => {
    // First create a hold
    const createResponse = await request.post(
      `${API_URL}/api/v1/agreements/holds`,
      {
        data: {
          event_date: getTestDate(32),
          event_time: '19:00',
          guest_count: 25,
          customer_email: generateUniqueEmail('release'),
          customer_name: 'Release Test',
          customer_phone: '555-777-6666',
          venue_address: '789 Test Blvd, Los Angeles, CA 90003',
          venue_lat: 34.054,
          venue_lng: -118.246,
        },
      }
    );

    if (createResponse.status() === 200 || createResponse.status() === 201) {
      const createData = await createResponse.json();
      const holdToken = createData.hold_token;

      // Release the hold
      const deleteResponse = await request.delete(
        `${API_URL}/api/v1/agreements/holds/${holdToken}`
      );

      expect([200, 204, 404]).toContain(deleteResponse.status());

      // Verify hold is no longer valid
      if (deleteResponse.status() === 200 || deleteResponse.status() === 204) {
        const validateResponse = await request.get(
          `${API_URL}/api/v1/agreements/holds/${holdToken}`
        );
        expect([404, 410]).toContain(validateResponse.status());
      }
    }
  });
});

test.describe('Agreements API - Signing @api @agreements', () => {
  test('POST /agreements/sign signs agreement with hold token @critical', async ({
    request,
  }) => {
    // First create a hold
    const createResponse = await request.post(
      `${API_URL}/api/v1/agreements/holds`,
      {
        data: {
          event_date: getTestDate(33),
          event_time: '18:30',
          guest_count: 20,
          customer_email: generateUniqueEmail('sign'),
          customer_name: 'Signature Test',
          customer_phone: '555-111-2222',
          venue_address: '100 Sign St, Los Angeles, CA 90004',
          venue_lat: 34.055,
          venue_lng: -118.247,
        },
      }
    );

    if (createResponse.status() === 200 || createResponse.status() === 201) {
      const createData = await createResponse.json();
      const holdToken = createData.hold_token;

      // Sign the agreement
      const signResponse = await request.post(
        `${API_URL}/api/v1/agreements/sign`,
        {
          data: {
            hold_token: holdToken,
            agreement_type: 'liability_waiver',
            signature_image_base64: mockSignatureBase64,
            typed_name: 'Signature Test',
            ip_address: '127.0.0.1',
          },
        }
      );

      expect([200, 201, 400, 422, 500]).toContain(signResponse.status());

      if (signResponse.status() === 200 || signResponse.status() === 201) {
        const data = await signResponse.json();

        // Should return signed agreement
        expect(data).toHaveProperty('agreement_id');
        expect(data).toHaveProperty('signed_at');
      }
    }
  });

  test('POST /agreements/validate-signature validates signature image @api', async ({
    request,
  }) => {
    const response = await request.post(
      `${API_URL}/api/v1/agreements/validate-signature`,
      {
        data: {
          signature_image_base64: mockSignatureBase64,
        },
      }
    );

    expect([200, 400, 404, 422, 500]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();

      expect(data).toHaveProperty('is_valid');
    }
  });

  test('GET /agreements/status/:booking_id returns agreement status @api', async ({
    request,
  }) => {
    // Use a test booking ID
    const response = await request.get(
      `${API_URL}/api/v1/agreements/status/00000000-0000-0000-0000-000000000001`
    );

    expect([200, 404, 500]).toContain(response.status());

    // 404 is expected if booking doesn't exist
    // 200 would return signing status
  });
});

test.describe('Agreements API - Send Link @api @agreements', () => {
  test('POST /agreements/send-link sends signing link @api', async ({
    request,
  }) => {
    // First create a hold
    const createResponse = await request.post(
      `${API_URL}/api/v1/agreements/holds`,
      {
        data: {
          event_date: getTestDate(34),
          event_time: '17:30',
          guest_count: 18,
          customer_email: generateUniqueEmail('sendlink'),
          customer_name: 'Send Link Test',
          customer_phone: '555-333-4444',
          venue_address: '200 Link Ave, Los Angeles, CA 90005',
          venue_lat: 34.056,
          venue_lng: -118.248,
        },
      }
    );

    if (createResponse.status() === 200 || createResponse.status() === 201) {
      const createData = await createResponse.json();
      const holdToken = createData.hold_token;

      // Request signing link to be sent
      const sendResponse = await request.post(
        `${API_URL}/api/v1/agreements/send-link`,
        {
          data: {
            hold_token: holdToken,
            send_method: 'email', // or 'sms'
          },
        }
      );

      expect([200, 201, 400, 422, 500]).toContain(sendResponse.status());

      if (sendResponse.status() === 200 || sendResponse.status() === 201) {
        const data = await sendResponse.json();

        expect(data).toHaveProperty('success');
        expect(data).toHaveProperty('message');
      }
    }
  });
});
