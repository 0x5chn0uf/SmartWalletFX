import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../providers/ThemeProvider';
import NavBar from '../../components/NavBar';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../../store/authSlice';
import { MemoryRouter } from 'react-router-dom';

describe('App Component', () => {
  it('renders navigation', () => {
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
    expect(screen.getByRole('link', { name: /portfolio/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument();
  });
});
