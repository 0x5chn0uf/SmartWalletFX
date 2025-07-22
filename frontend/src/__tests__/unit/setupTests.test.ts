import { vi, describe, it, expect, beforeEach } from 'vitest';
import '../../setupTests';
import { server } from '../../mocks/server';

describe('Test Setup', () => {
  describe('IntersectionObserver', () => {
    it('should create IntersectionObserver with default values', () => {
      const callback = vi.fn();
      const observer = new IntersectionObserver(callback);

      expect(observer.root).toBeNull();
      expect(observer.rootMargin).toBe('0px');
      expect(observer.thresholds).toEqual([0]);
    });

    it('should create IntersectionObserver with custom options', () => {
      const callback = vi.fn();
      const root = document.createElement('div');
      const options = {
        root,
        rootMargin: '10px',
        threshold: 0.5,
      };
      const observer = new IntersectionObserver(callback, options);

      expect(observer.root).toBe(root);
      expect(observer.rootMargin).toBe('10px');
      expect(observer.thresholds).toEqual([0.5]);
    });

    it('should have required methods', () => {
      const observer = new IntersectionObserver(() => {});

      expect(typeof observer.observe).toBe('function');
      expect(typeof observer.unobserve).toBe('function');
      expect(typeof observer.disconnect).toBe('function');
      expect(typeof observer.takeRecords).toBe('function');
      expect(observer.takeRecords()).toEqual([]);
    });
  });

  describe('window.matchMedia', () => {
    it('should mock matchMedia methods', () => {
      const mediaQuery = window.matchMedia('(min-width: 768px)');

      expect(typeof mediaQuery.addEventListener).toBe('function');
      expect(typeof mediaQuery.removeEventListener).toBe('function');
      expect(typeof mediaQuery.removeListener).toBe('function');
      expect(typeof mediaQuery.dispatchEvent).toBe('function');
    });

    it('should handle event listeners', () => {
      const mediaQuery = window.matchMedia('(min-width: 768px)');
      const listener = vi.fn();

      mediaQuery.addEventListener('change', listener);
      mediaQuery.removeEventListener('change', listener);
      mediaQuery.removeListener(listener); // Test deprecated method

      // Verify the mock functions were called
      expect(mediaQuery.addEventListener).toHaveBeenCalledWith('change', listener);
      expect(mediaQuery.removeEventListener).toHaveBeenCalledWith('change', listener);
      expect(mediaQuery.removeListener).toHaveBeenCalledWith(listener);
    });
  });

  describe('ResizeObserver', () => {
    let element: HTMLElement;

    beforeEach(() => {
      element = document.createElement('div');
    });

    it('should create ResizeObserver with required methods', () => {
      const observer = new ResizeObserver(() => {});

      expect(typeof observer.observe).toBe('function');
      expect(typeof observer.unobserve).toBe('function');
      expect(typeof observer.disconnect).toBe('function');
    });

    it('should handle observe and unobserve calls', () => {
      const observer = new ResizeObserver(() => {});

      // These should not throw errors
      expect(() => observer.observe(element)).not.toThrow();
      expect(() => observer.unobserve(element)).not.toThrow();
      expect(() => observer.disconnect()).not.toThrow();
    });
  });

  describe('Axios setup', () => {
    it('should have axios methods available', async () => {
      const axios = (await import('axios')).default;

      expect(typeof axios.get).toBe('function');
      expect(typeof axios.post).toBe('function');
      expect(typeof axios.put).toBe('function');
      expect(typeof axios.delete).toBe('function');

      // We use MSW for network mocking instead of axios mocks
      // so axios methods should be real functions, not mocks
      expect(vi.isMockFunction(axios.get)).toBe(false);
      expect(vi.isMockFunction(axios.post)).toBe(false);
      expect(vi.isMockFunction(axios.put)).toBe(false);
      expect(vi.isMockFunction(axios.delete)).toBe(false);
    });
  });

  describe('MSW Setup', () => {
    it('should have MSW server with required lifecycle methods', () => {
      expect(typeof server.listen).toBe('function');
      expect(typeof server.resetHandlers).toBe('function');
      expect(typeof server.close).toBe('function');
    });
  });
});
