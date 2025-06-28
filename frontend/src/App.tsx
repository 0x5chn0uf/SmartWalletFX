import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import WalletDetailPage from './pages/WalletDetailPage';
import { ColorModeToggle } from './components/ColorModeToggle/ColorModeToggle';
import WalletList from './pages/WalletList';
import { Provider } from 'react-redux';
import { ThemeProvider as CustomThemeProvider } from './providers/ThemeProvider';
import { store } from './store';
import { Navigate } from 'react-router-dom';
import NotificationManager from './components/NotificationManager';
import ErrorBoundary from './components/ErrorBoundary';
import DeFiDashboardPage from './pages/DeFiDashboardPage';
import { QueryClient, QueryClientProvider } from 'react-query';

function App() {
  const queryClient = React.useMemo(() => new QueryClient(), []);
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <CustomThemeProvider>
          <ErrorBoundary>
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
                <Route path="/login" element={<LoginPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/defi" element={<DeFiDashboardPage />} />
                <Route path="/wallets" element={<WalletList />} />
                <Route path="/wallets/:id" element={<WalletDetailPage />} />
                <Route path="/" element={<Navigate to="/login" replace />} />
              </Routes>
            </Router>
            <NotificationManager />
          </ErrorBoundary>
        </CustomThemeProvider>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
