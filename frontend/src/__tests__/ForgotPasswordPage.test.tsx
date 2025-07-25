import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { vi } from 'vitest';
import ForgotPasswordPage from '../pages/ForgotPasswordPage';

// Mock the API client
vi.mock('../services/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

// Mock the useAuth hook
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: false,
    status: 'idle',
  }),
}));

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

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the form correctly', () => {
    const store = createMockStore({
      status: 'idle',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('SmartWalletFX')).toBeInTheDocument();
    expect(
      screen.getByText('Enter your email to receive a password reset link.')
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send Reset Link' })).toBeInTheDocument();
  });

  it('should disable submit button when email is empty', () => {
    const store = createMockStore({
      status: 'idle',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    expect(submitButton).toBeDisabled();
  });

  it('should enable submit button when email is entered', () => {
    const store = createMockStore({
      status: 'idle',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    const emailInput = screen.getByLabelText('Email');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

    expect(submitButton).toBeEnabled();
  });

  it('should show loading state during request', () => {
    const store = createMockStore({
      status: 'loading',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByRole('button', { name: 'Sending...' })).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeDisabled();
  });

  it('should show success message when request succeeds', () => {
    const store = createMockStore({
      status: 'succeeded',
      error: null,
    });

    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(
      screen.getByText(
        'If an account with this email exists, you will receive a password reset link shortly.'
      )
    ).toBeInTheDocument();
  });

  it('should show error message when request fails', () => {
    const store = createMockStore({
      status: 'failed',
      error: 'Too many password reset requests. Please try again later.',
    });

    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(
      screen.getByText('Too many password reset requests. Please try again later.')
    ).toBeInTheDocument();
  });

  it('should show network error message', () => {
    const store = createMockStore({
      status: 'failed',
      error: 'Network error. Please check your connection and try again.',
    });

    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    expect(
      screen.getByText('Network error. Please check your connection and try again.')
    ).toBeInTheDocument();
  });
});
