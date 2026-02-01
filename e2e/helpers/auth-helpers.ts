import { Page } from '@playwright/test';
import { testAdmin } from './test-data';

/**
 * Authentication Helpers
 */

/**
 * Log in as admin user
 *
 * Note: The admin app is a separate Next.js app with baseURL set to
 * admin-staging.mysticdatanode.net, so the login page is at /login (not /admin/login).
 * After login, dashboard is at / (not /admin/dashboard).
 *
 * The login is a MULTI-STEP process:
 * 1. Enter email/password and submit
 * 2. If user has multiple stations → shows station selection dropdown
 * 3. Select a station and submit → redirects to /
 * 4. If user has only 1 station → auto-selects and redirects to /
 */
export async function loginAsAdmin(page: Page) {
  // Navigate to login page (admin app's baseURL is the admin domain)
  await page.goto('/login');

  // Wait for the login form to be fully loaded (handles Suspense loading state)
  // The form uses id="email" and id="password" attributes
  await page.waitForSelector('#email', { state: 'visible', timeout: 15000 });
  await page.waitForSelector('#password', { state: 'visible', timeout: 15000 });

  // Fill login form using id selectors (more reliable than name)
  await page.fill('#email', testAdmin.email);
  await page.fill('#password', testAdmin.password);

  // Submit credentials
  await page.click('button[type="submit"]');

  // Wait for either:
  // 1. Station selection dropdown (multi-station user)
  // 2. Redirect to dashboard (single-station user auto-selects)
  // We use Promise.race with a custom approach

  // First, wait a moment for the response to process
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
    // Network might not fully idle, continue anyway
  });

  // Check if station selection is shown (user has multiple stations)
  const stationSelect = page.locator('#station');
  const isStationSelectVisible = await stationSelect
    .isVisible({ timeout: 3000 })
    .catch(() => false);

  if (isStationSelectVisible) {
    // Multi-station flow: select the first station and submit
    console.log(
      '[loginAsAdmin] Station selection detected, selecting first station...'
    );

    // Wait for options to be populated
    await page.waitForSelector('#station option:not([value=""])', {
      timeout: 5000,
    });

    // Get the first non-empty option value
    const firstOptionValue = await page
      .locator('#station option:not([value=""])')
      .first()
      .getAttribute('value');

    if (firstOptionValue) {
      await stationSelect.selectOption(firstOptionValue);

      // Click the submit button for station selection
      await page.click('button[type="submit"]');
    }
  }

  // Wait for redirect to dashboard
  await page.waitForURL(/^\/$/, { timeout: 15000 });

  // Verify login success - look for dashboard content
  await page
    .waitForSelector('[data-testid="dashboard"], main, nav, h1, header', {
      timeout: 10000,
    })
    .catch(() => {
      // Fallback: just verify we're on the dashboard URL
      console.log(
        '[loginAsAdmin] Dashboard content selector not found, but URL is correct'
      );
    });
}

/**
 * Log out from admin panel
 */
export async function logout(page: Page) {
  // Click user menu (try multiple selectors)
  const userMenuSelector =
    '[aria-label="User menu"], button:has-text("Account"), [data-testid="user-menu"]';
  await page.click(userMenuSelector).catch(async () => {
    // Fallback: look for profile dropdown or settings
    await page.click(
      'button:has([aria-label="profile"]), button:has-text("Logout")'
    );
  });

  // Click logout
  await page.click('text=Logout, text=Sign out, [data-testid="logout-button"]');

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
