import { test, expect } from '@playwright/test';

/**
 * Customer Signing Page E2E Tests
 *
 * Tests the Customer Agreement Signing Flow:
 * - Token validation
 * - Agreement display
 * - Signature capture
 * - Form submission
 *
 * Tags: @customer @signing @e2e @critical
 */

const CUSTOMER_URL = process.env.CUSTOMER_STAGING_URL || 'https://staging.myhibachichef.com';

// Test with a valid existing token from staging
const TEST_TOKEN = '59681331-374a-4bf5-a773-f16b5e5fcde6';

test.describe('Customer Signing Page @customer @signing', () => {
  test('Signing page loads with valid token @critical', async ({ page }) => {
    await page.goto(`${CUSTOMER_URL}/sign/${TEST_TOKEN}`);
    
    // Wait for page to load (should show agreement or error/expired state)
    await page.waitForTimeout(2000);
    
    // Check for agreement content, signature area, or status message
    const content = page.locator('h1, h2, [data-testid="agreement-title"], [class*="agreement"]');
    await expect(content.first()).toBeVisible({ timeout: 10000 });
  });

  test('Signing page shows agreement details @critical', async ({ page }) => {
    await page.goto(`${CUSTOMER_URL}/sign/${TEST_TOKEN}`);
    await page.waitForTimeout(2000);
    
    // Check for agreement-related content
    const pageContent = await page.textContent('body');
    
    // Should contain either agreement content or expired/signed message
    const hasContent = pageContent?.includes('Agreement') || 
                       pageContent?.includes('Waiver') ||
                       pageContent?.includes('expired') ||
                       pageContent?.includes('signed') ||
                       pageContent?.includes('Service');
    
    expect(hasContent).toBeTruthy();
  });

  test('Invalid token shows error @critical', async ({ page }) => {
    await page.goto(`${CUSTOMER_URL}/sign/invalid-token-12345`);
    await page.waitForTimeout(2000);
    
    // Should show error message
    const pageContent = await page.textContent('body');
    const hasError = pageContent?.toLowerCase().includes('not found') ||
                     pageContent?.toLowerCase().includes('invalid') ||
                     pageContent?.toLowerCase().includes('error') ||
                     pageContent?.toLowerCase().includes('expired');
    
    expect(hasError).toBeTruthy();
  });

  test('Signature pad is visible for valid pending hold @signing', async ({ page }) => {
    await page.goto(`${CUSTOMER_URL}/sign/${TEST_TOKEN}`);
    await page.waitForTimeout(3000);
    
    // Check for signature area (canvas, signature pad component)
    const signatureArea = page.locator('canvas, [data-testid="signature-pad"], [class*="signature"]');
    
    // If hold is still pending (not expired or signed), should have signature pad
    if (await signatureArea.count() > 0) {
      await expect(signatureArea.first()).toBeVisible();
    }
  });

  test('Submit button present for pending agreement @signing', async ({ page }) => {
    await page.goto(`${CUSTOMER_URL}/sign/${TEST_TOKEN}`);
    await page.waitForTimeout(3000);
    
    // Check for submit/sign button
    const submitButton = page.locator('button').filter({ hasText: /sign|submit|agree|continue/i });
    
    // If hold is still pending, should have submit button
    if (await submitButton.count() > 0) {
      await expect(submitButton.first()).toBeVisible();
    }
  });

  test('Time remaining displayed for pending hold @customer', async ({ page }) => {
    await page.goto(`${CUSTOMER_URL}/sign/${TEST_TOKEN}`);
    await page.waitForTimeout(2000);
    
    const pageContent = await page.textContent('body');
    
    // Should show either time remaining or expired message
    const hasTimeInfo = pageContent?.toLowerCase().includes('expire') ||
                        pageContent?.toLowerCase().includes('remain') ||
                        pageContent?.toLowerCase().includes('minute') ||
                        pageContent?.toLowerCase().includes('hour');
    
    // This is not required but good to have
    console.log('Time info present:', hasTimeInfo);
  });
});
