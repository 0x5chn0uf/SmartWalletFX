import React, { useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Global, css } from '@emotion/react';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { Provider, useDispatch as useReduxDispatch } from 'react-redux';
import { store, AppDispatch } from './store';
import NotificationManager from './components/NotificationManager';
import ErrorBoundary from './components/ErrorBoundary';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import NavBar from './components/NavBar';
import PageSkeleton from './components/PageSkeleton';
import { fetchCurrentUser, sessionCheckStarted, sessionCheckFinished } from './store/authSlice';
import apiClient from './services/api';

// Lazy load all pages for code splitting
const LandingPage = lazy(() => import('./pages/LandingPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const WalletDetailPage = lazy(() => import('./pages/WalletDetailPage'));
const WalletList = lazy(() => import('./pages/WalletList'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const EmailVerificationPage = lazy(() => import('./pages/EmailVerificationPage'));
const VerifyEmailNoticePage = lazy(() => import('./pages/VerifyEmailNoticePage'));
const DeFiDashboardPage = lazy(() => import('./pages/DeFiDashboardPage'));
const LoginRegisterPage = lazy(() => import('./pages/LoginRegisterPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));
const UnauthorizedPage = lazy(() => import('./pages/UnauthorizedPage'));

const queryClient = new QueryClient();

// AppContent component for testing - contains all App logic except Router
export const AppContent: React.FC = () => {
  const dispatch = useReduxDispatch<AppDispatch>();

  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');

    if (storedToken) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      localStorage.setItem('access_token', storedToken);

      // Token is ready – fetch current user to populate store
      dispatch(fetchCurrentUser());
    }

    // If there is no stored token, check if we have evidence of a previous session
    // before attempting a silent refresh
    if (!storedToken) {
      const hasSessionEvidence = localStorage.getItem('session_active') === '1';

      // Only attempt silent refresh if there's evidence of a previous session
      if (hasSessionEvidence) {
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
            // Silent refresh failed – clear session evidence and finish check
            localStorage.removeItem('session_active');
            dispatch(sessionCheckFinished());
          });
      } else {
        // No session evidence, skip silent refresh
        dispatch(sessionCheckFinished());
      }
    }
  }, [dispatch]);

  return (
    <>
      <NavBar />
      <Suspense fallback={<PageSkeleton />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login-register" element={<LoginRegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/verify-email" element={<EmailVerificationPage />} />
          <Route path="/verify-email-sent" element={<VerifyEmailNoticePage />} />
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
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
      <NotificationManager />
    </>
  );
};

const App: React.FC = () => {
  // Global CSS baseline styles
  const globalStyles = css`
    * {
      box-sizing: border-box;
    }

    html,
    body {
      margin: 0;
      padding: 0;
      font-family:
        -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell',
        'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      line-height: 1.5;
      background-color: #ffffff;
      color: #1f2937;
    }

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      margin: 0;
      font-weight: 600;
    }

    p {
      margin: 0;
    }

    button {
      font-family: inherit;
    }

    a {
      color: inherit;
      text-decoration: none;
    }
  `;

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <Global styles={globalStyles} />
        <QueryClientProvider client={queryClient}>
          <Router>
            <AppContent />
          </Router>
        </QueryClientProvider>
      </Provider>
    </ErrorBoundary>
  );
};

export default App;
