import { test, expect } from '@playwright/test';

// Critical pages for visual regression testing
const criticalPages = [
  '/',
  '/menu',
  '/book-us',
  '/quote',
  '/contact',
  '/blog',
  '/locations',
  '/locations/mountain-view',
  '/payment',
];

test.describe('Visual Regression Tests - Critical Pages', () => {
  criticalPages.forEach((page) => {
    test(`Visual regression test for ${page}`, async ({ page: playwright }) => {
      // Navigate to the page
      await playwright.goto(page);

      // Wait for page to be fully loaded
      await playwright.waitForLoadState('networkidle');

      // Wait for any loading states to complete
      await playwright.waitForTimeout(2000);

      // Hide dynamic content that changes (timestamps, etc.)
      await playwright.addStyleTag({
        content: `
          [data-testid="timestamp"],
          .timestamp,
          .last-updated,
          .current-time {
            visibility: hidden !important;
          }
        `,
      });

      // Take full page screenshot
      await expect(playwright).toHaveScreenshot(`${page.replace(/\//g, '_')}-full-page.png`, {
        fullPage: true,
        threshold: 0.3, // Allow 30% difference for minor rendering variations
      });
    });
  });
});

test.describe('Visual Regression Tests - Interactive Elements', () => {
  test('Booking form interactions', async ({ page }) => {
    await page.goto('/book-us/');
    await page.waitForLoadState('networkidle');

    // Test form in different states
    await expect(page).toHaveScreenshot('booking-form-initial.png');

    // Fill out some form fields
    await page.fill('input[name="name"]', 'Test User');
    await page.fill('input[name="email"]', 'test@example.com');

    await expect(page).toHaveScreenshot('booking-form-filled.png');
  });

  test('Menu page responsiveness', async ({ page }) => {
    await page.goto('/menu');
    await page.waitForLoadState('networkidle');

    // Test menu sections
    await expect(page).toHaveScreenshot('menu-page-loaded.png');
  });

  test('Payment page layout', async ({ page }) => {
    await page.goto('/payment');
    await page.waitForLoadState('networkidle');

    // Test payment form layout
    await expect(page).toHaveScreenshot('payment-page-layout.png');
  });
});

test.describe('Visual Regression Tests - Navigation', () => {
  test('Navigation menu states', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test mobile menu if on mobile viewport
    const viewport = page.viewportSize();
    if (viewport && viewport.width <= 768) {
      // Click mobile menu button if it exists
      const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
      if (await mobileMenuButton.isVisible()) {
        await mobileMenuButton.click();
        await expect(page).toHaveScreenshot('mobile-menu-open.png');
      }
    }

    // Test desktop navigation
    await expect(page).toHaveScreenshot('navigation-default.png');
  });
});
