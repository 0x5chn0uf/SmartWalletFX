import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import WalletDetailPage from './pages/WalletDetailPage';
import { ColorModeToggle } from './components/ColorModeToggle/ColorModeToggle';
import WalletList from './pages/WalletList';
import { Provider } from 'react-redux';
import { ThemeProvider } from './providers/ThemeProvider';
import { store } from './store';
import { Navigate } from 'react-router-dom';
import NotificationManager from './components/NotificationManager';
import ErrorBoundary from './components/ErrorBoundary';
import DeFiDashboardPage from './pages/DeFiDashboardPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemeProvider>
          <QueryClientProvider client={queryClient}>
            <Router>
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
                  <ColorModeToggle />
                </Toolbar>
              </AppBar>
              <Routes>
                <Route path="/" element={<LoginPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/defi" element={<DeFiDashboardPage />} />
                <Route path="/wallets" element={<WalletList />} />
                <Route path="/wallets/:id" element={<WalletDetailPage />} />
                <Route path="/" element={<Navigate to="/login" replace />} />
              </Routes>
            </Router>
            <NotificationManager />
          </QueryClientProvider>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
