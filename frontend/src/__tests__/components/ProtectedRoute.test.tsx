import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import authReducer from '../../store/authSlice';
import ProtectedRoute from '../../components/auth/ProtectedRoute';

const TestComponent = () => <div>Protected Content</div>;

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users to login-register', () => {
    // @ts-expect-error testing store
    const store = configureStore({
      reducer: { auth: authReducer },
      preloadedState: {
        auth: { isAuthenticated: false, user: null, status: 'succeeded', error: null },
      } as any,
    });
    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/secret']}>
          <Routes>
            <Route
              path="/secret"
              element={
                <ProtectedRoute>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
            <Route path="/login-register" element={<div>Login</div>} />
          </Routes>
        </MemoryRouter>
      </Provider>
    );
    expect(screen.getByText('Login')).toBeInTheDocument();
  });

  it('allows access when authenticated', () => {
    // @ts-expect-error testing store
    const store = configureStore({
      reducer: { auth: authReducer },
      preloadedState: {
        auth: { isAuthenticated: true, user: null, status: 'succeeded', error: null },
      } as any,
    });
    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/secret']}>
          <Routes>
            <Route
              path="/secret"
              element={
                <ProtectedRoute>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
            <Route path="/login-register" element={<div>Login</div>} />
          </Routes>
        </MemoryRouter>
      </Provider>
    );
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('renders null during loading state when session flag set', () => {
    localStorage.setItem('session_active', '1');
    // @ts-expect-error testing store
    const store = configureStore({
      reducer: { auth: authReducer },
      preloadedState: {
        auth: { isAuthenticated: false, user: null, status: 'loading', error: null },
      } as any,
    });
    const { container } = render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/secret']}>
          <Routes>
            <Route
              path="/secret"
              element={
                <ProtectedRoute>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </Provider>
    );
    expect(container).toBeEmptyDOMElement();
    localStorage.removeItem('session_active');
  });

  it('redirects when role mismatch', () => {
    // @ts-expect-error testing store
    const store = configureStore({
      reducer: { auth: authReducer },
      preloadedState: {
        auth: {
          isAuthenticated: true,
          user: { id: '1', username: 'x', email: 'e', role: 'user' },
          status: 'succeeded',
          error: null,
        },
      } as any,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <ProtectedRoute roles={['admin']}>
                  <div>Admin</div>
                </ProtectedRoute>
              }
            />
            <Route path="/unauthorized" element={<div>Denied</div>} />
          </Routes>
        </MemoryRouter>
      </Provider>
    );
    expect(screen.getByText('Denied')).toBeInTheDocument();
  });
});
