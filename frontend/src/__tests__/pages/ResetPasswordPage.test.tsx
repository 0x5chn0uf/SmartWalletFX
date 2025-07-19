import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import ResetPasswordPage from '../../pages/ResetPasswordPage';
import passwordResetReducer, { resetPassword } from '../../store/passwordResetSlice';
import authReducer from '../../store/authSlice';
import { vi } from 'vitest';

describe('ResetPasswordPage', () => {
  it('dispatches resetPassword on submit', async () => {
    const store = configureStore({
      reducer: {
        passwordReset: passwordResetReducer,
        auth: authReducer,
      },
      preloadedState: {
        passwordReset: {
          status: 'idle',
          tokenValidationStatus: 'succeeded',
          error: null,
          successMessage: null,
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
    const spy = vi.spyOn(store, 'dispatch');

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=tkn1234567']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    // Wait for the form to render
    const input = await screen.findByLabelText(/new password/i);
    fireEvent.change(input, { target: { value: 'MyNewPass123!' } });
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));

    expect(spy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: resetPassword.pending.type,
      })
    );
  });
});
