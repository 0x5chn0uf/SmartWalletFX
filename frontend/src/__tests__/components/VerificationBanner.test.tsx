import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../../store/authSlice';
import verificationReducer, { resendVerification } from '../../store/emailVerificationSlice';
import VerificationBanner from '../../components/auth/VerificationBanner';
import { vi } from 'vitest';

vi.mock('../../store/emailVerificationSlice', async () => {
  const actual = await vi.importActual('../../store/emailVerificationSlice');
  return {
    ...actual,
    resendVerification: vi.fn(() => ({ type: 'emailVerification/resend' })),
  };
});

function renderWithState(state: any) {
  const store = configureStore({
    reducer: { auth: authReducer, emailVerification: verificationReducer },
    preloadedState: state as any,
  });
  return render(
    <Provider store={store}>
      <VerificationBanner />
    </Provider>
  );
}

describe('VerificationBanner', () => {
  it('does not render when user is verified', () => {
    renderWithState({
      auth: {
        isAuthenticated: true,
        user: { id: '1', username: 'u', email: 'e', email_verified: true },
        status: 'succeeded',
        error: null,
      },
    });
    expect(screen.queryByText(/please verify/i)).not.toBeInTheDocument();
  });

  it('dispatches resendVerification on click', () => {
    renderWithState({
      auth: {
        isAuthenticated: true,
        user: { id: '1', username: 'u', email: 'e@example.com', email_verified: false },
        status: 'succeeded',
        error: null,
      },
    });
    fireEvent.click(screen.getByRole('button', { name: /resend/i }));
    expect(resendVerification).toHaveBeenCalledWith('e@example.com');
  });
});
