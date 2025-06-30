import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CssBaseline } from '@mui/material';
import LoginPage from './pages/LoginPage';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import WalletDetailPage from './pages/WalletDetailPage';
import WalletList from './pages/WalletList';
import { Provider } from 'react-redux';
import { ThemeProvider } from './providers/ThemeProvider';
import { store } from './store';
import NotificationManager from './components/NotificationManager';
import ErrorBoundary from './components/ErrorBoundary';
import DeFiDashboardPage from './pages/DeFiDashboardPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LoginRegisterPage from './pages/LoginRegisterPage';
import NavBar from './components/NavBar';

const queryClient = new QueryClient();

const App: React.FC = () => {
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
                <Route path="/login" element={<LoginPage />} />
                <Route path="/login-register" element={<LoginRegisterPage />} />
                <Route path="/dashboard/:address" element={<DashboardPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/defi" element={<DeFiDashboardPage />} />
                <Route path="/wallets" element={<WalletList />} />
                <Route path="/wallets/:id" element={<WalletDetailPage />} />
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
