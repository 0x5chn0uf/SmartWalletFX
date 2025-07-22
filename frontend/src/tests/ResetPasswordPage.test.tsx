import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { vi } from 'vitest';
import ResetPasswordPage from '../pages/ResetPasswordPage';
import passwordResetReducer from '../store/passwordResetSlice';
import authReducer from '../store/authSlice';

// Mock the API client
vi.mock('../services/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

// Mock the useAuth hook
const mockUseAuth = vi.fn();
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const createMockStore = (passwordResetState: any, authState: any = {}) => {
  return configureStore({
    reducer: {
      passwordReset: () => passwordResetState,
      auth: () => ({
        isAuthenticated: false,
        status: 'idle',
        user: null,
        error: null,
        ...authState,
      }),
    },
  });
};

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      status: 'idle',
    });
  });

  it('should redirect authenticated users to dashboard', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      status: 'succeeded',
    });

    const store = createMockStore({
      status: 'idle',
      tokenValidationStatus: 'idle',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('should redirect to forgot-password if no token provided', () => {
    const store = createMockStore({
      status: 'idle',
      tokenValidationStatus: 'idle',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(mockNavigate).toHaveBeenCalledWith('/forgot-password');
  });

  it('should show loading state while validating token', () => {
    const store = createMockStore({
      status: 'idle',
      tokenValidationStatus: 'loading',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('SmartWalletFX')).toBeInTheDocument();
    expect(screen.getByText('Validating reset token...')).toBeInTheDocument();
  });

  it('should show error when token validation fails', () => {
    const store = createMockStore({
      status: 'idle',
      tokenValidationStatus: 'failed',
      error: 'Invalid or expired token',
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=invalid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('Reset token is invalid or expired.')).toBeInTheDocument();
    expect(screen.getByText('Invalid or expired token')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '← Request New Reset' })).toBeInTheDocument();
  });

  it('should render the form when token is valid', () => {
    const store = createMockStore({
      status: 'idle',
      tokenValidationStatus: 'succeeded',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('SmartWalletFX')).toBeInTheDocument();
    expect(screen.getByText('Enter a new password to complete the reset.')).toBeInTheDocument();
    expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reset Password' })).toBeInTheDocument();
  });

  it('should disable submit button when password is too short', () => {
    const store = createMockStore({
      status: 'idle',
      tokenValidationStatus: 'succeeded',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    const passwordInput = screen.getByLabelText('New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    fireEvent.change(passwordInput, { target: { value: 'short' } });

    expect(submitButton).toBeDisabled();
  });

  it('should enable submit button when password is valid', () => {
    const store = createMockStore({
      status: 'idle',
      tokenValidationStatus: 'succeeded',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    const passwordInput = screen.getByLabelText('New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    fireEvent.change(passwordInput, { target: { value: 'validpassword123' } });

    expect(submitButton).toBeEnabled();
  });

  it('should show loading state during password reset', () => {
    const store = createMockStore({
      status: 'loading',
      tokenValidationStatus: 'succeeded',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByRole('button', { name: 'Resetting...' })).toBeInTheDocument();
    expect(screen.getByLabelText('New Password')).toBeDisabled();
  });

  it('should show success message when password reset succeeds', () => {
    const store = createMockStore({
      status: 'succeeded',
      tokenValidationStatus: 'succeeded',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('Password reset complete!')).toBeInTheDocument();
    expect(
      screen.getByText('Your password has been reset successfully! Redirecting to login...')
    ).toBeInTheDocument();
    expect(screen.queryByRole('form')).not.toBeInTheDocument();
  });

  it('should show error message when password reset fails', () => {
    const store = createMockStore({
      status: 'failed',
      tokenValidationStatus: 'succeeded',
      error: 'Failed to reset password. Please try again.',
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('Failed to reset password. Please try again.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reset Password' })).toBeInTheDocument();
  });

  it('should redirect to login after successful password reset', async () => {
    vi.useFakeTimers();

    const store = createMockStore({
      status: 'succeeded',
      tokenValidationStatus: 'succeeded',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=valid-token']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    // Fast-forward time by 3 seconds
    vi.advanceTimersByTime(3000);

    // Use runOnlyPendingTimers to flush the timer
    await vi.runOnlyPendingTimersAsync();

    expect(mockNavigate).toHaveBeenCalledWith('/login-register');

    vi.useRealTimers();
  });
});
