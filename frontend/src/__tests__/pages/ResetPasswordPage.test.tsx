// @ts-nocheck
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import ResetPasswordPage from '../../pages/ResetPasswordPage';
import passwordResetReducer, { resetPassword } from '../../store/passwordResetSlice';
import { vi } from 'vitest';

describe('ResetPasswordPage', () => {
  it('dispatches resetPassword on submit', () => {
    const store = configureStore({ reducer: { passwordReset: passwordResetReducer } });
    const spy = vi.spyOn(store, 'dispatch');

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/reset-password?token=tkn1234567']}>
          <ResetPasswordPage />
        </MemoryRouter>
      </Provider>
    );

    const input = screen.getByLabelText(/new password/i);
    fireEvent.change(input, { target: { value: 'MyNewPass123!' } });
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));

    expect(spy).toHaveBeenCalled();
  });
});
