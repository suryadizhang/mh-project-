import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';

// Load .env file from project root
dotenv.config();

/**
 * Staging E2E Testing Configuration
 *
 * This config is used to test the STAGING environment before promoting to production.
 * Staging uses isolated database (myhibachi_staging) and test data.
 *
 * PREREQUISITES:
 *   - Set VERCEL_AUTOMATION_BYPASS_SECRET in .env (from Vercel dashboard)
 *   - Staging backend must be running: https://staging-api.mysticdatanode.net
 *
 * Usage:
 *   npx playwright test --config=playwright.staging.config.ts
 *   npm run test:e2e:staging
 *
 * Environment Variables:
 *   VERCEL_AUTOMATION_BYPASS_SECRET - Bypass Vercel Deployment Protection
 *   STAGING_URL - Customer frontend URL (optional)
 *   STAGING_ADMIN_URL - Admin frontend URL (optional)
 *   STAGING_API_URL - Backend API URL (optional)
 *
 * Environment URLs:
 *   - Customer Frontend: https://staging.myhibachichef.com
 *   - Admin Frontend: https://admin-staging.mysticdatanode.net
 *   - Backend API: https://staging-api.mysticdatanode.net
 *   - Database: myhibachi_staging (isolated from production)
 */

const stagingCustomerURL =
  process.env.STAGING_URL ||
  process.env.BASE_URL ||
  'https://staging.myhibachichef.com';

const stagingAdminURL =
  process.env.STAGING_ADMIN_URL || 'https://admin-staging.mysticdatanode.net';

const stagingAPIURL =
  process.env.STAGING_API_URL || 'https://staging-api.mysticdatanode.net';

// Vercel Deployment Protection bypass (from Vercel dashboard)
const vercelBypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET || '';

export default defineConfig({
  testDir: './e2e',

  // Longer timeout for staging (network latency)
  timeout: 90_000,

  // Expect timeout for assertions
  expect: {
    timeout: 10_000,
  },

  // Retry failed tests (network issues)
  retries: process.env.CI ? 2 : 1,

  // Run tests in parallel
  workers: process.env.CI ? 2 : 1,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report-staging' }],
    ['json', { outputFile: 'test-results/staging-results.json' }],
    ['list'],
  ],

  // Shared settings
  use: {
    // Base URL for customer frontend
    baseURL: stagingCustomerURL,

    // Always headless on staging tests
    headless: true,

    // Capture screenshots on failure
    screenshot: 'only-on-failure',

    // Capture video on failure
    video: 'retain-on-failure',

    // Capture trace on first retry
    trace: 'on-first-retry',

    // Viewport size
    viewport: { width: 1280, height: 720 },

    // User agent (identify as Playwright for debugging)
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Playwright/Staging',

    // Navigation timeout
    navigationTimeout: 30_000,

    // Action timeout
    actionTimeout: 10_000,

    // Extra HTTP headers (includes Vercel bypass for protected deployments)
    extraHTTPHeaders: {
      'X-Test-Environment': 'staging',
      // Bypass Vercel Deployment Protection (required for staging)
      ...(vercelBypassSecret && {
        'x-vercel-protection-bypass': vercelBypassSecret,
      }),
    },
  },

  // Test projects for staging environment
  projects: [
    // Customer frontend tests (Desktop)
    {
      name: 'staging-customer-desktop',
      testDir: 'e2e/customer',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: stagingCustomerURL,
      },
    },

    // Customer frontend tests (Mobile)
    {
      name: 'staging-customer-mobile',
      testDir: 'e2e/customer',
      use: {
        ...devices['iPhone 13'],
        baseURL: stagingCustomerURL,
      },
    },

    // Admin frontend tests
    {
      name: 'staging-admin-desktop',
      testDir: 'e2e/admin',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: stagingAdminURL,
      },
    },

    // API tests (staging backend)
    {
      name: 'staging-api',
      testDir: 'e2e/api',
      use: {
        baseURL: stagingAPIURL,
      },
    },
  ],

  // No webServer block - we test against live staging URLs, not local dev
  // webServer: undefined,
});
