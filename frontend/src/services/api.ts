import axios from 'axios';
import { validateApiResponse, ValidationError } from '../utils/validation';
import { TokenResponseSchema } from '../schemas/api';

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Flag to prevent refresh token loops
let isRefreshing = false;

apiClient.interceptors.response.use(
  response => response,
  async error => {
    // Only attempt refresh if:
    // 1. We got a 401 Unauthorized
    // 2. We're not already refreshing (avoid loops)
    // 3. We're not trying to login/register/refresh (these should fail normally)
    const originalRequest = error.config;
    const isAuthEndpoint =
      originalRequest?.url?.includes('/auth/token') ||
      originalRequest?.url?.includes('/auth/register') ||
      originalRequest?.url?.includes('/auth/refresh');

    // Check if there's evidence of an active session
    const hasActiveSession = localStorage.getItem('session_active') === '1';

    if (
      error.response?.status === 401 &&
      hasActiveSession &&
      !isRefreshing &&
      !isAuthEndpoint &&
      originalRequest
    ) {
      isRefreshing = true;

      try {
        // Attempt to refresh using httpOnly cookies
        await apiClient.post('/auth/refresh', {}, { withCredentials: true });

        isRefreshing = false;
        // Retry the original request - the new access token is now in the httpOnly cookie
        return apiClient(originalRequest);
      } catch (err) {
        isRefreshing = false;
        // Clear stale authentication state
        localStorage.removeItem('session_active');
        // Handle refresh failure (redirect to login, etc.)
        if (typeof window !== 'undefined') {
          // Always use test redirect in test environments (when available)
          const testRedirect = (window as any).__TEST_REDIRECT__;
          
          if (testRedirect && typeof testRedirect === 'function') {
            testRedirect('/login-register');
          } else {
            // Direct assignment to our mocked location object
            if (window.location && 'href' in window.location) {
              (window.location as any).href = '/login-register';
            }
          }
        }
        return Promise.reject(err);
      }
    }

    // If we get a 401 but no active session, clear any stale auth state
    if (error.response?.status === 401 && !hasActiveSession) {
      localStorage.removeItem('session_active');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
