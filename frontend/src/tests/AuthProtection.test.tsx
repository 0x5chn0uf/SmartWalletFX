import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import LoginRegisterPage from '../pages/LoginRegisterPage';
import ForgotPasswordPage from '../pages/ForgotPasswordPage';
import authReducer from '../store/authSlice';

import { vi } from 'vitest';

// Mock the store with different auth states
const createMockStore = (authState: any) => {
  return configureStore({
    reducer: {
      auth: () => authState,
      passwordReset: () => ({ status: 'idle', error: null }),
    },
  });
};

// Mock navigate function
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Authentication Protection', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  describe('LoginRegisterPage', () => {
    it('should redirect authenticated users to /defi', () => {
      const authenticatedStore = createMockStore({
        isAuthenticated: true,
        status: 'succeeded',
        user: { id: 1, email: 'test@example.com' },
        token: 'test-token',
      });

      render(
        <Provider store={authenticatedStore}>
          <MemoryRouter>
            <LoginRegisterPage />
          </MemoryRouter>
        </Provider>
      );

      expect(mockNavigate).toHaveBeenCalledWith('/defi', { replace: true });
    });

    it('should render login form for unauthenticated users', () => {
      const unauthenticatedStore = createMockStore({
        isAuthenticated: false,
        status: 'idle',
        user: null,
        token: null,
      });

      render(
        <Provider store={unauthenticatedStore}>
          <MemoryRouter>
            <LoginRegisterPage />
          </MemoryRouter>
        </Provider>
      );

      expect(screen.getByText('SmartWalletFX')).toBeInTheDocument();
      expect(screen.getByText('Register')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    });

    it('should not redirect when authentication is still loading', () => {
      const loadingStore = createMockStore({
        isAuthenticated: false,
        status: 'loading',
        user: null,
        token: null,
      });

      render(
        <Provider store={loadingStore}>
          <MemoryRouter>
            <LoginRegisterPage />
          </MemoryRouter>
        </Provider>
      );

      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('ForgotPasswordPage', () => {
    it('should redirect authenticated users to /defi', () => {
      const authenticatedStore = createMockStore({
        isAuthenticated: true,
        status: 'succeeded',
        user: { id: 1, email: 'test@example.com' },
        token: 'test-token',
      });

      render(
        <Provider store={authenticatedStore}>
          <MemoryRouter>
            <ForgotPasswordPage />
          </MemoryRouter>
        </Provider>
      );

      expect(mockNavigate).toHaveBeenCalledWith('/defi', { replace: true });
    });

    it('should render forgot password form for unauthenticated users', () => {
      const unauthenticatedStore = createMockStore({
        isAuthenticated: false,
        status: 'idle',
        user: null,
        token: null,
      });

      render(
        <Provider store={unauthenticatedStore}>
          <MemoryRouter>
            <ForgotPasswordPage />
          </MemoryRouter>
        </Provider>
      );

      expect(screen.getByText('SmartWalletFX')).toBeInTheDocument();
      expect(screen.getByText('Send Reset Link')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
    });

    it('should not redirect when authentication is still loading', () => {
      const loadingStore = createMockStore({
        isAuthenticated: false,
        status: 'loading',
        user: null,
        token: null,
      });

      render(
        <Provider store={loadingStore}>
          <MemoryRouter>
            <ForgotPasswordPage />
          </MemoryRouter>
        </Provider>
      );

      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });
});
