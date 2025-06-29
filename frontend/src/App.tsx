import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box, CssBaseline } from '@mui/material';
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
import { Layout } from './components/Layout/Layout';
import LoginRegisterPage from './pages/LoginRegisterPage';

const queryClient = new QueryClient();

// Navbar component: hidden on landing page
const NavBar: React.FC = () => {
  const location = useLocation();
  if (location.pathname === '/' || location.pathname === '/login-register') return null;
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div">
          SmartWalletFX
        </Typography>
        <Box sx={{ flexGrow: 1, ml: 2 }}>
          <Link
            to="/dashboard"
            style={{ color: 'inherit', textDecoration: 'none', marginRight: '1rem' }}
          >
            Dashboard
          </Link>
          <Link
            to="/defi"
            style={{ color: 'inherit', textDecoration: 'none', marginRight: '1rem' }}
          >
            DeFi Tracker
          </Link>
          <Link to="/wallets" style={{ color: 'inherit', textDecoration: 'none' }}>
            Wallets
          </Link>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

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
