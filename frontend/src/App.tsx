import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { CssBaseline } from '@mui/material';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import WalletDetailPage from './pages/WalletDetailPage';
import WalletList from './pages/WalletList';
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
import { fetchCurrentUser } from './store/authSlice';

const queryClient = new QueryClient();

const App: React.FC = () => {
  const dispatch = useReduxDispatch<AppDispatch>();

  useEffect(() => {
    dispatch(fetchCurrentUser());
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
                <Route path="/dashboard/:address" element={<DashboardPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <DashboardPage />
                    </ProtectedRoute>
                  }
                />
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
