import { test, expect } from '@playwright/test';

test('customer home renders', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/My Hibachi/i);
  await expect(page.locator('h1')).toContainText('MyHibachi');
});
