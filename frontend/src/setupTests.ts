// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import { vi } from 'vitest';

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

// Mock window.location for redirect tests
(globalThis as any).mockLocationHref = 'http://localhost:3000';

// Store original location
const originalLocation = window.location;

// Create a simple mock that just tracks href changes
delete (window as any).location;
(window as any).location = {
  get href() { 
    return (globalThis as any).mockLocationHref || 'http://localhost:3000';
  },
  set href(value) { 
    (globalThis as any).mockLocationHref = value;
  },
  assign: vi.fn(),
  reload: vi.fn(),
  replace: vi.fn(),
  origin: 'http://localhost:3000',
  pathname: '/',
  search: '',
  hash: '',
};

// Mock redirect function for API client - always available
(window as any).__TEST_REDIRECT__ = (url: string) => {
  (globalThis as any).mockLocationHref = url;
};

// Ensure test redirect is always available and works correctly
beforeEach(() => {
  // Reset location href
  (globalThis as any).mockLocationHref = 'http://localhost:3000';
  
  // Ensure test redirect function is available
  (window as any).__TEST_REDIRECT__ = (url: string) => {
    (globalThis as any).mockLocationHref = url;
  };
});

// Mock import.meta.env for tests
if (typeof import.meta === 'undefined') {
  (global as any).import = { meta: { env: { VITE_API_URL: 'http://localhost:8000' } } };
}

// MSW – mock API requests at network level
import { server } from './mocks/server';

// Establish API mocking before all tests.
beforeAll(() => server.listen());
// Reset any runtime request handlers we may add during the tests.
afterEach(() => server.resetHandlers());
// Clean up after the tests are finished.
afterAll(() => server.close());
