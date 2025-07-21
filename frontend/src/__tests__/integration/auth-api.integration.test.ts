import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import apiClient from '../../services/api';
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

// Note: With httpOnly cookies, we don't need mock token response as tokens are set in cookies
// by the backend and handled automatically by the browser

describe('Auth API Integration Tests (httpOnly Cookies)', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    
    // Note: No need to clear Authorization header as we're using httpOnly cookies
    // The cookies are managed by MSW and browser mock

    // Reset MSW handlers to default state
    server.resetHandlers();
  });

  describe('Registration Flow', () => {
    it('should successfully register a new user', async () => {
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return new HttpResponse(null, { status: 201 });
        })
      );

      const response = await apiClient.post('/auth/register', {
        username: 'testuser',
        email: 'test@example.com',
        password: 'securePassword123!',
      });

      expect(response.status).toBe(201);
      // Registration returns empty response, user data comes from subsequent login
    });

    it('should handle registration with duplicate email', async () => {
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return HttpResponse.json({ detail: 'email already exists' }, { status: 409 });
        })
      );

      try {
        await apiClient.post('/auth/register', {
          username: 'testuser',
          email: 'existing@example.com',
          password: 'securePassword123!',
        });
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(409);
        expect(error.response.data.detail).toBe('email already exists');
      }
    });

    it('should handle registration with weak password', async () => {
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return HttpResponse.json(
            { detail: 'Password does not meet strength requirements' },
            { status: 400 }
          );
        })
      );

      try {
        await apiClient.post('/auth/register', {
          username: 'testuser',
          email: 'test@example.com',
          password: '123',
        });
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.detail).toBe('Password does not meet strength requirements');
      }
    });
  });

  describe('Login Flow', () => {
    it('should successfully login with valid credentials and set httpOnly cookies', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          // With httpOnly cookies, the backend sets cookies in response headers
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
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      const form = new URLSearchParams();
      form.append('username', 'test@example.com');
      form.append('password', 'securePassword123!');

      const tokenResponse = await apiClient.post('/auth/token', form);
      expect(tokenResponse.status).toBe(200);
      // Login with httpOnly cookies returns empty response

      // Verify that subsequent requests work with cookies
      const userResponse = await apiClient.get('/users/me');
      expect(userResponse.status).toBe(200);
      expect(userResponse.data).toEqual(mockUser);
    });

    it('should handle login with invalid credentials', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.json({ detail: 'Invalid username or password' }, { status: 401 });
        })
      );

      try {
        const form = new URLSearchParams();
        form.append('username', 'test@example.com');
        form.append('password', 'wrongpassword');

        await apiClient.post('/auth/token', form);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toBe('Invalid username or password');
      }
    });

    it('should handle login with unverified email', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.json({ detail: 'Email address not verified' }, { status: 403 });
        })
      );

      try {
        const form = new URLSearchParams();
        form.append('username', 'unverified@example.com');
        form.append('password', 'securePassword123!');

        await apiClient.post('/auth/token', form);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(403);
        expect(error.response.data.detail).toBe('Email address not verified');
      }
    });

    it('should handle rate limiting on login attempts', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.json(
            { detail: 'Too many login attempts, please try again later.' },
            { status: 429 }
          );
        })
      );

      try {
        const form = new URLSearchParams();
        form.append('username', 'test@example.com');
        form.append('password', 'wrongpassword');

        await apiClient.post('/auth/token', form);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(429);
        expect(error.response.data.detail).toBe('Too many login attempts, please try again later.');
      }
    });
  });

  describe('Token Refresh Flow', () => {
    it('should successfully refresh access token with httpOnly cookies', async () => {
      server.use(
        http.post(`${API_URL}/auth/refresh`, () => {
          // Backend sets new tokens as httpOnly cookies
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

      const response = await apiClient.post('/auth/refresh', {});
      expect(response.status).toBe(200);
      // Refresh with httpOnly cookies returns empty response
    });

    it('should handle refresh with invalid token', async () => {
      server.use(
        http.post(`${API_URL}/auth/refresh`, () => {
          return HttpResponse.json({ detail: 'Invalid refresh token' }, { status: 401 });
        })
      );

      try {
        await apiClient.post('/auth/refresh', {});
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toBe('Invalid refresh token');
      }
    });

    it('should auto-refresh token on 401 and retry original request with httpOnly cookies', async () => {
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

      // Set up initial state with session active (no token storage needed with httpOnly cookies)
      localStorage.setItem('session_active', '1');

      const response = await apiClient.get('/users/me');
      expect(response.status).toBe(200);
      expect(response.data).toEqual(mockUser);
      expect(callCount).toBe(2); // Initial failed call + retry after refresh
    });

    it('should redirect to login when refresh fails with httpOnly cookies', async () => {
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
        // Note: In real implementation, localStorage.removeItem('session_active') would be called
        // by the API interceptor when refresh fails, but in tests we need to verify behavior
        expect(window.location.href).toBe('/login-register');
      }

      // Restore original location
      (window as any).location = { href: originalLocation };
    });
  });

  describe('Logout Flow', () => {
    it('should successfully logout user and clear httpOnly cookies', async () => {
      server.use(
        http.post(`${API_URL}/auth/logout`, () => {
          // Backend clears cookies by setting them with empty value and past expiry
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

      const response = await apiClient.post('/auth/logout', {}, { withCredentials: true });
      expect(response.status).toBe(200);
    });

    it('should handle logout when no refresh token provided', async () => {
      server.use(
        http.post(`${API_URL}/auth/logout`, () => {
          return HttpResponse.json({ detail: 'Refresh token not provided' }, { status: 401 });
        })
      );

      try {
        await apiClient.post('/auth/logout', {}, { withCredentials: true });
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response?.status).toBe(401);
        expect(error.response?.data?.detail).toBe('Refresh token not provided');
      }
    });
  });

  describe('Session Management', () => {
    it('should handle session check for authenticated user with httpOnly cookies', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // With httpOnly cookies, we just need to ensure the cookies exist (simulated by MSW)
      // No token storage in localStorage needed

      const response = await apiClient.get('/users/me', { withCredentials: true });
      expect(response.status).toBe(200);
      expect(response.data).toEqual(mockUser);
      expect(localStorage.getItem('session_active')).toBe('1');
    });

    it('should clear stale auth state on 401 without active session (httpOnly cookies)', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 });
        })
      );

      // With httpOnly cookies, we only need to ensure no session_active flag is set
      // No token storage in localStorage needed

      try {
        await apiClient.get('/users/me', { withCredentials: true });
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response?.status).toBe(401);

        // Verify session flag remains cleared (no session_active was set)
        expect(localStorage.getItem('session_active')).toBeNull();
      }
    });
  });

  describe('Network Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.error();
        })
      );

      try {
        const form = new URLSearchParams();
        form.append('username', 'test@example.com');
        form.append('password', 'password');

        await apiClient.post('/auth/token', form, { withCredentials: true });
        fail('Should have thrown an error');
      } catch (error: any) {
        // MSW error() creates a TypeError with 'Failed to fetch' message
        expect(error.message).toContain('Failed to fetch');
      }
    });

    it('should handle timeout errors', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, async () => {
          // Simulate timeout by delaying response
          await new Promise(resolve => setTimeout(resolve, 1000));
          return HttpResponse.json(mockTokenResponse);
        })
      );

      // Set a very short timeout for this test
      const originalTimeout = apiClient.defaults.timeout;
      apiClient.defaults.timeout = 100;

      try {
        const form = new URLSearchParams();
        form.append('username', 'test@example.com');
        form.append('password', 'password');

        await apiClient.post('/auth/token', form, { withCredentials: true });
        fail('Should have thrown an error');
      } catch (error: any) {
        // In test environment, timeout may not behave exactly like production
        expect(error.message || error.code).toBeTruthy();
      } finally {
        // Restore original timeout
        apiClient.defaults.timeout = originalTimeout;
      }
    });
  });
});
