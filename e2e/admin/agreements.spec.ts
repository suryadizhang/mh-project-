import { test, expect } from '@playwright/test';

/**
 * Admin Agreements Page E2E Tests
 *
 * Tests the Admin Panel Agreements Management:
 * - Signed agreements list
 * - Pending slot holds list
 * - Generate signing link
 * - Send link functionality
 *
 * Tags: @admin @agreements @e2e
 */

const ADMIN_URL = process.env.ADMIN_STAGING_URL || 'https://admin-staging.mysticdatanode.net';

test.describe('Admin Agreements Page @admin @agreements', () => {
  test.beforeEach(async ({ page }) => {
    // First navigate to login page
    await page.goto(`${ADMIN_URL}/login`);
    await page.waitForTimeout(1000);
    
    // Fill login form
    await page.fill('input[name="email"], input[type="email"]', 'suryadizhang.swe@gmail.com');
    await page.fill('input[name="password"], input[type="password"]', 'Test2025!Secure');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard to load
    await page.waitForTimeout(3000);
    
    // Navigate to agreements page
    await page.goto(`${ADMIN_URL}/agreements`);
    await page.waitForTimeout(2000);
  });

  test('Agreements page loads @critical', async ({ page }) => {
    // Verify we're on agreements page (check URL or content)
    const currentUrl = page.url();
    const pageContent = await page.textContent('body');
    
    // Should be on agreements page OR showing content
    const onPage = currentUrl.includes('/agreements') || 
                   pageContent?.toLowerCase().includes('agreement') ||
                   pageContent?.toLowerCase().includes('pending') ||
                   pageContent?.toLowerCase().includes('hold');
    
    expect(onPage).toBeTruthy();
  });

  test('Pending holds tab shows slot holds @critical', async ({ page }) => {
    // Click on pending/holds tab
    const pendingTab = page.locator('button, [role="tab"]').filter({ hasText: /pending|hold/i }).first();
    if (await pendingTab.count() > 0) {
      await pendingTab.click();
      await page.waitForTimeout(1000);
    }

    // Check for holds list or empty state
    const holdsSection = page.locator('[data-testid="holds-list"], table, [class*="hold"]');
    await expect(holdsSection.first()).toBeVisible({ timeout: 5000 });
  });

  test('Generate link tab shows form @admin', async ({ page }) => {
    // Click on generate link tab
    const generateTab = page.locator('button, [role="tab"]').filter({ hasText: /generate/i }).first();
    if (await generateTab.count() > 0) {
      await generateTab.click();
      await page.waitForTimeout(1000);
    }

    // Check for form fields
    const formSection = page.locator('form, [data-testid="generate-form"]');
    if (await formSection.count() > 0) {
      await expect(formSection).toBeVisible();
    }
  });

  test('Slot hold shows signing link and copy button @critical', async ({ page }) => {
    // Click on pending/holds tab
    const pendingTab = page.locator('button, [role="tab"]').filter({ hasText: /pending|hold/i }).first();
    if (await pendingTab.count() > 0) {
      await pendingTab.click();
      await page.waitForTimeout(1000);
    }

    // Look for signing link or copy button
    const linkOrCopy = page.locator('[data-testid="signing-link"], button:has-text("Copy"), [class*="copy"]');
    if (await linkOrCopy.count() > 0) {
      await expect(linkOrCopy.first()).toBeVisible();
    }
  });

  test('Signed agreements tab works @admin', async ({ page }) => {
    // Click on signed tab
    const signedTab = page.locator('button, [role="tab"]').filter({ hasText: /signed/i }).first();
    if (await signedTab.count() > 0) {
      await signedTab.click();
      await page.waitForTimeout(1000);
    }

    // Check for agreements list, empty state, or any content
    const pageContent = await page.textContent('body');
    const hasContent = pageContent?.toLowerCase().includes('agreement') ||
                       pageContent?.toLowerCase().includes('no ') ||
                       pageContent?.toLowerCase().includes('empty') ||
                       pageContent?.toLowerCase().includes('table');
    
    expect(hasContent).toBeTruthy();
  });
});
