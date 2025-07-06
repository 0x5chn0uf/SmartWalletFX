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
    const store = configureStore({ reducer: { auth: authReducer } });
    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={["/secret"]}>
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
    const store = configureStore({
      reducer: { auth: authReducer },
      preloadedState: { auth: { isAuthenticated: true, user: null, status: 'idle', error: null } },
    });
    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={["/secret"]}>
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
});
