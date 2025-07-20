import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import passwordResetReducer, { requestReset } from '../../store/passwordResetSlice';
import authReducer from '../../store/authSlice';
import ForgotPasswordPage from '../../pages/ForgotPasswordPage';
import { vi } from 'vitest';

// Mock the async thunk to return a proper Redux action with unwrap method
vi.mock('../../store/passwordResetSlice', async () => {
  const actual = await vi.importActual('../../store/passwordResetSlice');
  return {
    ...actual,
    requestReset: vi.fn(email => ({
      type: 'passwordReset/request/pending',
      payload: undefined,
      meta: {
        arg: email,
        requestId: 'test-request-id',
        requestStatus: 'pending',
      },
      unwrap: vi.fn(() => Promise.resolve()),
    })),
  };
});

// Mock the useAuth hook to return default non-authenticated state
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: false,
    status: 'idle',
  }),
}));

const store = configureStore({
  reducer: {
    passwordReset: passwordResetReducer,
    auth: authReducer,
  },
});

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('dispatches requestReset on submit', async () => {
    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /send reset link/i });

    fireEvent.change(emailInput, {
      target: { value: 'test@example.com' },
    });

    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(requestReset).toHaveBeenCalledWith('test@example.com');
    });
  });
});
