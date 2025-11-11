import { test, expect } from '@playwright/test';

/**
 * Customer Frontend Smoke Tests
 * 
 * Quick tests to verify basic functionality
 * These run fast and don't require backend
 * 
 * Tags: @smoke
 * Services needed: Frontend only
 */
test.describe('Homepage', () => {
  test('loads successfully @smoke', async ({ page }) => {
    await page.goto('/');
    
    // Verify page loads
    await expect(page).toHaveTitle(/MyHibachi/i);
    
    // Verify main heading
    await expect(page.locator('h1')).toContainText('MyHibachi');
  });
  
  test('displays hero section @smoke', async ({ page }) => {
    await page.goto('/');
    
    // Verify hero content
    await expect(page.locator('text=Premium Hibachi Catering')).toBeVisible();
    await expect(page.locator('button:has-text("Book Now")')).toBeVisible();
  });
  
  test('shows navigation menu @smoke', async ({ page }) => {
    await page.goto('/');
    
    // Verify nav links
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('text=Menu')).toBeVisible();
    await expect(page.locator('text=Booking')).toBeVisible();
    await expect(page.locator('text=Contact')).toBeVisible();
  });
  
  test('is mobile responsive @smoke', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Verify mobile menu
    const mobileMenu = page.locator('[aria-label="Mobile menu"]');
    if (await mobileMenu.isVisible()) {
      await mobileMenu.click();
      await expect(page.locator('nav')).toBeVisible();
    }
  });
});

test.describe('Navigation', () => {
  test('can navigate to booking page @smoke', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Book Now');
    await expect(page).toHaveURL(/.*booking/);
  });
  
  test('can navigate to menu page @smoke', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Menu');
    await expect(page).toHaveURL(/.*menu/);
  });
  
  test('can navigate to contact page @smoke', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Contact');
    await expect(page).toHaveURL(/.*contact/);
  });
  
  test('logo links to homepage @smoke', async ({ page }) => {
    await page.goto('/booking');
    
    await page.click('img[alt*="MyHibachi"]');
    await expect(page).toHaveURL('/');
  });
});

test.describe('Menu Page', () => {
  test('displays menu items @smoke', async ({ page }) => {
    await page.goto('/menu');
    
    // Verify menu items displayed
    await expect(page.locator('text=Hibachi Chicken')).toBeVisible();
    await expect(page.locator('text=Hibachi Steak')).toBeVisible();
    await expect(page.locator('text=Fried Rice')).toBeVisible();
  });
  
  test('shows prices @smoke', async ({ page }) => {
    await page.goto('/menu');
    
    // Verify at least one price is shown
    await expect(page.locator('text=/\\$\\d+/')).toBeVisible();
  });
});

test.describe('Footer', () => {
  test('displays footer content @smoke', async ({ page }) => {
    await page.goto('/');
    
    // Scroll to footer
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    // Verify footer elements
    await expect(page.locator('footer')).toBeVisible();
    await expect(page.locator('text=© 2025 MyHibachi')).toBeVisible();
  });
  
  test('shows social media links @smoke', async ({ page }) => {
    await page.goto('/');
    
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    // Check for social links (adjust selectors based on your implementation)
    const footer = page.locator('footer');
    await expect(footer.locator('a[href*="facebook"]').or(footer.locator('a[href*="instagram"]'))).toBeVisible();
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
  test('has proper meta tags @smoke @seo', async ({ page }) => {
    await page.goto('/');
    
    // Check title
    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
    expect(title.length).toBeLessThan(60); // SEO best practice
    
    // Check meta description
    const description = await page.getAttribute('meta[name="description"]', 'content');
    expect(description).toBeTruthy();
    expect(description!.length).toBeGreaterThan(50);
    expect(description!.length).toBeLessThan(160); // SEO best practice
  });
});
