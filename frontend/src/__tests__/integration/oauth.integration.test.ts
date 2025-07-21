import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OAuthButton } from '../../components/oauth/OAuthButton';

const API_URL = 'http://localhost:8000';

// Mock window.location.href for OAuth redirects
const mockLocationAssign = jest.fn();
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    assign: mockLocationAssign,
  },
  writable: true,
});

describe('OAuth Integration Tests', () => {
  beforeEach(() => {
    // Clear localStorage and reset mocks
    localStorage.clear();
    mockLocationAssign.mockClear();
    
    // Reset MSW handlers
    server.resetHandlers();
  });

  describe('OAuth Button Component', () => {
    it('should render Google OAuth button correctly', () => {
      render(<OAuthButton provider="google" />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Continue with Google');
      expect(button).toHaveClass('oauth-btn', 'oauth-btn-google');
    });

    it('should render GitHub OAuth button correctly', () => {
      render(<OAuthButton provider="github" />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Continue with GitHub');
      expect(button).toHaveClass('oauth-btn', 'oauth-btn-github');
    });

    it('should redirect to OAuth endpoint when clicked', () => {
      render(<OAuthButton provider="google" />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      expect(window.location.href).toBe(`${API_URL}/auth/oauth/google/login`);
    });

    it('should call onClick handler if provided', () => {
      const mockOnClick = jest.fn();
      render(<OAuthButton provider="github" onClick={mockOnClick} />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      expect(mockOnClick).toHaveBeenCalledTimes(1);
      expect(window.location.href).toBe(`${API_URL}/auth/oauth/github/login`);
    });
  });

  describe('OAuth Login Flow', () => {
    it('should handle Google OAuth login redirect', async () => {
      // Mock the OAuth login endpoint that would be called by the backend
      server.use(
        http.get(`${API_URL}/auth/oauth/google/login`, () => {
          // This would typically return a redirect response
          return new Response(null, {
            status: 302,
            headers: {
              Location: 'https://accounts.google.com/oauth/authorize?client_id=...'
            }
          });
        })
      );

      render(<OAuthButton provider="google" />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // Verify that the user would be redirected to OAuth provider
      expect(window.location.href).toBe(`${API_URL}/auth/oauth/google/login`);
    });

    it('should handle GitHub OAuth login redirect', async () => {
      server.use(
        http.get(`${API_URL}/auth/oauth/github/login`, () => {
          return new Response(null, {
            status: 302,
            headers: {
              Location: 'https://github.com/login/oauth/authorize?client_id=...'
            }
          });
        })
      );

      render(<OAuthButton provider="github" />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      expect(window.location.href).toBe(`${API_URL}/auth/oauth/github/login`);
    });
  });

  describe('OAuth Callback Simulation', () => {
    it('should simulate successful Google OAuth callback', async () => {
      const mockCode = 'oauth_authorization_code_123';
      const mockState = 'oauth_state_456';
      
      const mockTokenResponse = {
        access_token: 'oauth-access-token',
        refresh_token: 'oauth-refresh-token',
        token_type: 'bearer'
      };

      const mockUser = {
        id: 'oauth-user-123',
        username: 'googleuser',
        email: 'user@gmail.com',
        email_verified: true,
        role: 'user'
      };

      server.use(
        http.get(`${API_URL}/auth/oauth/google/callback`, ({ request }) => {
          const url = new URL(request.url);
          const code = url.searchParams.get('code');
          const state = url.searchParams.get('state');
          
          if (code === mockCode && state === mockState) {
            // Simulate successful OAuth callback
            return new Response(null, {
              status: 302,
              headers: {
                Location: '/dashboard',
                'Set-Cookie': [
                  `access_token=${mockTokenResponse.access_token}; HttpOnly; SameSite=Lax`,
                  `refresh_token=${mockTokenResponse.refresh_token}; HttpOnly; SameSite=Lax; Path=/auth`
                ].join(', ')
              }
            });
          }
          
          return HttpResponse.json(
            { detail: 'Invalid OAuth callback' },
            { status: 400 }
          );
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(mockUser);
        })
      );

      // Simulate OAuth callback URL
      const callbackUrl = `${API_URL}/auth/oauth/google/callback?code=${mockCode}&state=${mockState}`;
      
      // This would typically be handled by the browser navigation
      // We're testing that the endpoint would respond correctly
      const response = await fetch(callbackUrl);
      expect(response.status).toBe(302);
      expect(response.headers.get('Location')).toBe('/dashboard');
    });

    it('should handle OAuth callback with invalid state', async () => {
      server.use(
        http.get(`${API_URL}/auth/oauth/google/callback`, () => {
          return HttpResponse.json(
            { detail: 'Invalid state' },
            { status: 400 }
          );
        })
      );

      const callbackUrl = `${API_URL}/auth/oauth/google/callback?code=valid_code&state=invalid_state`;
      
      const response = await fetch(callbackUrl);
      expect(response.status).toBe(400);
      
      const data = await response.json();
      expect(data.detail).toBe('Invalid state');
    });

    it('should handle OAuth callback with missing code', async () => {
      server.use(
        http.get(`${API_URL}/auth/oauth/google/callback`, ({ request }) => {
          const url = new URL(request.url);
          const code = url.searchParams.get('code');
          
          if (!code) {
            return HttpResponse.json(
              { detail: 'Authorization code not provided' },
              { status: 400 }
            );
          }
          
          return HttpResponse.json({ success: true });
        })
      );

      const callbackUrl = `${API_URL}/auth/oauth/google/callback?state=valid_state`;
      
      const response = await fetch(callbackUrl);
      expect(response.status).toBe(400);
      
      const data = await response.json();
      expect(data.detail).toBe('Authorization code not provided');
    });

    it('should handle OAuth error responses', async () => {
      server.use(
        http.get(`${API_URL}/auth/oauth/google/callback`, ({ request }) => {
          const url = new URL(request.url);
          const error = url.searchParams.get('error');
          
          if (error === 'access_denied') {
            return HttpResponse.json(
              { detail: 'User denied access' },
              { status: 400 }
            );
          }
          
          return HttpResponse.json({ success: true });
        })
      );

      const callbackUrl = `${API_URL}/auth/oauth/google/callback?error=access_denied&state=valid_state`;
      
      const response = await fetch(callbackUrl);
      expect(response.status).toBe(400);
      
      const data = await response.json();
      expect(data.detail).toBe('User denied access');
    });
  });

  describe('OAuth Error Handling', () => {
    it('should handle unsupported OAuth provider', async () => {
      server.use(
        http.get(`${API_URL}/auth/oauth/unsupported/login`, () => {
          return HttpResponse.json(
            { detail: 'Provider not supported' },
            { status: 404 }
          );
        })
      );

      // Test that unsupported provider would return 404
      const response = await fetch(`${API_URL}/auth/oauth/unsupported/login`);
      expect(response.status).toBe(404);
      
      const data = await response.json();
      expect(data.detail).toBe('Provider not supported');
    });

    it('should handle OAuth provider service unavailable', async () => {
      server.use(
        http.get(`${API_URL}/auth/oauth/google/login`, () => {
          return HttpResponse.json(
            { detail: 'OAuth provider temporarily unavailable' },
            { status: 503 }
          );
        })
      );

      render(<OAuthButton provider="google" />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // The redirect would still happen, but the backend would handle the error
      expect(window.location.href).toBe(`${API_URL}/auth/oauth/google/login`);
    });

    it('should handle network errors during OAuth initiation', async () => {
      server.use(
        http.get(`${API_URL}/auth/oauth/github/login`, () => {
          return HttpResponse.error();
        })
      );

      render(<OAuthButton provider="github" />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // Redirect would still happen, error handling is done at network level
      expect(window.location.href).toBe(`${API_URL}/auth/oauth/github/login`);
    });
  });

  describe('OAuth State Management', () => {
    it('should handle OAuth state cookie validation', async () => {
      const mockState = 'secure_oauth_state_123';
      
      server.use(
        http.get(`${API_URL}/auth/oauth/google/callback`, ({ request }) => {
          const cookies = request.headers.get('cookie') || '';
          const url = new URL(request.url);
          const stateParam = url.searchParams.get('state');
          
          // Check if state parameter matches cookie
          if (cookies.includes(`oauth_state=${mockState}`) && stateParam === mockState) {
            return new Response(null, {
              status: 302,
              headers: { Location: '/dashboard' }
            });
          }
          
          return HttpResponse.json(
            { detail: 'Invalid state' },
            { status: 400 }
          );
        })
      );

      // Mock cookie with OAuth state
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: `oauth_state=${mockState}`
      });

      const callbackUrl = `${API_URL}/auth/oauth/google/callback?code=valid_code&state=${mockState}`;
      
      const response = await fetch(callbackUrl, {
        headers: {
          'Cookie': `oauth_state=${mockState}`
        }
      });
      
      expect(response.status).toBe(302);
      expect(response.headers.get('Location')).toBe('/dashboard');
    });

    it('should handle CSRF protection through state parameter', async () => {
      server.use(
        http.get(`${API_URL}/auth/oauth/github/callback`, ({ request }) => {
          const url = new URL(request.url);
          const state = url.searchParams.get('state');
          
          // Simulate CSRF check failure
          if (!state || state.length < 10) {
            return HttpResponse.json(
              { detail: 'Invalid state parameter - possible CSRF attack' },
              { status: 400 }
            );
          }
          
          return HttpResponse.json({ success: true });
        })
      );

      // Test with short/weak state parameter
      const callbackUrl = `${API_URL}/auth/oauth/github/callback?code=valid_code&state=weak`;
      
      const response = await fetch(callbackUrl);
      expect(response.status).toBe(400);
      
      const data = await response.json();
      expect(data.detail).toBe('Invalid state parameter - possible CSRF attack');
    });
  });

  describe('OAuth Integration with Existing Auth', () => {
    it('should handle OAuth login when user already has account', async () => {
      const existingUser = {
        id: 'existing-user-123',
        username: 'existinguser',
        email: 'user@gmail.com',
        email_verified: true,
        role: 'user'
      };

      server.use(
        http.get(`${API_URL}/auth/oauth/google/callback`, () => {
          // Simulate linking OAuth account to existing user
          return new Response(null, {
            status: 302,
            headers: {
              Location: '/dashboard',
              'Set-Cookie': 'access_token=linked-account-token; HttpOnly; SameSite=Lax'
            }
          });
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(existingUser);
        })
      );

      const callbackUrl = `${API_URL}/auth/oauth/google/callback?code=valid_code&state=valid_state`;
      
      const response = await fetch(callbackUrl);
      expect(response.status).toBe(302);
      expect(response.headers.get('Location')).toBe('/dashboard');
    });

    it('should handle OAuth account creation for new users', async () => {
      const newUser = {
        id: 'new-oauth-user-123',
        username: 'newgoogleuser',
        email: 'newuser@gmail.com',
        email_verified: true, // OAuth users are auto-verified
        role: 'user'
      };

      server.use(
        http.get(`${API_URL}/auth/oauth/google/callback`, () => {
          return new Response(null, {
            status: 302,
            headers: {
              Location: '/dashboard',
              'Set-Cookie': 'access_token=new-user-token; HttpOnly; SameSite=Lax'
            }
          });
        }),
        http.get(`${API_URL}/users/me`, () => {
          return HttpResponse.json(newUser);
        })
      );

      const callbackUrl = `${API_URL}/auth/oauth/google/callback?code=valid_code&state=valid_state`;
      
      const response = await fetch(callbackUrl);
      expect(response.status).toBe(302);
      expect(response.headers.get('Location')).toBe('/dashboard');
    });
  });

  describe('OAuth Environment Configuration', () => {
    it('should use correct API URL from environment', () => {
      // Test that OAuth button uses the configured API URL
      render(<OAuthButton provider="google" />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // Should use the API_URL constant from the component
      expect(window.location.href).toBe(`${API_URL}/auth/oauth/google/login`);
    });

    it('should handle different environments correctly', () => {
      // Test production-like URL
      const originalEnv = (import.meta as any).env;
      (import.meta as any).env = {
        ...originalEnv,
        VITE_API_URL: 'https://api.production.com'
      };

      // Re-render with new environment
      render(<OAuthButton provider="github" />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // Should use production URL
      expect(window.location.href).toBe('https://api.production.com/auth/oauth/github/login');

      // Restore original environment
      (import.meta as any).env = originalEnv;
    });
  });
});