import React from 'react';
import { Typography, Box } from '@mui/material';
import { Layout } from '../../components/Layout/Layout';

export const Home: React.FC = () => {
  return (
    <Layout>
      <Box sx={{ py: 4 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          SmartWalletFX
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          Your Smart Crypto Portfolio Tracker
        </Typography>
      </Box>
    </Layout>
  );
}; 