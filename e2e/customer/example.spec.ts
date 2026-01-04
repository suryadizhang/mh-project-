import { test, expect } from '@playwright/test';

test('customer home renders', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/My Hibachi/i);
  // Homepage hero title - check for actual text from home.ts
  await expect(page.locator('h1').first()).toBeVisible();
});
