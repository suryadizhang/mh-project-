/**
 * Comprehensive E2E Test Suite for All Channels
 * Tests Email, SMS, Instagram, Facebook, and Voice AI
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
const API_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Helper Functions
 */

async function loginAsAdmin(page: Page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('[name="email"]', 'admin@myhibachichef.com');
  await page.fill('[name="password"]', 'test_password');
  await page.click('button[type="submit"]');
  await page.waitForURL(`${BASE_URL}/dashboard`);
}

async function waitForAPIResponse(page: Page, endpoint: string, timeout = 5000) {
  return await page.waitForResponse(
    response => response.url().includes(endpoint) && response.status() === 200,
    { timeout }
  );
}

/**
 * Email Channel Tests
 */
test.describe('Email Channel E2E', () => {
  test('should send approval email successfully', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Navigate to user management
    await page.goto(`${BASE_URL}/admin/users`);
    
    // Find pending user
    await page.click('[data-testid="pending-users-tab"]');
    const firstUser = page.locator('[data-testid="user-row"]').first();
    await expect(firstUser).toBeVisible();
    
    // Approve user
    await firstUser.locator('[data-testid="approve-button"]').click();
    
    // Wait for confirmation
    await expect(page.locator('[data-testid="success-message"]')).toContainText(
      'Email sent successfully'
    );
    
    // Verify email was logged
    const emailResponse = await waitForAPIResponse(page, '/api/v1/admin/email-logs');
    expect(emailResponse.ok()).toBeTruthy();
  });

  test('should display AI-generated email for review', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Navigate to email review dashboard
    await page.goto(`${BASE_URL}/admin/email-review`);
    
    // Check for pending emails
    const pendingEmails = page.locator('[data-testid="pending-email-card"]');
    const count = await pendingEmails.count();
    
    if (count > 0) {
      // Click first pending email
      await pendingEmails.first().click();
      
      // Verify AI response is shown
      await expect(page.locator('[data-testid="ai-response"]')).toBeVisible();
      await expect(page.locator('[data-testid="original-email"]')).toBeVisible();
      
      // Edit response
      await page.click('[data-testid="edit-button"]');
      await page.fill('[data-testid="response-editor"]', 'Edited response');
      
      // Approve and send
      await page.click('[data-testid="approve-send-button"]');
      
      await expect(page.locator('[data-testid="success-message"]')).toContainText(
        'Email sent'
      );
    }
  });
});

/**
 * SMS Channel Tests
 */
test.describe('SMS Channel E2E', () => {
  test('should send SMS via RingCentral', async ({ page, request }) => {
    // API test for SMS sending
    const response = await request.post(`${API_URL}/api/v1/sms/send`, {
      data: {
        to: '+19167408768',
        message: 'Test SMS from E2E suite'
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
  });

  test('should receive SMS webhook and trigger AI response', async ({ page, request }) => {
    // Simulate incoming SMS webhook
    const webhookPayload = {
      from: { phoneNumber: '+19167408768' },
      to: { phoneNumber: '+18005551234' },
      subject: 'SMS',
      body: 'I want to book a party for 10 people'
    };
    
    const response = await request.post(
      `${API_URL}/api/v1/webhooks/ringcentral/sms`,
      {
        data: webhookPayload
      }
    );
    
    expect(response.ok()).toBeTruthy();
    
    // Wait a bit for AI processing
    await page.waitForTimeout(2000);
    
    // Check conversation was created
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/conversations`);
    
    const conversations = page.locator('[data-testid="conversation-item"]');
    await expect(conversations.first()).toBeVisible();
  });
});

/**
 * Instagram DM Tests
 */
test.describe('Instagram Channel E2E', () => {
  test('should process Instagram DM webhook', async ({ request }) => {
    const webhookPayload = {
      entry: [
        {
          id: 'page_123',
          messaging: [
            {
              sender: { id: 'user_456' },
              recipient: { id: 'page_123' },
              message: {
                mid: 'msg_789',
                text: 'What are your menu options?'
              }
            }
          ]
        }
      ]
    };
    
    const response = await request.post(
      `${API_URL}/api/v1/webhooks/instagram`,
      {
        data: webhookPayload
      }
    );
    
    expect(response.ok()).toBeTruthy();
  });

  test('should display Instagram conversations in admin', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/social/instagram`);
    
    // Check for Instagram conversations
    const conversations = page.locator('[data-testid="instagram-conversation"]');
    await expect(conversations.first()).toBeVisible({ timeout: 10000 });
    
    // Click first conversation
    await conversations.first().click();
    
    // Verify message thread loads
    await expect(page.locator('[data-testid="message-thread"]')).toBeVisible();
  });
});

/**
 * Facebook Messenger Tests
 */
test.describe('Facebook Channel E2E', () => {
  test('should process Facebook Messenger webhook', async ({ request }) => {
    const webhookPayload = {
      entry: [
        {
          id: 'page_123',
          messaging: [
            {
              sender: { id: 'user_789' },
              recipient: { id: 'page_123' },
              message: {
                mid: 'msg_abc',
                text: 'Do you cater for corporate events?'
              }
            }
          ]
        }
      ]
    };
    
    const response = await request.post(
      `${API_URL}/api/v1/webhooks/facebook`,
      {
        data: webhookPayload
      }
    );
    
    expect(response.ok()).toBeTruthy();
  });

  test('should display Facebook conversations in admin', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/social/facebook`);
    
    // Check for Facebook conversations
    const conversations = page.locator('[data-testid="facebook-conversation"]');
    await expect(conversations.first()).toBeVisible({ timeout: 10000 });
  });
});

/**
 * Voice AI Tests
 */
test.describe('Voice AI Channel E2E', () => {
  test('should process inbound call webhook', async ({ request }) => {
    const callWebhookPayload = {
      body: {
        id: 'call_test_123',
        from: { phoneNumber: '+19167408768' },
        to: { phoneNumber: '+18005551234' },
        status: 'Setup'
      }
    };
    
    const response = await request.post(
      `${API_URL}/api/v1/webhooks/ringcentral/voice/inbound`,
      {
        data: callWebhookPayload
      }
    );
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.action).toBe('answer');
  });

  test('should show active calls in dashboard', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/voice/calls`);
    
    // Check active calls widget
    const activeCalls = page.locator('[data-testid="active-calls"]');
    await expect(activeCalls).toBeVisible();
    
    // Check call count
    const callCount = await page.locator('[data-testid="call-count"]').textContent();
    expect(parseInt(callCount || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display call recordings', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/voice/recordings`);
    
    // Wait for recordings to load
    await page.waitForSelector('[data-testid="recording-item"]', { timeout: 10000 });
    
    const recordings = page.locator('[data-testid="recording-item"]');
    const count = await recordings.count();
    
    if (count > 0) {
      // Click first recording
      await recordings.first().click();
      
      // Verify transcript is shown
      await expect(page.locator('[data-testid="call-transcript"]')).toBeVisible();
    }
  });

  test('should test voice AI health', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/ai/health`);
    expect(response.ok()).toBeTruthy();
    
    const health = await response.json();
    expect(health.deepgram).toBeDefined();
    expect(health.elevenlabs).toBeDefined();
  });
});

/**
 * AI Monitoring Dashboard Tests
 */
test.describe('AI Monitoring Dashboard E2E', () => {
  test('should display comprehensive monitoring dashboard', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/monitoring`);
    
    // Check all key sections are visible
    await expect(page.locator('[data-testid="system-health"]')).toBeVisible();
    await expect(page.locator('[data-testid="ai-metrics"]')).toBeVisible();
    await expect(page.locator('[data-testid="active-alerts"]')).toBeVisible();
    await expect(page.locator('[data-testid="predictive-warnings"]')).toBeVisible();
  });

  test('should show AI metrics for all channels', async ({ page, request }) => {
    const response = await request.get(`${API_URL}/api/v1/monitoring/dashboard/`);
    expect(response.ok()).toBeTruthy();
    
    const dashboard = await response.json();
    expect(dashboard.ai_metrics).toBeDefined();
    expect(dashboard.ai_metrics.channels).toBeDefined();
    
    // Check all channels are tracked
    const channels = dashboard.ai_metrics.channels;
    expect(channels.email).toBeDefined();
    expect(channels.sms).toBeDefined();
    expect(channels.instagram).toBeDefined();
    expect(channels.facebook).toBeDefined();
    expect(channels.phone).toBeDefined();
  });

  test('should create and trigger custom alert rules', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/monitoring/rules`);
    
    // Create new rule
    await page.click('[data-testid="create-rule-button"]');
    
    await page.fill('[name="name"]', 'High Voice AI Cost');
    await page.fill('[name="metric_name"]', 'ai.costs.hourly');
    await page.fill('[name="threshold"]', '10.0');
    await page.selectOption('[name="operator"]', 'greater_than');
    await page.selectOption('[name="severity"]', 'warning');
    
    await page.click('[data-testid="save-rule-button"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toContainText(
      'Rule created'
    );
  });
});

/**
 * Omnichannel Integration Tests
 */
test.describe('Omnichannel Integration E2E', () => {
  test('should show unified customer view across all channels', async ({ page }) => {
    await loginAsAdmin(page);
    
    const customerPhone = '+19167408768';
    
    // Search for customer
    await page.goto(`${BASE_URL}/admin/customers`);
    await page.fill('[data-testid="search-input"]', customerPhone);
    await page.press('[data-testid="search-input"]', 'Enter');
    
    // Click first result
    await page.click('[data-testid="customer-row"]');
    
    // Verify all channel interactions are shown
    await expect(page.locator('[data-testid="email-interactions"]')).toBeVisible();
    await expect(page.locator('[data-testid="sms-interactions"]')).toBeVisible();
    await expect(page.locator('[data-testid="social-interactions"]')).toBeVisible();
    await expect(page.locator('[data-testid="voice-interactions"]')).toBeVisible();
  });

  test('should handle cross-channel conversation flow', async ({ page, request }) => {
    const customerId = 'test_customer_123';
    
    // 1. Customer sends SMS
    await request.post(`${API_URL}/api/v1/webhooks/ringcentral/sms`, {
      data: {
        from: { phoneNumber: '+19167408768' },
        body: 'I have a question'
      }
    });
    
    // 2. Customer sends Instagram DM
    await request.post(`${API_URL}/api/v1/webhooks/instagram`, {
      data: {
        entry: [{
          messaging: [{
            sender: { id: customerId },
            message: { text: 'Same question on Instagram' }
          }]
        }]
      }
    });
    
    // 3. Check admin sees unified view
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/conversations`);
    
    // Filter by customer
    await page.fill('[data-testid="customer-filter"]', '+19167408768');
    
    // Should see conversations from both channels
    const conversations = page.locator('[data-testid="conversation-item"]');
    await expect(conversations).toHaveCount(2, { timeout: 10000 });
  });
});

/**
 * Performance & Load Tests
 */
test.describe('Performance Tests', () => {
  test('should handle concurrent requests across all channels', async ({ request }) => {
    const requests = [
      // Email
      request.post(`${API_URL}/api/v1/test/email`, {
        data: { to: 'test@example.com', subject: 'Test', body: 'Test' }
      }),
      // SMS
      request.post(`${API_URL}/api/v1/sms/send`, {
        data: { to: '+19167408768', message: 'Test SMS' }
      }),
      // Instagram webhook
      request.post(`${API_URL}/api/v1/webhooks/instagram`, {
        data: { entry: [] }
      }),
      // Facebook webhook
      request.post(`${API_URL}/api/v1/webhooks/facebook`, {
        data: { entry: [] }
      }),
      // Voice webhook
      request.post(`${API_URL}/api/v1/webhooks/ringcentral/voice/inbound`, {
        data: { body: { id: 'test', from: {}, to: {} } }
      })
    ];
    
    const startTime = Date.now();
    const responses = await Promise.all(requests);
    const endTime = Date.now();
    
    const duration = endTime - startTime;
    
    // All requests should succeed
    responses.forEach(response => {
      expect(response.status()).toBeLessThan(500);
    });
    
    // Should complete in reasonable time
    expect(duration).toBeLessThan(10000); // 10 seconds for all 5 channels
  });

  test('should maintain performance under load', async ({ page, request }) => {
    const iterations = 20;
    const requests = [];
    
    for (let i = 0; i < iterations; i++) {
      requests.push(
        request.get(`${API_URL}/api/v1/monitoring/dashboard/health`)
      );
    }
    
    const startTime = Date.now();
    const responses = await Promise.all(requests);
    const endTime = Date.now();
    
    const avgResponseTime = (endTime - startTime) / iterations;
    
    // Average response should be fast
    expect(avgResponseTime).toBeLessThan(500); // 500ms average
    
    // All requests should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });
  });
});

/**
 * Error Handling Tests
 */
test.describe('Error Handling E2E', () => {
  test('should handle invalid email gracefully', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/test/email`, {
      data: {
        to: 'invalid-email',
        subject: 'Test',
        body: 'Test'
      }
    });
    
    expect(response.status()).toBe(400);
  });

  test('should handle missing API keys gracefully', async ({ request }) => {
    // This will fail if voice AI keys are not configured
    const response = await request.get(`${API_URL}/api/ai/health`);
    
    if (!response.ok()) {
      const data = await response.json();
      expect(data.deepgram?.status).toBeDefined();
      expect(data.elevenlabs?.status).toBeDefined();
    }
  });

  test('should show error messages in UI', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/admin/settings`);
    
    // Try to save invalid settings
    await page.fill('[name="invalid_field"]', 'bad_value');
    await page.click('[data-testid="save-button"]');
    
    // Should show error
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  });
});
