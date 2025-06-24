import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import authReducer from '../../store/authSlice';
import LoginPage from '../../pages/LoginPage';

describe('LoginPage', () => {
  function renderWithStore(preloadedState: any) {
    const store = configureStore({
      reducer: { auth: authReducer },
      preloadedState,
    });
    return render(
      <Provider store={store}>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </Provider>
    );
  }

  it('renders login form', () => {
    renderWithStore({ auth: { user: null, status: 'idle', error: null } });
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });
}); 