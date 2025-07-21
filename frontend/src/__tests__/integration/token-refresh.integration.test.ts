import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import { store } from '../../store';
import { fetchCurrentUser } from '../../store/authSlice';
import apiClient from '../../services/api';

const API_URL = 'http://localhost:8000';

// Mock data
const mockUser = {
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  email_verified: true,
  role: 'user',
};

// Note: With httpOnly cookies, tokens are managed automatically by the browser
// No need for mockTokenResponse

describe('Token Refresh Mechanism Integration Tests (httpOnly Cookies)', () => {
  beforeEach(() => {
    // Clear localStorage (no auth headers to clear with httpOnly cookies)
    localStorage.clear();

    // Reset MSW handlers
    server.resetHandlers();

    // Clear Redux store state
    store.dispatch({ type: 'auth/logout' });
  });

  describe('Automatic Token Refresh on Expired Tokens', () => {
    it('should automatically refresh token when receiving 401 and retry original request', async () => {
      let callCount = 0;

      server.use(
        // First call to protected endpoint fails with 401
        http.get(`${API_URL}/users/me`, () => {
          callCount++;
          if (callCount === 1) {
            return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
          }
          // Second call after refresh succeeds
          return HttpResponse.json(mockUser);
        }),
        // Refresh token call succeeds
        http.post(`${API_URL}/auth/refresh`, () => {
          return new HttpResponse(null, { 
            status: 200,
            headers: {
              'Set-Cookie': [
                'access_token=new-access-token; Path=/; HttpOnly; SameSite=Lax; Secure',
                'refresh_token=new-refresh-token; Path=/auth; HttpOnly; SameSite=Lax; Secure'
              ].join(', ')
            }
          });
        })
      );

      // Set up initial state with session active (no token storage with httpOnly cookies)
      localStorage.setItem('session_active', '1');

      const response = await apiClient.get('/users/me');

      expect(response.status).toBe(200);
      expect(response.data).toEqual(mockUser);
      expect(callCount).toBe(2); // Initial failed call + retry after refresh
    });

    it('should not attempt refresh for auth endpoints', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
        }),
        http.post(`${API_URL}/auth/refresh`, () => {
          // This should not be called
          return new HttpResponse(null, { status: 200 });
        })
      );

      // Set up state with session active
      localStorage.setItem('session_active', '1');

      try {
        const form = new URLSearchParams();
        form.append('username', 'test@example.com');
        form.append('password', 'wrongpassword');

        await apiClient.post('/auth/token', form);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        // Refresh should not have been attempted
      }
    });

    it('should not attempt refresh when no active session', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 });
        }),
        http.post(`${API_URL}/auth/refresh`, () => {
          // This should not be called
          return new HttpResponse(null, { status: 200 });
        })
      );

      // Set up state with no active session (no session_active flag set)
      // No token storage needed with httpOnly cookies

      try {
        await apiClient.get('/users/me');
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);

        // Verify session flag remains cleared
        expect(localStorage.getItem('session_active')).toBeNull();
      }
    });

    it('should redirect to login when refresh fails', async () => {
      const originalLocation = window.location.href;

      // Mock window.location.href setter
      delete (window as any).location;
      (window as any).location = { href: '' };

      server.use(
        // Protected endpoint fails
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
        }),
        // Refresh fails
        http.post(`${API_URL}/auth/refresh`, () => {
          return HttpResponse.json({ detail: 'Invalid refresh token' }, { status: 401 });
        })
      );

      // Set up initial state with session active
      localStorage.setItem('session_active', '1');

      try {
        await apiClient.get('/users/me');
        fail('Should have thrown an error');
      } catch (error) {
        // Verify auth state is cleared
        expect(localStorage.getItem('session_active')).toBeNull();
        expect(window.location.href).toBe('/login-register');
      }

      // Restore original location
      (window as any).location = { href: originalLocation };
    });

    it('should prevent refresh token loops', async () => {
      let refreshCallCount = 0;

      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
        }),
        http.post(`${API_URL}/auth/refresh`, () => {
          refreshCallCount++;
          return HttpResponse.json({ detail: 'Invalid refresh token' }, { status: 401 });
        })
      );

      // Set up initial state with session active
      localStorage.setItem('session_active', '1');

      // Make multiple concurrent requests
      const requests = Array(3)
        .fill(0)
        .map(() => apiClient.get('/users/me').catch(() => {}));

      await Promise.all(requests);

      // Refresh should only be attempted once to prevent loops
      expect(refreshCallCount).toBe(1);
    });

    it('should handle concurrent requests during refresh', async () => {
      let usersMeCallCount = 0;
      let refreshCallCount = 0;

      server.use(
        http.get(`${API_URL}/users/me`, () => {
          usersMeCallCount++;
          if (usersMeCallCount <= 3) {
            // First 3 calls fail
            return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
          }
          // Subsequent calls succeed
          return HttpResponse.json(mockUser);
        }),
        http.post(`${API_URL}/auth/refresh`, async () => {
          refreshCallCount++;
          // Simulate some delay in refresh
          await new Promise(resolve => setTimeout(resolve, 100));
          return new HttpResponse(null, { 
            status: 200,
            headers: {
              'Set-Cookie': [
                'access_token=new-access-token; Path=/; HttpOnly; SameSite=Lax; Secure',
                'refresh_token=new-refresh-token; Path=/auth; HttpOnly; SameSite=Lax; Secure'
              ].join(', ')
            }
          });
        })
      );

      // Set up initial state with session active
      localStorage.setItem('session_active', '1');

      // Make multiple concurrent requests
      const requests = Array(3)
        .fill(0)
        .map(() => apiClient.get('/users/me'));
      const responses = await Promise.all(requests);

      // All requests should succeed
      responses.forEach(response => {
        expect(response.status).toBe(200);
        expect(response.data).toEqual(mockUser);
      });

      // Only one refresh should have been attempted
      expect(refreshCallCount).toBe(1);
    });
  });

  describe('Silent Refresh on App Startup', () => {
    it('should attempt to restore session on app startup', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // Simulate session evidence from previous session
      localStorage.setItem('session_active', '1');

      // With httpOnly cookies, no manual token setup needed
      await store.dispatch(fetchCurrentUser());

      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user).toEqual(mockUser);
      expect(localStorage.getItem('session_active')).toBe('1');
    });

    it('should handle invalid stored token on app startup', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Invalid token' }, { status: 401 });
        })
      );

      // Simulate invalid stored token
      localStorage.setItem('access_token', 'invalid-token');
      apiClient.defaults.headers.common['Authorization'] = 'Bearer invalid-token';

      await store.dispatch(fetchCurrentUser());

      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.status).toBe('failed');
    });

    it('should handle no stored token on app startup', async () => {
      // No token stored
      await store.dispatch(fetchCurrentUser());

      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.status).toBe('failed');
    });

    it('should attempt refresh if stored token is expired on startup', async () => {
      let callCount = 0;

      server.use(
        http.get(`${API_URL}/users/me`, () => {
          callCount++;
          if (callCount === 1) {
            return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
          }
          return HttpResponse.json(mockUser);
        }),
        http.post(`${API_URL}/auth/refresh`, () => {
          return HttpResponse.json(mockTokenResponse);
        })
      );

      // Simulate expired stored token
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('session_active', '1');
      apiClient.defaults.headers.common['Authorization'] = 'Bearer expired-token';

      await store.dispatch(fetchCurrentUser());

      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user).toEqual(mockUser);
      expect(localStorage.getItem('access_token')).toBe('new-access-token');
    });
  });

  describe('Token Lifecycle Management', () => {
    it('should handle token rotation properly', async () => {
      // Initial tokens
      const initialAccessToken = 'initial-access-token';
      const refreshedAccessToken = 'refreshed-access-token';

      // Set up initial state
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${initialAccessToken}`;
      localStorage.setItem('access_token', initialAccessToken);
      localStorage.setItem('session_active', '1');

      server.use(
        // First request fails with expired token
        http.get(`${API_URL}/users/me`, () => {
          const authHeader = apiClient.defaults.headers.common['Authorization'];
          if (authHeader === `Bearer ${initialAccessToken}`) {
            return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
          }
          return HttpResponse.json(mockUser);
        }),
        // Refresh provides new tokens
        http.post(`${API_URL}/auth/refresh`, () => {
          return HttpResponse.json({
            access_token: refreshedAccessToken,
            refresh_token: 'new-refresh-token',
          });
        })
      );

      const response = await apiClient.get('/users/me');

      expect(response.status).toBe(200);
      expect(localStorage.getItem('access_token')).toBe(refreshedAccessToken);
      expect(apiClient.defaults.headers.common['Authorization']).toBe(
        `Bearer ${refreshedAccessToken}`
      );
    });

    it('should handle refresh token being sent via different methods', async () => {
      const refreshToken = 'test-refresh-token';

      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
        }),
        http.post(`${API_URL}/auth/refresh`, ({ request }) => {
          // Check that refresh token is sent in cookie
          const cookies = request.headers.get('cookie') || '';
          if (cookies.includes(`refresh_token=${refreshToken}`)) {
            return HttpResponse.json(mockTokenResponse);
          }
          return HttpResponse.json({ detail: 'No refresh token' }, { status: 401 });
        })
      );

      // Set up initial state with expired access token and valid refresh token in cookie
      apiClient.defaults.headers.common['Authorization'] = 'Bearer expired-token';
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('session_active', '1');

      // Mock document.cookie for refresh token
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: `refresh_token=${refreshToken}; Path=/auth; HttpOnly; SameSite=Lax`,
      });

      const response = await apiClient.get('/users/me');
      expect(response.status).toBe(200);
    });
  });

  describe('Error Scenarios', () => {
    it('should handle network errors during token refresh', async () => {
      const originalLocation = window.location.href;
      delete (window as any).location;
      (window as any).location = { href: '' };

      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
        }),
        http.post(`${API_URL}/auth/refresh`, () => {
          return HttpResponse.error();
        })
      );

      // Set up initial state
      apiClient.defaults.headers.common['Authorization'] = 'Bearer expired-token';
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('session_active', '1');

      try {
        await apiClient.get('/users/me');
        fail('Should have thrown an error');
      } catch (error) {
        // Should redirect to login on network error during refresh
        expect(window.location.href).toBe('/login-register');
      }

      (window as any).location = { href: originalLocation };
    });

    it('should handle server errors during token refresh', async () => {
      const originalLocation = window.location.href;
      delete (window as any).location;
      (window as any).location = { href: '' };

      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
        }),
        http.post(`${API_URL}/auth/refresh`, () => {
          return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
        })
      );

      // Set up initial state
      apiClient.defaults.headers.common['Authorization'] = 'Bearer expired-token';
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('session_active', '1');

      try {
        await apiClient.get('/users/me');
        fail('Should have thrown an error');
      } catch (error) {
        expect(window.location.href).toBe('/login-register');
      }

      (window as any).location = { href: originalLocation };
    });

    it('should handle malformed refresh response', async () => {
      const originalLocation = window.location.href;
      delete (window as any).location;
      (window as any).location = { href: '' };

      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
        }),
        http.post(`${API_URL}/auth/refresh`, () => {
          // Return malformed response without access_token
          return HttpResponse.json({
            token_type: 'bearer',
            // missing access_token
          });
        })
      );

      // Set up initial state
      apiClient.defaults.headers.common['Authorization'] = 'Bearer expired-token';
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('session_active', '1');

      try {
        await apiClient.get('/users/me');
        fail('Should have thrown an error');
      } catch (error) {
        // Should handle gracefully and redirect to login
        expect(window.location.href).toBe('/login-register');
      }

      (window as any).location = { href: originalLocation };
    });
  });
});
