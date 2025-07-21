import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import { store } from '../../store';
import { login, registerUser, logoutUser, fetchCurrentUser } from '../../store/authSlice';
import { requestReset, resetPassword } from '../../store/passwordResetSlice';
import { verifyEmail, resendVerification } from '../../store/emailVerificationSlice';
import { UserProfile } from '../../schemas/api';

const API_URL = 'http://localhost:8000';

// Mock user data
const mockUser: UserProfile = {
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  email_verified: true,
  role: 'user',
};

const mockUnverifiedUser: UserProfile = {
  id: 'user-456',
  username: 'unverifieduser',
  email: 'unverified@example.com',
  email_verified: false,
  role: 'user',
};

describe('Authentication Flows Integration Tests (httpOnly Cookies)', () => {
  beforeEach(() => {
    // Clear localStorage and reset store
    localStorage.clear();
    server.resetHandlers();
    
    // Reset store to initial state
    store.dispatch({ type: 'auth/logout' });
  });

  describe('Complete Login Flow', () => {
    it('should complete login flow: credentials → httpOnly cookies → user profile → dashboard ready', async () => {
      server.use(
        // Login endpoint sets httpOnly cookies
        http.post(`${API_URL}/auth/token`, () => {
          return new HttpResponse(null, { 
            status: 200,
            headers: {
              'Set-Cookie': [
                'access_token=mock-access-token; Path=/; HttpOnly; SameSite=Lax; Secure',
                'refresh_token=mock-refresh-token; Path=/auth; HttpOnly; SameSite=Lax; Secure'
              ].join(', ')
            }
          });
        }),
        // User profile endpoint returns user data
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // Step 1: Dispatch login action
      const loginResult = await store.dispatch(login({
        email: 'test@example.com',
        password: 'securePassword123!'
      }));

      // Verify login was successful
      expect(loginResult.type).toBe('auth/login/fulfilled');
      expect(loginResult.payload).toEqual(mockUser);

      // Step 2: Check auth state
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user).toEqual(mockUser);
      expect(authState.status).toBe('succeeded');
      expect(authState.error).toBeNull();

      // Step 3: Verify session flag is set
      expect(localStorage.getItem('session_active')).toBe('1');
    });

    it('should handle login with invalid credentials', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.json({ detail: 'Invalid username or password' }, { status: 401 });
        })
      );

      const loginResult = await store.dispatch(login({
        email: 'test@example.com',
        password: 'wrongpassword'
      }));

      expect(loginResult.type).toBe('auth/login/rejected');
      
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.user).toBeNull();
      expect(authState.status).toBe('failed');
      expect(authState.error).toBeTruthy();
    });

    it('should handle login with unverified email', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.json({ detail: 'Email address not verified' }, { status: 403 });
        })
      );

      const loginResult = await store.dispatch(login({
        email: 'unverified@example.com',
        password: 'securePassword123!'
      }));

      expect(loginResult.type).toBe('auth/login/rejected');
      
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.error?.status).toBe(403);
    });
  });

  describe('Complete Registration Flow', () => {
    it('should complete registration flow: signup → success → email verification needed', async () => {
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return new HttpResponse(null, { status: 201 });
        })
      );

      // Step 1: Register user
      const registerResult = await store.dispatch(registerUser({
        email: 'newuser@example.com',
        password: 'securePassword123!'
      }));

      expect(registerResult.type).toBe('auth/register/fulfilled');
      
      const authState = store.getState().auth;
      expect(authState.status).toBe('succeeded');
      expect(authState.isAuthenticated).toBe(false); // User needs to verify email first
    });

    it('should handle registration with duplicate email', async () => {
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return HttpResponse.json({ detail: 'Email already exists' }, { status: 409 });
        })
      );

      const registerResult = await store.dispatch(registerUser({
        email: 'existing@example.com',
        password: 'securePassword123!'
      }));

      expect(registerResult.type).toBe('auth/register/rejected');
      
      const authState = store.getState().auth;
      expect(authState.status).toBe('failed');
      expect(authState.error?.status).toBe(409);
    });
  });

  describe('Complete Email Verification Flow', () => {
    it('should complete email verification flow: verify token → auto-login → dashboard ready', async () => {
      server.use(
        // Email verification endpoint
        http.post(`${API_URL}/auth/verify-email`, () => {
          return new HttpResponse(null, { 
            status: 200,
            headers: {
              'Set-Cookie': [
                'access_token=verified-access-token; Path=/; HttpOnly; SameSite=Lax; Secure',
                'refresh_token=verified-refresh-token; Path=/auth; HttpOnly; SameSite=Lax; Secure'
              ].join(', ')
            }
          });
        }),
        // User profile endpoint that gets called after verification
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // Step 1: Verify email with token
      const verifyResult = await store.dispatch(verifyEmail('valid-verification-token'));

      expect(verifyResult.type).toBe('emailVerification/verify/fulfilled');
      expect(verifyResult.payload).toEqual(mockUser);

      // Step 2: Check that auth state is updated (auto-login)
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user).toEqual(mockUser);
      expect(authState.status).toBe('succeeded');

      // Step 3: Verify session flag is set
      expect(localStorage.getItem('session_active')).toBe('1');
    });

    it('should handle invalid verification token', async () => {
      server.use(
        http.post(`${API_URL}/auth/verify-email`, () => {
          return HttpResponse.json({ detail: 'Invalid or expired token' }, { status: 400 });
        })
      );

      const verifyResult = await store.dispatch(verifyEmail('invalid-token'));

      expect(verifyResult.type).toBe('emailVerification/verify/rejected');
      
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
    });

    it('should resend verification email', async () => {
      server.use(
        http.post(`${API_URL}/auth/resend-verification`, () => {
          return new HttpResponse(null, { status: 200 });
        })
      );

      const resendResult = await store.dispatch(resendVerification('test@example.com'));

      expect(resendResult.type).toBe('emailVerification/resend/fulfilled');
    });
  });

  describe('Complete Password Reset Flow', () => {
    it('should complete password reset flow: request → email sent → reset with token → success', async () => {
      server.use(
        // Step 1: Request password reset
        http.post(`${API_URL}/auth/password-reset-request`, () => {
          return new HttpResponse(null, { status: 200 });
        }),
        // Step 2: Reset password with token
        http.post(`${API_URL}/auth/password-reset-complete`, () => {
          return new HttpResponse(null, { status: 200 });
        })
      );

      // Step 1: Request password reset
      const requestResult = await store.dispatch(requestReset('test@example.com'));
      expect(requestResult.type).toBe('passwordReset/request/fulfilled');

      // Step 2: Reset password with token
      const resetResult = await store.dispatch(resetPassword({
        token: 'valid-reset-token',
        password: 'newSecurePassword123!'
      }));
      expect(resetResult.type).toBe('passwordReset/reset/fulfilled');
    });

    it('should handle invalid reset token', async () => {
      server.use(
        http.post(`${API_URL}/auth/password-reset-complete`, () => {
          return HttpResponse.json({ detail: 'Invalid or expired token' }, { status: 400 });
        })
      );

      const resetResult = await store.dispatch(resetPassword({
        token: 'invalid-token',
        password: 'newPassword123!'
      }));

      expect(resetResult.type).toBe('passwordReset/reset/rejected');
    });
  });

  describe('Session Restoration Flow', () => {
    it('should restore session on app startup when session_active flag exists', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // Simulate existing session
      localStorage.setItem('session_active', '1');

      // Fetch current user (simulating app startup)
      const fetchResult = await store.dispatch(fetchCurrentUser());

      expect(fetchResult.type).toBe('auth/fetchCurrentUser/fulfilled');
      expect(fetchResult.payload).toEqual(mockUser);

      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user).toEqual(mockUser);
    });

    it('should handle expired session gracefully', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 });
        })
      );

      // Simulate existing session that's actually expired
      localStorage.setItem('session_active', '1');

      const fetchResult = await store.dispatch(fetchCurrentUser());

      expect(fetchResult.type).toBe('auth/fetchCurrentUser/rejected');
      
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.status).toBe('failed');
    });
  });

  describe('Logout Flow', () => {
    it('should complete logout flow: logout request → cookies cleared → state cleared → redirect ready', async () => {
      server.use(
        http.post(`${API_URL}/auth/logout`, () => {
          return new HttpResponse(null, { 
            status: 200,
            headers: {
              'Set-Cookie': [
                'access_token=; Path=/; HttpOnly; SameSite=Lax; Secure; Expires=Thu, 01 Jan 1970 00:00:00 GMT',
                'refresh_token=; Path=/auth; HttpOnly; SameSite=Lax; Secure; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
              ].join(', ')
            }
          });
        })
      );

      // Set up authenticated state first
      store.dispatch({ 
        type: 'auth/login/fulfilled', 
        payload: mockUser 
      });
      localStorage.setItem('session_active', '1');

      // Logout
      const logoutResult = await store.dispatch(logoutUser());

      expect(logoutResult.type).toBe('auth/logout/fulfilled');
      
      // Verify state is cleared
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.user).toBeNull();
      expect(authState.status).toBe('idle');

      // Verify session flag is cleared
      expect(localStorage.getItem('session_active')).toBeNull();
    });

    it('should handle logout even when backend call fails', async () => {
      server.use(
        http.post(`${API_URL}/auth/logout`, () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 });
        })
      );

      // Set up authenticated state first
      store.dispatch({ 
        type: 'auth/login/fulfilled', 
        payload: mockUser 
      });
      localStorage.setItem('session_active', '1');

      // Logout should still succeed on frontend even if backend fails
      const logoutResult = await store.dispatch(logoutUser());

      expect(logoutResult.type).toBe('auth/logout/fulfilled');
      
      // Frontend state should be cleared
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.user).toBeNull();
    });
  });

  describe('Token Refresh Flow', () => {
    it('should handle automatic token refresh with httpOnly cookies', async () => {
      let userMeCallCount = 0;
      
      server.use(
        // First call fails with 401
        http.get(`${API_URL}/users/me`, () => {
          userMeCallCount++;
          if (userMeCallCount === 1) {
            return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
          }
          // Second call succeeds after refresh
          return HttpResponse.json(mockUser);
        }),
        // Refresh token endpoint
        http.post(`${API_URL}/auth/refresh`, () => {
          return new HttpResponse(null, { 
            status: 200,
            headers: {
              'Set-Cookie': [
                'access_token=refreshed-access-token; Path=/; HttpOnly; SameSite=Lax; Secure',
                'refresh_token=refreshed-refresh-token; Path=/auth; HttpOnly; SameSite=Lax; Secure'
              ].join(', ')
            }
          });
        })
      );

      // Set up session active flag
      localStorage.setItem('session_active', '1');

      // This should trigger auto-refresh
      const fetchResult = await store.dispatch(fetchCurrentUser());

      expect(fetchResult.type).toBe('auth/fetchCurrentUser/fulfilled');
      expect(fetchResult.payload).toEqual(mockUser);
      expect(userMeCallCount).toBe(2); // Called twice due to retry after refresh
    });
  });

  describe('Error Scenarios', () => {
    it('should handle network errors gracefully', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.error();
        })
      );

      const loginResult = await store.dispatch(login({
        email: 'test@example.com',
        password: 'password'
      }));

      expect(loginResult.type).toBe('auth/login/rejected');
      
      const authState = store.getState().auth;
      expect(authState.status).toBe('failed');
      expect(authState.error).toBeTruthy();
    });

    it('should handle validation errors', async () => {
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return HttpResponse.json({ 
            detail: 'Validation error',
            errors: ['Password too weak', 'Email invalid']
          }, { status: 422 });
        })
      );

      const registerResult = await store.dispatch(registerUser({
        email: 'invalid-email',
        password: '123'
      }));

      expect(registerResult.type).toBe('auth/register/rejected');
      
      const authState = store.getState().auth;
      expect(authState.error?.status).toBe(422);
    });
  });

  describe('Concurrent Request Handling', () => {
    it('should handle multiple concurrent requests during authentication', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, async () => {
          // Simulate some delay
          await new Promise(resolve => setTimeout(resolve, 100));
          return new HttpResponse(null, { 
            status: 200,
            headers: {
              'Set-Cookie': [
                'access_token=concurrent-access-token; Path=/; HttpOnly; SameSite=Lax; Secure',
                'refresh_token=concurrent-refresh-token; Path=/auth; HttpOnly; SameSite=Lax; Secure'
              ].join(', ')
            }
          });
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // Make multiple concurrent login requests
      const loginPromises = Array(3).fill(0).map(() => 
        store.dispatch(login({
          email: 'test@example.com',
          password: 'password'
        }))
      );

      const results = await Promise.all(loginPromises);

      // All should succeed (though some might be redundant)
      results.forEach(result => {
        expect(['auth/login/fulfilled', 'auth/login/pending'].includes(result.type)).toBe(true);
      });

      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
    });
  });
});