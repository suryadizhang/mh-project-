import '@testing-library/jest-dom/vitest';

import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll } from 'vitest';

// Suppress React act warnings in tests - they're expected for async hook tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: An update to') &&
      args[0].includes('was not wrapped in act')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock WebSocket
global.WebSocket = class MockWebSocket {
  url: string;
  readyState: number = 0;

  constructor(url: string) {
    this.url = url;
  }

  send() {}
  close() {}
} as unknown as typeof WebSocket;
