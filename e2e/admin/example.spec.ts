import { test, expect } from '@playwright/test';

test('admin dashboard shows', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/MyHibachi Admin/i);
  await expect(page.locator('text=MyHibachi Admin')).toBeVisible();
  await expect(page.locator('text=Dashboard')).toBeVisible();
});
