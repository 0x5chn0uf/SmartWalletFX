import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import apiClient from '../../services/api';
import { UserProfile } from '../../store/authSlice';

const API_URL = 'http://localhost:8000';

// Mock user data
const mockUser: UserProfile = {
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  email_verified: true,
  role: 'user',
};

const mockTokenResponse = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
};

describe('Auth API Integration Tests', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Clear authorization header
    delete apiClient.defaults.headers.common['Authorization'];

    // Reset MSW handlers to default state
    server.resetHandlers();
  });

  describe('Registration Flow', () => {
    it('should successfully register a new user', async () => {
      server.use(
        http.post(`${API_URL}/auth/register`, () => {
          return HttpResponse.json(mockUser, { status: 201 });
        })
      );

      const response = await apiClient.post('/auth/register', {
        username: 'testuser',
        email: 'test@example.com',
        password: 'securePassword123!',
      });

      expect(response.status).toBe(201);
      expect(response.data).toEqual(mockUser);
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
    it('should successfully login with valid credentials', async () => {
      server.use(
        http.post(`${API_URL}/auth/token`, () => {
          return HttpResponse.json(mockTokenResponse);
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
      expect(tokenResponse.data).toEqual(mockTokenResponse);

      // Verify token is set in headers
      apiClient.defaults.headers.common['Authorization'] =
        `Bearer ${mockTokenResponse.access_token}`;

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
    it('should successfully refresh access token', async () => {
      const newTokenResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      };

      server.use(
        http.post(`${API_URL}/auth/refresh`, () => {
          return HttpResponse.json(newTokenResponse);
        })
      );

      const response = await apiClient.post('/auth/refresh', {});
      expect(response.status).toBe(200);
      expect(response.data).toEqual(newTokenResponse);
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

    it('should auto-refresh token on 401 and retry original request', async () => {
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
          return HttpResponse.json({
            access_token: 'new-access-token',
            refresh_token: 'new-refresh-token',
          });
        })
      );

      // Set up initial state with expired token
      apiClient.defaults.headers.common['Authorization'] = 'Bearer expired-token';
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('session_active', '1');

      const response = await apiClient.get('/users/me');
      expect(response.status).toBe(200);
      expect(response.data).toEqual(mockUser);
      expect(callCount).toBe(2); // Initial failed call + retry after refresh

      // Verify new token is stored
      expect(localStorage.getItem('access_token')).toBe('new-access-token');
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

      // Set up initial state
      apiClient.defaults.headers.common['Authorization'] = 'Bearer expired-token';
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('session_active', '1');

      try {
        await apiClient.get('/users/me');
        fail('Should have thrown an error');
      } catch (error) {
        // Verify auth state is cleared
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(localStorage.getItem('session_active')).toBeNull();
        expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
        expect(window.location.href).toBe('/login-register');
      }

      // Restore original location
      (window as any).location = { href: originalLocation };
    });
  });

  describe('Logout Flow', () => {
    it('should successfully logout user', async () => {
      server.use(
        http.post(`${API_URL}/auth/logout`, () => {
          return new HttpResponse(null, { status: 200 });
        })
      );

      const response = await apiClient.post('/auth/logout', {});
      expect(response.status).toBe(200);
    });

    it('should handle logout when no refresh token provided', async () => {
      server.use(
        http.post(`${API_URL}/auth/logout`, () => {
          return HttpResponse.json({ detail: 'Refresh token not provided' }, { status: 401 });
        })
      );

      try {
        await apiClient.post('/auth/logout', {});
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toBe('Refresh token not provided');
      }
    });
  });

  describe('Session Management', () => {
    it('should handle session check for authenticated user', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // Set up authenticated state
      apiClient.defaults.headers.common['Authorization'] = 'Bearer valid-token';
      localStorage.setItem('access_token', 'valid-token');

      const response = await apiClient.get('/users/me');
      expect(response.status).toBe(200);
      expect(response.data).toEqual(mockUser);
      expect(localStorage.getItem('session_active')).toBe('1');
    });

    it('should clear stale auth state on 401 without active session', async () => {
      server.use(
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 });
        })
      );

      // Set up stale auth state without active session
      apiClient.defaults.headers.common['Authorization'] = 'Bearer stale-token';
      localStorage.setItem('access_token', 'stale-token');
      // No session_active flag set

      try {
        await apiClient.get('/users/me');
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);

        // Verify stale auth state is cleared
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
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

        await apiClient.post('/auth/token', form);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.code).toBe('ERR_NETWORK');
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

        await apiClient.post('/auth/token', form);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.code).toBe('ECONNABORTED');
      } finally {
        // Restore original timeout
        apiClient.defaults.timeout = originalTimeout;
      }
    });
  });
});
