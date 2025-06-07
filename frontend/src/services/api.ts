import axios from 'axios';
import { ApiResponse } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for consistent error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);

// Health check endpoint
export const checkHealth = async (): Promise<ApiResponse<{ status: string }>> => {
  const response = await api.get<ApiResponse<{ status: string }>>('/health');
  return response.data;
}; 