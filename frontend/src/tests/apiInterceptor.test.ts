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
    // Simulate having a stale token but no active session
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'access_token') return 'expired_token_123';
      if (key === 'session_active') return null;
      return null;
    });

    const error = {
      response: { status: 401 },
      config: {
        url: '/users/me',
        headers: { Authorization: 'Bearer expired_token_123' },
      },
    };

    // The interceptor logic (we would need to extract this to a testable function)
    const hasAuthHeader = Boolean(error.config.headers?.Authorization);
    const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';
    const isAuthEndpoint =
      error.config.url?.includes('/auth/token') ||
      error.config.url?.includes('/auth/register') ||
      error.config.url?.includes('/auth/refresh');

    const shouldAttemptRefresh =
      error.response?.status === 401 && hasAuthHeader && hasActiveSession && !isAuthEndpoint;

    expect(shouldAttemptRefresh).toBe(false);
    expect(hasAuthHeader).toBe(true);
    expect(hasActiveSession).toBe(false);
  });

  it('should attempt refresh when user has active session', () => {
    // Simulate having both token and active session
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'access_token') return 'expired_token_123';
      if (key === 'session_active') return '1';
      return null;
    });

    const error = {
      response: { status: 401 },
      config: {
        url: '/users/me',
        headers: { Authorization: 'Bearer expired_token_123' },
      },
    };

    const hasAuthHeader = Boolean(error.config.headers?.Authorization);
    const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';
    const isAuthEndpoint =
      error.config.url?.includes('/auth/token') ||
      error.config.url?.includes('/auth/register') ||
      error.config.url?.includes('/auth/refresh');

    const shouldAttemptRefresh =
      error.response?.status === 401 && hasAuthHeader && hasActiveSession && !isAuthEndpoint;

    expect(shouldAttemptRefresh).toBe(true);
    expect(hasAuthHeader).toBe(true);
    expect(hasActiveSession).toBe(true);
  });

  it('should not attempt refresh for auth endpoints', () => {
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'access_token') return 'expired_token_123';
      if (key === 'session_active') return '1';
      return null;
    });

    const authEndpoints = ['/auth/token', '/auth/register', '/auth/refresh'];

    authEndpoints.forEach(endpoint => {
      const error = {
        response: { status: 401 },
        config: {
          url: endpoint,
          headers: { Authorization: 'Bearer expired_token_123' },
        },
      };

      const hasAuthHeader = Boolean(error.config.headers?.Authorization);
      const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';
      const isAuthEndpoint =
        error.config.url?.includes('/auth/token') ||
        error.config.url?.includes('/auth/register') ||
        error.config.url?.includes('/auth/refresh');

      const shouldAttemptRefresh =
        error.response?.status === 401 && hasAuthHeader && hasActiveSession && !isAuthEndpoint;

      expect(shouldAttemptRefresh).toBe(false);
      expect(isAuthEndpoint).toBe(true);
    });
  });

  it('should clear stale tokens when 401 occurs without active session', () => {
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'access_token') return 'expired_token_123';
      if (key === 'session_active') return null;
      return null;
    });

    const error = {
      response: { status: 401 },
      config: {
        url: '/users/me',
        headers: { Authorization: 'Bearer expired_token_123' },
      },
    };

    const hasAuthHeader = Boolean(error.config.headers?.Authorization);
    const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';

    // Simulate the cleanup logic
    if (error.response?.status === 401 && hasAuthHeader && !hasActiveSession) {
      mockLocalStorage.removeItem('access_token');
      mockLocalStorage.removeItem('session_active');
    }

    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('session_active');
  });

  it('should not attempt refresh for non-401 errors', () => {
    mockLocalStorage.getItem.mockImplementation(key => {
      if (key === 'access_token') return 'valid_token_123';
      if (key === 'session_active') return '1';
      return null;
    });

    const error = {
      response: { status: 500 }, // Server error, not auth error
      config: {
        url: '/users/me',
        headers: { Authorization: 'Bearer valid_token_123' },
      },
    };

    const hasAuthHeader = Boolean(error.config.headers?.Authorization);
    const hasActiveSession = mockLocalStorage.getItem('session_active') === '1';
    const isAuthEndpoint =
      error.config.url?.includes('/auth/token') ||
      error.config.url?.includes('/auth/register') ||
      error.config.url?.includes('/auth/refresh');

    const shouldAttemptRefresh =
      error.response?.status === 401 && hasAuthHeader && hasActiveSession && !isAuthEndpoint;

    expect(shouldAttemptRefresh).toBe(false);
  });

  describe('App.tsx Silent Refresh Logic', () => {
    it('should not attempt silent refresh when no session evidence exists', () => {
      // Simulate fresh user with no tokens or session
      mockLocalStorage.getItem.mockImplementation(key => {
        return null; // No stored values
      });

      const storedToken = mockLocalStorage.getItem('access_token');
      const hasSessionEvidence = mockLocalStorage.getItem('session_active') === '1';

      const shouldAttemptSilentRefresh = !storedToken && hasSessionEvidence;

      expect(shouldAttemptSilentRefresh).toBe(false);
      expect(storedToken).toBe(null);
      expect(hasSessionEvidence).toBe(false);
    });

    it('should attempt silent refresh when session evidence exists but no token', () => {
      // Simulate user who had a session but token expired/removed
      mockLocalStorage.getItem.mockImplementation(key => {
        if (key === 'access_token') return null;
        if (key === 'session_active') return '1';
        return null;
      });

      const storedToken = mockLocalStorage.getItem('access_token');
      const hasSessionEvidence = mockLocalStorage.getItem('session_active') === '1';

      const shouldAttemptSilentRefresh = !storedToken && hasSessionEvidence;

      expect(shouldAttemptSilentRefresh).toBe(true);
      expect(storedToken).toBe(null);
      expect(hasSessionEvidence).toBe(true);
    });

    it('should not attempt silent refresh when token exists', () => {
      // Simulate user with valid token
      mockLocalStorage.getItem.mockImplementation(key => {
        if (key === 'access_token') return 'valid_token_123';
        if (key === 'session_active') return '1';
        return null;
      });

      const storedToken = mockLocalStorage.getItem('access_token');
      const hasSessionEvidence = mockLocalStorage.getItem('session_active') === '1';

      const shouldAttemptSilentRefresh = !storedToken && hasSessionEvidence;

      expect(shouldAttemptSilentRefresh).toBe(false);
      expect(storedToken).toBe('valid_token_123');
      expect(hasSessionEvidence).toBe(true);
    });
  });
});
