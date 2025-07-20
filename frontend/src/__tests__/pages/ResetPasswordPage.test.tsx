import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import ResetPasswordPage from '../../pages/ResetPasswordPage';
import passwordResetReducer, {
  resetPassword,
  verifyResetToken,
} from '../../store/passwordResetSlice';
import authReducer from '../../store/authSlice';
import { vi } from 'vitest';

// Mock the API client
vi.mock('../../services/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

// Mock the useAuth hook
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: false,
  }),
}));

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('dispatches resetPassword on submit', async () => {
    // Mock the API calls to succeed
    const mockApiClient = await import('../../services/api');
    mockApiClient.default.post.mockResolvedValue({ data: {} });

    const store = configureStore({
      reducer: {
        passwordReset: passwordResetReducer,
        auth: authReducer,
      },
      preloadedState: {
        passwordReset: {
          status: 'idle',
          tokenValidationStatus: 'idle',
          error: null,
        },
        auth: {
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
          isCheckingSession: false,
        },
      },
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=tkn1234567']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    // Wait for token validation to complete and form to render
    await waitFor(() => {
      expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
    });

    const input = screen.getByLabelText(/new password/i);
    fireEvent.change(input, { target: { value: 'MyNewPass123!' } });

    const submitButton = screen.getByRole('button', { name: /reset password/i });
    fireEvent.click(submitButton);

    // Wait for the API to be called with the correct parameters
    await waitFor(() => {
      expect(mockApiClient.default.post).toHaveBeenCalledWith('/auth/password-reset-complete', {
        token: 'tkn1234567',
        password: 'MyNewPass123!',
      });
    });

    // Wait for success state to be reached in the store
    await waitFor(() => {
      const state = store.getState();
      expect(state.passwordReset.status).toBe('succeeded');
    });

    // Verify the success message is displayed
    await waitFor(() => {
      expect(screen.getByText(/password has been reset successfully/i)).toBeInTheDocument();
    });
  });
});
