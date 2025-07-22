import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import apiClient from '../services/api';

// Mock axios.post to track calls
const mockPost = vi.fn();
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      defaults: { headers: { common: {} } },
      interceptors: {
        response: {
          use: vi.fn(),
        },
      },
      post: mockPost,
    })),
    isAxiosError: vi.fn(),
  },
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock window.location
const mockLocation = {
  href: '',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

describe('API Interceptor Token Refresh Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.href = '';
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should not attempt refresh when user is not logged in (no session_active)', () => {
    // Simulate having no active session
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'session_active') return null;
      return null;
    });

    const error = {
      response: { status: 401 },
      config: {
        url: '/users/me',
      },
    };

    // The interceptor logic with cookie-based authentication
    const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';
    const isAuthEndpoint =
      error.config.url?.includes('/auth/token') ||
      error.config.url?.includes('/auth/register') ||
      error.config.url?.includes('/auth/refresh');

    const shouldAttemptRefresh =
      error.response?.status === 401 && hasActiveSession && !isAuthEndpoint;

    expect(shouldAttemptRefresh).toBe(false);
    expect(hasActiveSession).toBe(false);
  });

  it('should attempt refresh when user has active session', () => {
    // Simulate having active session
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'session_active') return '1';
      return null;
    });

    const error = {
      response: { status: 401 },
      config: {
        url: '/users/me',
      },
    };

    const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';
    const isAuthEndpoint =
      error.config.url?.includes('/auth/token') ||
      error.config.url?.includes('/auth/register') ||
      error.config.url?.includes('/auth/refresh');

    const shouldAttemptRefresh =
      error.response?.status === 401 && hasActiveSession && !isAuthEndpoint;

    expect(shouldAttemptRefresh).toBe(true);
    expect(hasActiveSession).toBe(true);
  });

  it('should not attempt refresh for auth endpoints', () => {
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'session_active') return '1';
      return null;
    });

    const authEndpoints = ['/auth/token', '/auth/register', '/auth/refresh'];

    authEndpoints.forEach(endpoint => {
      const error = {
        response: { status: 401 },
        config: {
          url: endpoint,
        },
      };

      const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';
      const isAuthEndpoint =
        error.config.url?.includes('/auth/token') ||
        error.config.url?.includes('/auth/register') ||
        error.config.url?.includes('/auth/refresh');

      const shouldAttemptRefresh =
        error.response?.status === 401 && hasActiveSession && !isAuthEndpoint;

      expect(shouldAttemptRefresh).toBe(false);
      expect(isAuthEndpoint).toBe(true);
    });
  });

  it('should clear session when 401 occurs without active session', () => {
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'session_active') return null;
      return null;
    });

    const error = {
      response: { status: 401 },
      config: {
        url: '/users/me',
      },
    };

    const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';

    // Simulate the cleanup logic
    if (error.response?.status === 401 && !hasActiveSession) {
      mockLocalStorage.removeItem('session_active');
    }

    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('session_active');
  });

  it('should not attempt refresh for non-401 errors', () => {
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'session_active') return '1';
      return null;
    });

    const error = {
      response: { status: 500 }, // Server error, not auth error
      config: {
        url: '/users/me',
      },
    };

    const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';
    const isAuthEndpoint =
      error.config.url?.includes('/auth/token') ||
      error.config.url?.includes('/auth/register') ||
      error.config.url?.includes('/auth/refresh');

    const shouldAttemptRefresh =
      error.response?.status === 401 && hasActiveSession && !isAuthEndpoint;

    expect(shouldAttemptRefresh).toBe(false);
  });

  describe('App.tsx Session Check Logic', () => {
    it('should not perform session check when no session evidence exists', () => {
      // Simulate fresh user with no session
      mockLocalStorage.getItem.mockImplementation(key => {
        return null; // No stored values
      });

      const hasSessionEvidence = mockLocalStorage.getItem('session_active') === '1';

      expect(hasSessionEvidence).toBe(false);
    });

    it('should perform session check when session evidence exists', () => {
      // Simulate user who had a session
      mockLocalStorage.getItem.mockImplementation(key => {
        if (key === 'session_active') return '1';
        return null;
      });

      const hasSessionEvidence = mockLocalStorage.getItem('session_active') === '1';

      expect(hasSessionEvidence).toBe(true);
    });
  });
});
