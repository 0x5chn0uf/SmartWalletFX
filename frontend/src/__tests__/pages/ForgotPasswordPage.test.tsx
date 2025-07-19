import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import passwordResetReducer, { requestReset } from '../../store/passwordResetSlice';
import authReducer from '../../store/authSlice';
import ForgotPasswordPage from '../../pages/ForgotPasswordPage';
import { vi } from 'vitest';

vi.mock('../../store/passwordResetSlice', async () => {
  const actual = await vi.importActual('../../store/passwordResetSlice');
  return {
    ...actual,
    requestReset: vi.fn(() => ({ type: 'passwordReset/request' })),
  };
});

const store = configureStore({
  reducer: {
    passwordReset: passwordResetReducer,
    auth: authReducer,
  },
});

describe('ForgotPasswordPage', () => {
  it('dispatches requestReset on submit', () => {
    render(
      <Provider store={store}>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </Provider>
    );
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.submit(screen.getByRole('button', { name: /send reset link/i }));
    expect(requestReset).toHaveBeenCalled();
  });
});
