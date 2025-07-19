import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import EmailVerificationPage from '../../pages/EmailVerificationPage';
import emailVerificationReducer from '../../store/emailVerificationSlice';
import { vi } from 'vitest';

describe('EmailVerificationPage', () => {
  it('dispatches verifyEmail on submit', () => {
    const store = configureStore({ reducer: { emailVerification: emailVerificationReducer } });
    const spy = vi.spyOn(store, 'dispatch');

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/verify-email?token=abc123']}>
          <EmailVerificationPage />
        </MemoryRouter>
      </Provider>
    );

    fireEvent.click(screen.getByRole('button', { name: /go to dashboard/i }));
    expect(spy).toHaveBeenCalled();
  });
});
