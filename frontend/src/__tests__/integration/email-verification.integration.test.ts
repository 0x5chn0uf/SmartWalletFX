import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import { store } from '../../store';
import { verifyEmail, resendVerification } from '../../store/emailVerificationSlice';
import { registerUser } from '../../store/authSlice';
import apiClient from '../../services/api';

const API_URL = 'http://localhost:8000';

// Mock data
const mockEmail = 'test@example.com';
const mockUsername = 'testuser';
const mockPassword = 'securePassword123!';
const mockVerificationToken = 'verification-token-123';

const mockUser = {
  id: 'user-123',
  username: mockUsername,
  email: mockEmail,
  email_verified: true,
  role: 'user',
};

const mockUnverifiedUser = {
  ...mockUser,
  email_verified: false,
};

const mockTokenResponse = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
};

describe('Email Verification Flow Integration Tests', () => {
  beforeEach(() => {
    // Clear localStorage and auth headers
    localStorage.clear();
    delete apiClient.defaults.headers.common['Authorization'];

    // Reset MSW handlers
    server.resetHandlers();

    // Clear Redux store state
    store.dispatch({ type: 'emailVerification/resetState' });
    store.dispatch({ type: 'auth/logout' });
  });

  describe('Complete Email Verification Flow', () => {
    it('should complete the full verification flow: registration → verification email → verify → auto-login', async () => {
      // Step 1: User registration
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return HttpResponse.json(mockUnverifiedUser, { status: 201 });
        })
      );

      await store.dispatch(
        registerUser({
          email: mockEmail,
          password: mockPassword,
        })
      );

      let authState = store.getState().auth;
      expect(authState.status).toBe('succeeded');
      expect(authState.isAuthenticated).toBe(false); // Not authenticated until email verified

      // Step 2: Email verification (simulating user clicking email link)
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json(mockTokenResponse);
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      await store.dispatch(verifyEmail(mockVerificationToken));

      // Check email verification state
      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('succeeded');
      expect(verificationState.error).toBeNull();

      // Check that user is auto-logged in after verification
      authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user).toEqual(mockUser);
      expect(authState.user?.email_verified).toBe(true);

      // Verify session is marked as active (tokens are in httpOnly cookies)
      expect(localStorage.getItem('session_active')).toBe('1');
    });

    it('should handle verification with invalid token', async () => {
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json({ detail: 'Invalid verification token' }, { status: 400 });
        })
      );

      await store.dispatch(verifyEmail('invalid-token'));

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('failed');
      expect(verificationState.error).toBe('Verification failed');

      // Ensure user is not authenticated
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
    });

    it('should handle verification with expired token', async () => {
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json({ detail: 'Verification token has expired' }, { status: 400 });
        })
      );

      await store.dispatch(verifyEmail('expired-token'));

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('failed');
      expect(verificationState.error).toBe('Verification failed');
    });

    it('should handle already verified email', async () => {
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json({ detail: 'Email already verified' }, { status: 400 });
        })
      );

      await store.dispatch(verifyEmail(mockVerificationToken));

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('failed');
      expect(verificationState.error).toBe('Verification failed');
    });
  });

  describe('Resend Verification Email Flow', () => {
    it('should successfully resend verification email', async () => {
      server.use(
        http.post(`${API_URL}/auth/resend-verification`, () => {
          return new HttpResponse(null, { status: 204 });
        })
      );

      await store.dispatch(resendVerification(mockEmail));

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('succeeded');
      expect(verificationState.error).toBeNull();
    });

    it('should handle rate limiting when resending verification email', async () => {
      server.use(
        http.post(`${API_URL}/auth/resend-verification`, () => {
          return HttpResponse.json(
            { detail: 'Too many verification requests. Please try again later.' },
            { status: 429 }
          );
        })
      );

      await store.dispatch(resendVerification(mockEmail));

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('failed');
      expect(verificationState.error).toBe('Resend failed');
    });

    it('should handle resend for non-existent email', async () => {
      server.use(
        http.post(`${API_URL}/auth/resend-verification`, () => {
          return HttpResponse.json({ detail: 'Email not found' }, { status: 404 });
        })
      );

      await store.dispatch(resendVerification('nonexistent@example.com'));

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('failed');
      expect(verificationState.error).toBe('Resend failed');
    });

    it('should handle resend for already verified email', async () => {
      server.use(
        http.post(`${API_URL}/auth/resend-verification`, () => {
          return HttpResponse.json({ detail: 'Email already verified' }, { status: 400 });
        })
      );

      await store.dispatch(resendVerification(mockEmail));

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('failed');
      expect(verificationState.error).toBe('Resend failed');
    });
  });

  describe('Registration to Verification Integration', () => {
    it('should maintain state between registration and verification', async () => {
      // Step 1: Registration
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return HttpResponse.json(mockUnverifiedUser, { status: 201 });
        })
      );

      await store.dispatch(
        registerUser({
          email: mockEmail,
          password: mockPassword,
        })
      );

      const authState = store.getState().auth;
      expect(authState.status).toBe('succeeded');

      // Step 2: Simulate user going to email verification page
      // (In real app, user would be redirected to verification notice page)

      // Step 3: User clicks verification link
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json(mockTokenResponse);
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      await store.dispatch(verifyEmail(mockVerificationToken));

      const finalAuthState = store.getState().auth;
      expect(finalAuthState.isAuthenticated).toBe(true);
      expect(finalAuthState.user?.email_verified).toBe(true);
    });

    it('should handle verification failure after successful registration', async () => {
      // Successful registration
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return HttpResponse.json(mockUnverifiedUser, { status: 201 });
        })
      );

      await store.dispatch(
        registerUser({
          email: mockEmail,
          password: mockPassword,
        })
      );

      expect(store.getState().auth.status).toBe('succeeded');

      // Failed verification
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json({ detail: 'Invalid token' }, { status: 400 });
        })
      );

      await store.dispatch(verifyEmail('invalid-token'));

      // User should not be authenticated after failed verification
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('failed');
    });
  });

  describe('Token Management During Verification', () => {
    it('should properly set auth tokens after successful verification', async () => {
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json({
            access_token: 'new-access-token',
            refresh_token: 'new-refresh-token',
          });
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      await store.dispatch(verifyEmail(mockVerificationToken));

      // Check that session is marked as active (tokens are in httpOnly cookies)
      expect(localStorage.getItem('session_active')).toBe('1');
    });

    it('should not set tokens if verification fails', async () => {
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json({ detail: 'Invalid token' }, { status: 400 });
        })
      );

      await store.dispatch(verifyEmail('invalid-token'));

      // Ensure no session is stored
      expect(localStorage.getItem('session_active')).toBeNull();
    });
  });

  describe('State Management During Verification Flow', () => {
    it('should maintain proper loading states during verification', async () => {
      let verificationResolver: (value: any) => void;
      const verificationPromise = new Promise(resolve => {
        verificationResolver = resolve;
      });

      server.use(
        http.post(`${API_URL}/auth/verify-email`, async () => {
          await verificationPromise;
          return HttpResponse.json(mockTokenResponse);
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // Start verification
      const verificationAction = store.dispatch(verifyEmail(mockVerificationToken));

      // Check loading state
      let state = store.getState().emailVerification;
      expect(state.status).toBe('loading');

      // Complete verification
      verificationResolver!(null);
      await verificationAction;

      // Check completed state
      state = store.getState().emailVerification;
      expect(state.status).toBe('succeeded');
    });

    it('should maintain proper loading states during resend operation', async () => {
      let resendResolver: (value: any) => void;
      const resendPromise = new Promise(resolve => {
        resendResolver = resolve;
      });

      server.use(
        http.post(`${API_URL}/auth/resend-verification`, async () => {
          await resendPromise;
          return new HttpResponse(null, { status: 204 });
        })
      );

      // Start resend
      const resendAction = store.dispatch(resendVerification(mockEmail));

      // Check loading state
      let state = store.getState().emailVerification;
      expect(state.status).toBe('loading');

      // Complete resend
      resendResolver!(null);
      await resendAction;

      // Check completed state
      state = store.getState().emailVerification;
      expect(state.status).toBe('succeeded');
    });
  });

  describe('Network Error Handling', () => {
    it('should handle network errors during verification', async () => {
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.error();
        })
      );

      await store.dispatch(verifyEmail(mockVerificationToken));

      const state = store.getState().emailVerification;
      expect(state.status).toBe('failed');
      expect(state.error).toBe('Verification failed');
    });

    it('should handle network errors during resend', async () => {
      server.use(
        http.post(`${API_URL}/auth/resend-verification`, () => {
          return HttpResponse.error();
        })
      );

      await store.dispatch(resendVerification(mockEmail));

      const state = store.getState().emailVerification;
      expect(state.status).toBe('failed');
      expect(state.error).toBe('Resend failed');
    });

    it('should handle timeout errors during verification', async () => {
      server.use(
        http.post(`${API_URL}/auth/verify-email`, async () => {
          await new Promise(resolve => setTimeout(resolve, 1000));
          return HttpResponse.json(mockTokenResponse);
        })
      );

      // Set a very short timeout for this test
      const originalTimeout = apiClient.defaults.timeout;
      apiClient.defaults.timeout = 100;

      try {
        await store.dispatch(verifyEmail(mockVerificationToken));

        const state = store.getState().emailVerification;
        expect(state.status).toBe('failed');
      } finally {
        // Restore original timeout
        apiClient.defaults.timeout = originalTimeout;
      }
    });
  });

  describe('User Experience Scenarios', () => {
    it('should handle user verifying email from different browser/device', async () => {
      // Clear any existing session to simulate different device
      localStorage.clear();
      delete apiClient.defaults.headers.common['Authorization'];

      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json(mockTokenResponse);
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      await store.dispatch(verifyEmail(mockVerificationToken));

      // Should still work and establish new session
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(localStorage.getItem('session_active')).toBe('1');
    });

    it('should handle user trying to verify multiple times', async () => {
      // First verification attempt (successful)
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json(mockTokenResponse);
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      await store.dispatch(verifyEmail(mockVerificationToken));
      expect(store.getState().auth.isAuthenticated).toBe(true);

      // Second verification attempt (already verified)
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json({ detail: 'Email already verified' }, { status: 400 });
        })
      );

      await store.dispatch(verifyEmail(mockVerificationToken));

      // Should still remain authenticated from first verification
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);

      const verificationState = store.getState().emailVerification;
      expect(verificationState.status).toBe('failed');
    });
  });
});
