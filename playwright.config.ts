import { defineConfig } from '@playwright/test';

const baseURL = process.env.BASE_URL || 'http://127.0.0.1:3000';

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  use: { baseURL, headless: true },
  projects: [
    { name: 'customer', testDir: 'e2e/customer' },
    { name: 'admin', testDir: 'e2e/admin' },
  ],
});
