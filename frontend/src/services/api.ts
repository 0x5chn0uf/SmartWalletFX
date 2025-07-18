import axios from 'axios';

const API_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Rehydrate access token from storage on page load
const storedToken = localStorage.getItem('access_token');
if (storedToken) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
}

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
      originalRequest.url?.includes('/auth/token') ||
      originalRequest.url?.includes('/auth/register') ||
      originalRequest.url?.includes('/auth/refresh');

    const hasAuthHeader = Boolean(
      originalRequest.headers?.Authorization || apiClient.defaults.headers.common['Authorization']
    );

    if (
      error.response?.status === 401 &&
      hasAuthHeader &&
      !isRefreshing &&
      !isAuthEndpoint &&
      originalRequest
    ) {
      isRefreshing = true;

      try {
        const refreshResp = await apiClient.post('/auth/refresh', {}, { withCredentials: true });

        const newToken = refreshResp.data?.access_token as string | undefined;
        if (newToken) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
          localStorage.setItem('access_token', newToken);
        }
        isRefreshing = false;
        return apiClient(originalRequest);
      } catch (err) {
        isRefreshing = false;
        // Handle refresh failure (redirect to login, etc.)
        window.location.href = '/login-register';
        return Promise.reject(err);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
