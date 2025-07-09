import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CssBaseline } from '@mui/material';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import WalletDetailPage from './pages/WalletDetailPage';
import WalletList from './pages/WalletList';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { Provider, useDispatch as useReduxDispatch } from 'react-redux';
import { ThemeProvider } from './providers/ThemeProvider';
import { store, AppDispatch } from './store';
import NotificationManager from './components/NotificationManager';
import ErrorBoundary from './components/ErrorBoundary';
import DeFiDashboardPage from './pages/DeFiDashboardPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LoginRegisterPage from './pages/LoginRegisterPage';
import NavBar from './components/NavBar';
import { fetchCurrentUser, sessionCheckStarted, sessionCheckFinished } from './store/authSlice';
import apiClient from './services/api';

const queryClient = new QueryClient();

const App: React.FC = () => {
  const dispatch = useReduxDispatch<AppDispatch>();

  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');

    if (storedToken) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      localStorage.setItem('access_token', storedToken);

      // Token is ready – fetch current user to populate store
      dispatch(fetchCurrentUser());
    }

    // If there is no stored token we attempt a silent refresh once – if the
    // browser carries a valid refresh_token cookie the call will succeed.
    if (!storedToken) {
      // Indicate that we are performing a silent session check
      dispatch(sessionCheckStarted());

      apiClient
        .post('/auth/refresh', {}, { withCredentials: true })
        .then(resp => {
          const newToken = resp.data?.access_token as string | undefined;
          if (newToken) {
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
            localStorage.setItem('access_token', newToken);
            dispatch(fetchCurrentUser());
          } else {
            // No token in response – finish session check without session
            dispatch(sessionCheckFinished());
          }
        })
        .catch(() => {
          // Silent refresh failed – finish session check so UI can redirect
          dispatch(sessionCheckFinished());
        });
    }
  }, [dispatch]);

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemeProvider>
          <CssBaseline />
          <QueryClientProvider client={queryClient}>
            <Router>
              <NavBar />
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login-register" element={<LoginRegisterPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <DashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route path="/defi/:address" element={<DeFiDashboardPage />} />
                <Route
                  path="/defi"
                  element={
                    <ProtectedRoute>
                      <DeFiDashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/wallets"
                  element={
                    <ProtectedRoute>
                      <WalletList />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/wallets/:id"
                  element={
                    <ProtectedRoute>
                      <WalletDetailPage />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </Router>
            <NotificationManager />
          </QueryClientProvider>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
};

export default App;
