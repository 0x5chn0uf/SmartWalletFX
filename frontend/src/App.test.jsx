import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from './providers/ThemeProvider';
import NavBar from './components/NavBar';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './store/authSlice';
import { MemoryRouter } from 'react-router-dom';

test('renders navigation links', () => {
  // ensure the NavBar is visible by navigating to dashboard route
  window.history.pushState({}, '', '/dashboard');

  const store = configureStore({
    reducer: { auth: authReducer },
    preloadedState: { auth: { isAuthenticated: true, user: null, status: 'idle', error: null } },
  });

  render(
    <Provider store={store}>
      <MemoryRouter initialEntries={['/dashboard']}>
        <ThemeProvider>
          <NavBar />
        </ThemeProvider>
      </MemoryRouter>
    </Provider>
  );

  expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /defi/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument();
});
