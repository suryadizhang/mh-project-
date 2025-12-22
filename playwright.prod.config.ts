import { defineConfig, devices } from '@playwright/test';

/**
 * Production E2E Testing Configuration
 *
 * This config is used to test the LIVE production environment
 * after deployment to verify everything is working correctly.
 *
 * Usage:
 *   npx playwright test --config=playwright.prod.config.ts
 *   BASE_URL=https://yourdomain.com npx playwright test --config=playwright.prod.config.ts
 */

const productionURL =
  process.env.PROD_URL ||
  process.env.BASE_URL ||
  'https://www.myhibachichef.com';
const adminURL = process.env.ADMIN_URL || 'https://admin.mysticdatanode.net';

export default defineConfig({
  testDir: './e2e',

  // Longer timeout for production (network latency)
  timeout: 90_000,

  // Expect timeout for assertions
  expect: {
    timeout: 10_000,
  },

  // Retry failed tests on production (network issues)
  retries: process.env.CI ? 2 : 1,

  // Run tests in parallel
  workers: process.env.CI ? 2 : 1,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report-prod' }],
    ['json', { outputFile: 'test-results/prod-results.json' }],
    ['list'],
  ],

  // Shared settings
  use: {
    // Base URL for customer frontend
    baseURL: productionURL,

    // Always headless on production tests
    headless: true,

    // Capture screenshots on failure
    screenshot: 'only-on-failure',

    // Capture video on failure
    video: 'retain-on-failure',

    // Capture trace on first retry
    trace: 'on-first-retry',

    // Viewport size
    viewport: { width: 1280, height: 720 },

    // User agent
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',

    // Navigation timeout
    navigationTimeout: 30_000,

    // Action timeout
    actionTimeout: 10_000,
  },

  // Test projects for different environments
  projects: [
    // Customer frontend tests (Desktop)
    {
      name: 'customer-desktop',
      testDir: 'e2e/customer',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: productionURL,
      },
    },

    // Customer frontend tests (Mobile)
    {
      name: 'customer-mobile',
      testDir: 'e2e/customer',
      use: {
        ...devices['iPhone 13'],
        baseURL: productionURL,
      },
    },

    // Admin frontend tests
    {
      name: 'admin-desktop',
      testDir: 'e2e/admin',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: adminURL,
      },
    },

    // API tests (direct backend)
    {
      name: 'api',
      testDir: 'e2e/api',
      use: {
        baseURL: process.env.API_URL || 'https://mhapi.mysticdatanode.net',
      },
    },
  ],

  // Global setup/teardown
  // globalSetup: require.resolve('./e2e/global-setup'),
  // globalTeardown: require.resolve('./e2e/global-teardown'),
});
