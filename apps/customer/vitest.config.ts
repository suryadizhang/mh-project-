import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    // Test environment
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov', 'json'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/**',
        '.next/**',
        'coverage/**',
        '**/*.d.ts',
        '**/*.config.*',
        '**/test/**',
        '**/__tests__/**',
        '**/*.test.*',
        '**/*.spec.*',
      ],
      thresholds: {
        global: {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
        // Per-file thresholds for critical components
        './src/lib/': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        './src/components/booking/': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90,
        },
      },
    },

    // Test patterns
    // Test file patterns - exclude playwright tests
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/.next/**',
      '**/coverage/**',
      '**/*.d.ts',
      '**/tests/**', // Exclude playwright tests
      '**/e2e/**'    // Exclude e2e tests
    ],

    // Test timeout
    testTimeout: 10000,
    hookTimeout: 10000,

    // Globals
    globals: true,

    // Test results reporting
    reporters: ['verbose', 'html', 'json'],
    outputFile: {
      html: './coverage/test-report.html',
      json: './coverage/test-results.json',
    },
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/lib': path.resolve(__dirname, './src/lib'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/styles': path.resolve(__dirname, './src/styles'),
    },
  },
});
