import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import passwordResetReducer, { requestReset } from '../../store/passwordResetSlice';
import ForgotPasswordPage from '../../pages/ForgotPasswordPage';

vi.mock('../../store/passwordResetSlice', async () => {
  const actual = await vi.importActual('../../store/passwordResetSlice');
  return {
    ...actual,
    requestReset: vi.fn(() => ({ type: 'passwordReset/request' })),
  };
});

const store = configureStore({ reducer: { passwordReset: passwordResetReducer } });

describe('ForgotPasswordPage', () => {
  it('dispatches requestReset on submit', () => {
    render(
      <Provider store={store}>
        <ForgotPasswordPage />
      </Provider>
    );
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.submit(screen.getByRole('button'));
    expect(requestReset).toHaveBeenCalled();
  });
});
