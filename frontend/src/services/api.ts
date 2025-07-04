import axios from 'axios';

const API_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      try {
        await apiClient.post('/auth/refresh', {
          refresh_token: '',
        });
      } catch (err) {
        return Promise.reject(err);
      }
      return apiClient(error.config);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
