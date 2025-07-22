import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import { store } from '../../store';
import { requestReset, verifyResetToken, resetPassword } from '../../store/passwordResetSlice';
import { login } from '../../store/authSlice';
import apiClient from '../../services/api';

const API_URL = 'http://localhost:8000';

// Mock data
const mockEmail = 'test@example.com';
const mockToken = 'reset-token-123';
const mockNewPassword = 'newSecurePassword123!';

const mockTokenResponse = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
};

const mockUser = {
  id: 'user-123',
  username: 'testuser',
  email: mockEmail,
  email_verified: true,
  role: 'user',
};

describe('Password Reset Flow Integration Tests', () => {
  beforeEach(() => {
    // Clear localStorage and auth headers
    localStorage.clear();
    delete apiClient.defaults.headers.common['Authorization'];

    // Reset MSW handlers
    server.resetHandlers();

    // Clear Redux store state
    store.dispatch({ type: 'passwordReset/resetState' });
    store.dispatch({ type: 'auth/logout' });
  });

  describe('Complete Password Reset Flow', () => {
    it('should complete the full password reset flow: request → verify → reset → login', async () => {
      // Step 1: Request password reset
      server.use(
        http.post(`${API_URL}/auth/password-reset-request`, () => {
          return new HttpResponse(null, { status: 204 });
        })
      );

      await store.dispatch(requestReset(mockEmail));
      let state = store.getState().passwordReset;
      expect(state.status).toBe('succeeded');
      expect(state.error).toBeNull();

      // Step 2: Verify reset token
      server.use(
        http.post(`${API_URL}/auth/password-reset-verify`, () => {
          return HttpResponse.json({
            valid: true,
            message: 'Token verified',
          });
        })
      );

      await store.dispatch(verifyResetToken(mockToken));
      state = store.getState().passwordReset;
      expect(state.tokenValidationStatus).toBe('succeeded');
      expect(state.error).toBeNull();

      // Step 3: Complete password reset
      server.use(
        http.post(`${API_URL}/auth/password-reset-complete`, () => {
          return HttpResponse.json({
            message: 'Password reset completed successfully',
          });
        })
      );

      await store.dispatch(
        resetPassword({
          token: mockToken,
          password: mockNewPassword,
        })
      );
      state = store.getState().passwordReset;
      expect(state.status).toBe('succeeded');
      expect(state.error).toBeNull();

      // Step 4: Login with new password
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.json(mockTokenResponse);
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      await store.dispatch(
        login({
          email: mockEmail,
          password: mockNewPassword,
        })
      );

      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user).toEqual(mockUser);
      expect(authState.status).toBe('succeeded');
    });

    it('should handle rate limiting during password reset request', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-request`, () => {
          return HttpResponse.json(
            { detail: 'Too many password reset requests. Please try again later.' },
            { status: 429 }
          );
        })
      );

      await store.dispatch(requestReset(mockEmail));
      const state = store.getState().passwordReset;
      expect(state.status).toBe('failed');
      expect(state.error).toBe('Too many password reset requests. Please try again later.');
    });

    it('should handle network errors during password reset request', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-request`, () => {
          return HttpResponse.error();
        })
      );

      await store.dispatch(requestReset(mockEmail));
      const state = store.getState().passwordReset;
      expect(state.status).toBe('failed');
      expect(state.error).toBe('Network error. Please check your connection and try again.');
    });

    it('should not reveal if email exists during password reset request', async () => {
      // Even for non-existent emails, the endpoint should return 204
      server.use(
        http.post(`${API_URL}/auth/password-reset-request`, () => {
          return new HttpResponse(null, { status: 204 });
        })
      );

      await store.dispatch(requestReset('nonexistent@example.com'));
      const state = store.getState().passwordReset;
      expect(state.status).toBe('succeeded');
      expect(state.error).toBeNull();
    });
  });

  describe('Token Verification Edge Cases', () => {
    it('should handle invalid reset token', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-verify`, () => {
          return HttpResponse.json({ detail: 'Invalid or expired token' }, { status: 400 });
        })
      );

      await store.dispatch(verifyResetToken('invalid-token'));
      const state = store.getState().passwordReset;
      expect(state.tokenValidationStatus).toBe('failed');
      expect(state.error).toBe('Invalid or expired token');
    });

    it('should handle expired reset token', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-verify`, () => {
          return HttpResponse.json({ detail: 'Token has expired' }, { status: 400 });
        })
      );

      await store.dispatch(verifyResetToken('expired-token'));
      const state = store.getState().passwordReset;
      expect(state.tokenValidationStatus).toBe('failed');
      expect(state.error).toBe('Token has expired');
    });

    it('should handle malformed reset token', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-verify`, () => {
          return HttpResponse.json({ detail: 'Malformed token' }, { status: 400 });
        })
      );

      await store.dispatch(verifyResetToken('malformed-token'));
      const state = store.getState().passwordReset;
      expect(state.tokenValidationStatus).toBe('failed');
      expect(state.error).toBe('Malformed token');
    });
  });

  describe('Password Reset Completion Edge Cases', () => {
    it('should handle password reset with invalid token during completion', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-complete`, () => {
          return HttpResponse.json({ detail: 'Invalid or expired token' }, { status: 400 });
        })
      );

      await store.dispatch(
        resetPassword({
          token: 'invalid-token',
          password: mockNewPassword,
        })
      );

      const state = store.getState().passwordReset;
      expect(state.status).toBe('failed');
      expect(state.error).toBe('Invalid or expired token');
    });

    it('should handle user not found during password reset completion', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-complete`, () => {
          return HttpResponse.json({ detail: 'User not found' }, { status: 400 });
        })
      );

      await store.dispatch(
        resetPassword({
          token: mockToken,
          password: mockNewPassword,
        })
      );

      const state = store.getState().passwordReset;
      expect(state.status).toBe('failed');
      expect(state.error).toBe('User not found');
    });

    it('should handle weak password during reset completion', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-complete`, () => {
          return HttpResponse.json(
            { detail: 'Password does not meet strength requirements' },
            { status: 400 }
          );
        })
      );

      await store.dispatch(
        resetPassword({
          token: mockToken,
          password: 'weak',
        })
      );

      const state = store.getState().passwordReset;
      expect(state.status).toBe('failed');
      expect(state.error).toBe('Password does not meet strength requirements');
    });

    it('should handle server errors during password reset completion', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-complete`, () => {
          return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
        })
      );

      await store.dispatch(
        resetPassword({
          token: mockToken,
          password: mockNewPassword,
        })
      );

      const state = store.getState().passwordReset;
      expect(state.status).toBe('failed');
      expect(state.error).toBe('Internal server error');
    });
  });

  describe('State Management During Flow', () => {
    it('should maintain proper loading states throughout the flow', async () => {
      let requestPromiseResolver: (value: any) => void;
      const requestPromise = new Promise(resolve => {
        requestPromiseResolver = resolve;
      });

      server.use(
        http.post(`${API_URL}/auth/password-reset-request`, async () => {
          await requestPromise;
          return new HttpResponse(null, { status: 204 });
        })
      );

      // Start request
      const requestAction = store.dispatch(requestReset(mockEmail));

      // Check loading state
      let state = store.getState().passwordReset;
      expect(state.status).toBe('loading');

      // Complete request
      requestPromiseResolver!(null);
      await requestAction;

      // Check completed state
      state = store.getState().passwordReset;
      expect(state.status).toBe('succeeded');
    });

    it('should reset state correctly between operations', async () => {
      // First operation - request reset
      server.use(
        http.post(`${API_URL}/auth/password-reset-request`, () => {
          return new HttpResponse(null, { status: 204 });
        })
      );

      await store.dispatch(requestReset(mockEmail));
      let state = store.getState().passwordReset;
      expect(state.status).toBe('succeeded');

      // Reset state
      store.dispatch({ type: 'passwordReset/resetState' });
      state = store.getState().passwordReset;
      expect(state.status).toBe('idle');
      expect(state.tokenValidationStatus).toBe('idle');
      expect(state.error).toBeNull();

      // Second operation - verify token
      server.use(
        http.post(`${API_URL}/auth/password-reset-verify`, () => {
          return HttpResponse.json({
            valid: true,
            message: 'Token verified',
          });
        })
      );

      await store.dispatch(verifyResetToken(mockToken));
      state = store.getState().passwordReset;
      expect(state.tokenValidationStatus).toBe('succeeded');
    });
  });

  describe('User Experience Flow', () => {
    it('should simulate realistic user interaction timing', async () => {
      // Step 1: User requests password reset
      server.use(
        http.post(`${API_URL}/auth/password-reset-request`, async () => {
          // Simulate email service delay
          await new Promise(resolve => setTimeout(resolve, 100));
          return new HttpResponse(null, { status: 204 });
        })
      );

      const startTime = Date.now();
      await store.dispatch(requestReset(mockEmail));
      const requestTime = Date.now() - startTime;

      expect(requestTime).toBeGreaterThan(90); // Should take some time
      expect(store.getState().passwordReset.status).toBe('succeeded');

      // Step 2: User clicks email link and verifies token
      server.use(
        http.post(`${API_URL}/auth/password-reset-verify`, () => {
          return HttpResponse.json({
            valid: true,
            message: 'Token verified',
          });
        })
      );

      await store.dispatch(verifyResetToken(mockToken));
      expect(store.getState().passwordReset.tokenValidationStatus).toBe('succeeded');

      // Step 3: User enters new password
      server.use(
        http.post(`${API_URL}/auth/password-reset-complete`, () => {
          return HttpResponse.json({
            message: 'Password reset completed successfully',
          });
        })
      );

      await store.dispatch(
        resetPassword({
          token: mockToken,
          password: mockNewPassword,
        })
      );
      expect(store.getState().passwordReset.status).toBe('succeeded');
    });

    it('should handle user abandoning flow and restarting', async () => {
      // Start flow
      server.use(
        http.post(`${API_URL}/auth/password-reset-request`, () => {
          return new HttpResponse(null, { status: 204 });
        })
      );

      await store.dispatch(requestReset(mockEmail));
      expect(store.getState().passwordReset.status).toBe('succeeded');

      // User abandons and starts over (simulate page refresh by resetting state)
      store.dispatch({ type: 'passwordReset/resetState' });

      // New request
      await store.dispatch(requestReset(mockEmail));
      expect(store.getState().passwordReset.status).toBe('succeeded');
      expect(store.getState().passwordReset.tokenValidationStatus).toBe('idle');
    });
  });
});
