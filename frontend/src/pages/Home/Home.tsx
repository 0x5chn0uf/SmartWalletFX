import React from 'react';
import { Typography, Box, CircularProgress } from '@mui/material';
import { Layout } from '../../components/Layout/Layout';
import { useTimeline } from '../../hooks/useTimeline';
import { TimelineChart } from '../../components/Charts/TimelineChart';

// TODO: wire with actual wallet selection UI
const DEMO_ADDRESS = '0xmeta';

export const Home: React.FC = () => {
  const now = Math.floor(Date.now() / 1000);
  const oneMonthAgo = now - 60 * 60 * 24 * 30;

  const { data, loading, error } = useTimeline({
    address: DEMO_ADDRESS,
    from: oneMonthAgo,
    to: now,
  });

  return (
    <Layout>
      <Box sx={{ py: 4 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          SmartWalletFX
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          Your Smart Crypto Portfolio Tracker
        </Typography>

        {loading && <CircularProgress />}
        {error && <Typography color="error">{error}</Typography>}
        {data && data.length > 0 && <TimelineChart snapshots={data} />}
      </Box>
    </Layout>
  );
}; 