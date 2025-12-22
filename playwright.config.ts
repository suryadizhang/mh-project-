import { defineConfig } from '@playwright/test';

const baseURL = process.env.BASE_URL || 'http://localhost:3000';

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  use: {
    baseURL,
    headless: true,
    trace: 'on-first-retry',
  },
  retries: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  projects: [
    { name: 'customer', testDir: 'e2e/customer' },
    { name: 'admin', testDir: 'e2e/admin' },
    { name: 'api', testDir: 'e2e/api' },
  ],
  // Auto-start dev server for tests
  webServer: {
    command: 'npm run dev:customer',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
