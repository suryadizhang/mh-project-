import '@testing-library/jest-dom/vitest';

import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

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
