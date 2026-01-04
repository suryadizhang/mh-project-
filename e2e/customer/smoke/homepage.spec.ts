import { test, expect, Page } from '@playwright/test';

/**
 * Customer Frontend Smoke Tests
 *
 * Quick tests to verify basic functionality
 * These run fast and don't require backend
 *
 * Tags: @smoke
 * Services needed: Frontend only
 *
 * Updated: 2025-01-04 to match actual production site
 *
 * Note: Some mobile tests are skipped because mobile has hamburger menu
 * which requires different interaction patterns
 */

// Helper to open mobile menu if needed
async function openMobileMenuIfNeeded(
  page: Page,
  testInfo: { project: { name: string } }
) {
  if (testInfo.project.name.includes('mobile')) {
    // Mobile viewport - try to open hamburger menu
    // Common selectors for mobile menu buttons
    const mobileMenuButton = page
      .locator(
        'button[aria-label*="menu" i], ' +
          'button[aria-label*="navigation" i], ' +
          'button.navbar-toggler, ' +
          '[data-bs-toggle="collapse"], ' +
          'button[class*="hamburger"], ' +
          'button[class*="mobile-menu"], ' +
          '.menu-toggle, ' +
          '[aria-expanded]'
      )
      .first();

    if (
      await mobileMenuButton.isVisible({ timeout: 2000 }).catch(() => false)
    ) {
      await mobileMenuButton.click();
      // Wait for menu animation
      await page.waitForTimeout(500);
      return true;
    }
  }
  return false;
}

test.describe('Homepage', () => {
  test('loads successfully @smoke', async ({ page }) => {
    // Navigate and wait for load state
    await page.goto('/', { waitUntil: 'domcontentloaded' });

    // Wait for page to fully load before checking title
    await page.waitForLoadState('load');

    // Verify page loads - actual title is "My Hibachi Chef - Premium Mobile Hibachi Catering..."
    await expect(page).toHaveTitle(/My Hibachi/i, { timeout: 15000 });

    // Verify main heading exists (different formats on different pages)
    await expect(page.locator('h1').first()).toBeVisible();
  });

  test('displays hero section @smoke', async ({ page }) => {
    await page.goto('/');

    // Verify hero content - look for Book Now button or similar CTA
    const bookNowButton = page.getByRole('link', {
      name: /book now|get.*quote/i,
    });
    await expect(bookNowButton.first()).toBeVisible();
  });

  // Works on both desktop and mobile (with hamburger menu handling)
  test('shows navigation menu @smoke', async ({
    page,
    browserName,
  }, testInfo) => {
    await page.goto('/');

    // Open mobile menu if on mobile
    await openMobileMenuIfNeeded(page, testInfo);

    // Verify nav exists
    await expect(page.locator('nav').first()).toBeVisible();

    // Verify key nav links using more specific selectors
    // On mobile, these should be visible after opening hamburger menu
    await expect(page.getByRole('link', { name: /menu/i }).first()).toBeVisible(
      { timeout: 5000 }
    );
  });

  test('is mobile responsive @smoke', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Verify page loads on mobile
    await expect(page.locator('body')).toBeVisible();

    // Check for mobile menu button (hamburger)
    const mobileMenuButton = page
      .locator(
        '[aria-label*="menu" i], button.navbar-toggler, [data-bs-toggle="collapse"]'
      )
      .first();
    if (await mobileMenuButton.isVisible()) {
      await mobileMenuButton.click();
      // After click, nav should be visible
      await expect(page.locator('nav').first()).toBeVisible();
    }
  });
});

test.describe('Navigation', () => {
  test('can navigate to booking page @smoke', async ({ page }) => {
    await page.goto('/');

    // Click on Book Now or similar CTA - goes to /quote/ page
    const bookNowLink = page
      .getByRole('link', { name: /book now|get.*quote/i })
      .first();
    await bookNowLink.click();

    // URL should contain quote or BookUs (booking flow pages)
    await expect(page).toHaveURL(/.*(?:quote|BookUs)/i);
  });

  // Works on both desktop and mobile (with hamburger menu handling)
  test('can navigate to menu page @smoke', async ({ page }, testInfo) => {
    await page.goto('/');

    // Open mobile menu if on mobile
    await openMobileMenuIfNeeded(page, testInfo);

    // Use nav link specifically to avoid multiple matches
    await page.getByRole('link', { name: /menu/i }).first().click();
    await expect(page).toHaveURL(/.*menu/i);
  });

  // Works on both desktop and mobile (with hamburger menu handling)
  test('can navigate to contact page @smoke', async ({ page }, testInfo) => {
    await page.goto('/');

    // Open mobile menu if on mobile
    await openMobileMenuIfNeeded(page, testInfo);

    // Use nav link specifically
    await page
      .getByRole('link', { name: /contact/i })
      .first()
      .click();
    await expect(page).toHaveURL(/.*contact/i);
  });

  test('logo links to homepage @smoke', async ({ page }) => {
    await page.goto('/menu/');

    // Click logo/brand link to go home
    const logoLink = page
      .locator('a')
      .filter({
        has: page.locator('img[alt*="hibachi" i], img[alt*="logo" i]'),
      })
      .first();
    if (await logoLink.isVisible()) {
      await logoLink.click();
    } else {
      // Fallback: click navbar brand
      await page.locator('.navbar-brand, a[href="/"]').first().click();
    }
    await expect(page).toHaveURL('/');
  });
});

test.describe('Menu Page', () => {
  test('displays menu content @smoke', async ({ page }) => {
    await page.goto('/menu/');

    // Verify menu page has pricing information visible
    // The actual menu shows prices like $55, $30, etc.
    await expect(
      page.locator('.pricing-amount, .price-tag').first()
    ).toBeVisible();
  });

  // Works on both desktop and mobile
  test('shows prices @smoke', async ({ page }) => {
    await page.goto('/menu/');

    // Verify at least one price is shown - use first() to avoid strict mode violation
    await expect(page.locator('.pricing-amount').first()).toBeVisible();
  });
});

test.describe('Footer', () => {
  // Works on both desktop and mobile - scroll to footer first
  test('displays footer content @smoke', async ({ page }) => {
    await page.goto('/');

    // Scroll to footer
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500); // Wait for scroll to complete

    // Verify footer elements
    await expect(page.locator('footer')).toBeVisible();

    // Check for copyright text - using dynamic year (2024-2030)
    await expect(
      page
        .locator('footer')
        .getByText(/©.*20(2[4-9]|30)|copyright|All rights reserved/i)
        .first()
    ).toBeVisible();
  });

  // Works on both desktop and mobile - scroll to footer first
  test('shows social media links @smoke', async ({ page }) => {
    await page.goto('/');

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500); // Wait for scroll to complete

    // Check for social links - footer uses ig.me/m for Instagram DM and m.me for Facebook Messenger
    const footer = page.locator('footer');
    await expect(
      footer
        .locator(
          'a[href*="ig.me"], a[href*="m.me"], a[href*="facebook"], a[href*="instagram"]'
        )
        .first()
    ).toBeVisible();
  });
});

test.describe('Performance', () => {
  test('loads within acceptable time @smoke @performance', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Should load in less than 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });
});

test.describe('SEO', () => {
  // Works on both desktop and mobile
  test('has proper meta tags @smoke @seo', async ({ page }) => {
    // Navigate to homepage first!
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('load');

    const description = await page.getAttribute(
      'meta[name="description"]',
      'content'
    );
    expect(description).toBeTruthy();
    expect(description!.length).toBeGreaterThan(50);
    expect(description!.length).toBeLessThan(200); // Allow slightly longer descriptions
  });
});
