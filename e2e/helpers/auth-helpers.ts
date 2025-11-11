import { Page } from '@playwright/test';
import { testAdmin } from './test-data';

/**
 * Authentication Helpers
 */

/**
 * Log in as admin user
 */
export async function loginAsAdmin(page: Page) {
  await page.goto('/admin/login');
  
  // Fill login form
  await page.fill('[name="email"]', testAdmin.email);
  await page.fill('[name="password"]', testAdmin.password);
  
  // Submit
  await page.click('button[type="submit"]');
  
  // Wait for redirect to dashboard
  await page.waitForURL('**/admin/dashboard', { timeout: 10000 });
  
  // Verify login success
  await page.waitForSelector('text=Dashboard', { timeout: 5000 });
}

/**
 * Log out
 */
export async function logout(page: Page) {
  // Click user menu
  await page.click('[aria-label="User menu"]');
  
  // Click logout
  await page.click('text=Logout');
  
  // Wait for redirect to login
  await page.waitForURL('**/login');
}

/**
 * Check if user is logged in
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  try {
    await page.waitForSelector('[aria-label="User menu"]', { timeout: 2000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Get API authentication token
 * Useful for API tests
 */
export async function getAuthToken(page: Page): Promise<string> {
  // Login first
  await loginAsAdmin(page);
  
  // Get token from localStorage or cookies
  const token = await page.evaluate(() => {
    return localStorage.getItem('authToken') || '';
  });
  
  return token;
}
