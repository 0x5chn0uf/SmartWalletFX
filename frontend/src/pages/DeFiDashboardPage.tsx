import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import TableBody from '@mui/material/TableBody';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import WalletAddressHeader from '../components/WalletAddressHeader';
import InteractiveTimelineChart from '../components/InteractiveTimelineChart';
import EnhancedTopPositions from '../components/EnhancedTopPositions';
import EnhancedFeatureLockedModal from '../components/EnhancedFeatureLockedModal';
import FeatureLockedToast from '../components/FeatureLockedToast';
import FloatingActionButton from '../components/FloatingActionButton';

const MOCK = {
  walletAddress: '0x742d35cc6df08fc34234523523Cf6E231c2f6E',
  totalValue: 42500,
  totalValueChange: 2.3,
  totalValueChangeAbs: 950,
  apy: 7.25,
  apyProjected: 3800,
  apyRealized: 2400,
  netDeposits: 18000,
  netWithdrawals: 7000,
  net: 11000,
  timeline: {},
  timelineChanges: [
    { label: '24h', value: '+2.3%', color: 'var(--success)' },
    { label: '7d', value: '+5.8%', color: 'var(--accent-secondary)' },
    { label: '30d', value: '+12.1%', color: 'var(--warning)' },
  ],
  positions: [
    { asset: 'WBTC', protocol: 'Yearn', value: 22000, apy: 9.1, icon: 'W' },
    { asset: 'ETH', protocol: 'Aave', value: 12000, apy: 5.2, icon: 'E' },
    { asset: 'USDC', protocol: 'Compound', value: 8500, apy: 3.8, icon: 'U' },
  ],
};


const DeFiDashboardPage: React.FC = () => {
  const { address } = useParams<{ address: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isSmDown = useMediaQuery(theme.breakpoints.down('sm'));
  const [modalOpen, setModalOpen] = useState(false);
  const [toastVisible, setToastVisible] = useState(false);

  // Use the address from the URL or fall back to the mock address
  const walletAddress = address || MOCK.walletAddress;

  const handleLockedFeatureClick = () => {
    setToastVisible(true);
  };

  const handleUnlockClick = () => {
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
  };

  const handleToastClose = () => {
    setToastVisible(false);
  };

  const handleRefresh = () => {
    // Simulate data refresh - implement actual refresh logic here
  };

  const handleStartTrial = () => {
    navigate('/login-register', { state: { from: location.pathname } });
  };

  return (
    <Box className="dashboard-container" sx={{ maxWidth: 1200, mx: 'auto', my: 5 }}>
      {/* Wallet Address Header */}
      <WalletAddressHeader address={walletAddress} isPreviewMode={true} />

      {/* Combined Portfolio & Positions Card */}
      <Box
        sx={{
          position: 'relative',
          mb: 3,
          background: 'var(--color-surface)',
          borderRadius: 2,
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
          minHeight: 400,
          display: 'flex',
          flexDirection: 'column',
          transition: 'all 0.3s ease',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: 'linear-gradient(90deg, var(--color-primary), var(--accent-secondary), var(--success))',
          },
          '&:hover': {
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25), 0 0 30px rgba(79, 209, 199, 0.2)',
          },
        }}
      >
        <InteractiveTimelineChart
          totalValue={MOCK.totalValue}
          totalValueChange={MOCK.totalValueChange}
          totalValueChangeAbs={MOCK.totalValueChangeAbs}
          onLockedFeatureClick={handleLockedFeatureClick}
          walletAddress={walletAddress}
          isAuthenticated={false} // TODO: Connect to actual auth state
        />
        
        <EnhancedTopPositions
          positions={MOCK.positions}
          onUnlockClick={handleUnlockClick}
        />
      </Box>

      {/* Metrics Row: APY and Net Deposits/Withdrawals */}
      <Box
        className="metrics-row"
        sx={{ display: 'flex', gap: isSmDown ? 1.5 : 3, mb: 4, flexWrap: 'wrap' }}
      >
        {/* APY Card */}
        <Box
          className="metric-card"
          sx={{
            position: 'relative',
            background: 'var(--color-surface)',
            borderRadius: 2,
            p: isSmDown ? 2 : 3,
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
            minWidth: 220,
            flex: '1 1 320px',
            mb: 1.5,
            border: '1px solid rgba(255, 255, 255, 0.1)',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '3px',
              background: 'linear-gradient(90deg, var(--color-primary), var(--accent-secondary), var(--success))',
              borderRadius: '8px 8px 0 0',
            },
            '&:hover': {
              boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25), 0 0 30px rgba(79, 209, 199, 0.2)',
            },
          }}
        >
          <Typography
            className="metric-label"
            sx={{ color: 'var(--text-secondary)', fontSize: 14, mb: 1 }}
          >
            Average APY
          </Typography>
          <Box
            className="metric-value-row"
            sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5, mb: 1 }}
          >
            <Typography
              className="metric-value"
              sx={{ fontSize: 32, fontWeight: 700, color: 'var(--color-primary)' }}
            >
              {MOCK.apy}%
            </Typography>
            <span
              className="apy-projected"
              style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', fontWeight: 500 }}
            >
              (${MOCK.apyProjected.toLocaleString()} projected)
            </span>
          </Box>
          <hr
            className="metric-divider"
            style={{
              width: '100%',
              height: 1,
              background: 'rgba(255,255,255,0.08)',
              border: 'none',
              margin: '16px 0 12px 0',
            }}
          />
          <Typography
            className="yield-title"
            sx={{ color: 'var(--text-secondary)', fontSize: '1.1rem', fontWeight: 600, mb: 1 }}
          >
            Realized vs Projected Yield
          </Typography>
          <Box
            className="yield-bars"
            sx={{ display: 'flex', gap: isSmDown ? 1.5 : 3, alignItems: 'flex-end', mt: 1 }}
          >
            <Box
              className="yield-bar"
              sx={{
                width: 60,
                height: 80,
                borderRadius: '8px 8px 0 0',
                background: 'linear-gradient(135deg, #10b981 0%, #4fd1c7 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                mb: 0,
              }}
            >
              ${MOCK.apyRealized.toLocaleString()}
              <div
                className="yield-bar-label"
                style={{
                  marginTop: 8,
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 700,
                  textShadow: '0 2px 8px #1a1f2e',
                }}
              >
                Realized
              </div>
            </Box>
            <Box
              className="yield-bar projected"
              sx={{
                width: 60,
                height: 120,
                borderRadius: '8px 8px 0 0',
                background: 'linear-gradient(135deg, #6366f1 0%, #4fd1c7 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                mb: 0,
              }}
            >
              ${MOCK.apyProjected.toLocaleString()}
              <div
                className="yield-bar-label"
                style={{
                  marginTop: 8,
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 700,
                  textShadow: '0 2px 8px #1a1f2e',
                }}
              >
                Projected
              </div>
            </Box>
          </Box>
        </Box>
        {/* Net Deposits/Withdrawals */}
        <Box
          className="net-section"
          sx={{
            position: 'relative',
            background: 'var(--color-surface)',
            borderRadius: 2,
            p: isSmDown ? 2 : 3,
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
            minWidth: 220,
            flex: '1 1 320px',
            mb: 1.5,
            border: '1px solid rgba(255, 255, 255, 0.1)',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '3px',
              background: 'linear-gradient(90deg, var(--color-primary), var(--accent-secondary), var(--success))',
              borderRadius: '8px 8px 0 0',
            },
            '&:hover': {
              boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25), 0 0 30px rgba(79, 209, 199, 0.2)',
            },
          }}
        >
          <Typography
            className="net-title"
            sx={{ color: 'var(--text-secondary)', fontSize: '1.1rem', fontWeight: 600, mb: 1 }}
          >
            Net Deposits vs Net Withdrawals
          </Typography>
          <Typography
            className="net-value"
            sx={{
              fontSize: 20,
              fontWeight: 700,
              mb: 0.5,
              color: 'var(--success)',
            }}
          >
            Net: +${MOCK.net.toLocaleString()}
          </Typography>
          <Box
            className="net-bars"
            sx={{ display: 'flex', gap: isSmDown ? 1.5 : 3, alignItems: 'flex-end', mt: 1 }}
          >
            <Box
              className="net-bar"
              sx={{
                width: 60,
                height: 120,
                borderRadius: '8px 8px 0 0',
                background: 'linear-gradient(135deg, #4fd1c7 0%, #3b82f6 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                mb: 0,
              }}
            >
              ${MOCK.netDeposits / 1000}k
              <div
                className="net-bar-label"
                style={{
                  marginTop: 8,
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 700,
                  textShadow: '0 2px 8px #1a1f2e',
                }}
              >
                Deposits
              </div>
            </Box>
            <Box
              className="net-bar withdrawal"
              sx={{
                width: 60,
                height: 60,
                borderRadius: '8px 8px 0 0',
                background: 'linear-gradient(135deg, #ef4444 0%, #f59e0b 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                mb: 0,
              }}
            >
              ${MOCK.netWithdrawals / 1000}k
              <div
                className="net-bar-label"
                style={{
                  marginTop: 8,
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 700,
                  textShadow: '0 2px 8px #1a1f2e',
                }}
              >
                Withdrawals
              </div>
            </Box>
          </Box>
        </Box>
      </Box>


      {/* Feature Locked Modal */}
      <EnhancedFeatureLockedModal
        open={modalOpen}
        onClose={handleModalClose}
        onStartTrial={handleStartTrial}
      />

      {/* Toast Notification */}
      <FeatureLockedToast
        show={toastVisible}
        onClose={handleToastClose}
      />

      {/* Floating Action Button */}
      <FloatingActionButton onRefresh={handleRefresh} />
    </Box>
  );
};

export default DeFiDashboardPage;
