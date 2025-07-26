import * as matchers from '@testing-library/jest-dom/matchers';
import '@testing-library/jest-dom';
import { afterEach, beforeAll, afterAll, vi, expect } from 'vitest';
import { cleanup } from '@testing-library/react';

// Extend expect with jest-dom matchers
expect.extend(matchers);

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  root: Element | null;
  rootMargin: string;
  thresholds: ReadonlyArray<number>;

  constructor(
    private callback: IntersectionObserverCallback,
    private options: IntersectionObserverInit = {}
  ) {
    this.root = options.root instanceof Element ? options.root : null;
    this.rootMargin = options.rootMargin || '0px';
    this.thresholds = Array.isArray(options.threshold)
      ? options.threshold
      : [options.threshold ?? 0];
  }

  observe(target: Element) {
    // You can trigger the callback with mock entries here if needed
  }

  unobserve(target: Element) {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
};

// @ts-ignore
window.matchMedia =
  window.matchMedia ||
  function () {
    return {
      removeListener: vi.fn(), // deprecated
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    };
  };

// Polyfill ResizeObserver used by Recharts in tests
class ResizeObserver {
  observe(target: Element) {}
  unobserve(target: Element) {}
  disconnect() {}
}

// @ts-ignore
global.ResizeObserver = ResizeObserver;

// MSW – mock API requests at network level
import { server } from '../mocks/server';

// Establish API mocking before all tests.
beforeAll(() => server.listen());
// Reset any runtime request handlers we may add during the tests.
afterEach(() => {
  server.resetHandlers();
  cleanup();
});
// Clean up after the tests are finished.
afterAll(() => server.close());
