import React from 'react';
import { Grid, Paper, Typography, Box } from '@mui/material';

interface Wallet {
  id: string;
  name: string;
  balance: number;
  currency?: string;
}

interface StatsCardsProps {
  wallets: Wallet[];
}

const formatCurrency = (value: number): string =>
  value.toLocaleString(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  });

const StatsCards: React.FC<StatsCardsProps> = ({ wallets }) => {
  if (!wallets || wallets.length === 0) {
    return null;
  }

  const totalBalance = wallets.reduce((sum, w) => sum + (w.balance || 0), 0);
  const topWallet = wallets.reduce(
    (prev, cur) => (cur.balance > (prev?.balance || 0) ? cur : prev),
    wallets[0]
  );

  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      <Grid item xs={12} md={4}>
        <Paper elevation={2}>
          <Box p={2}>
            <Typography variant="subtitle2" color="textSecondary" gutterBottom>
              Total Wallets
            </Typography>
            <Typography variant="h5">{wallets.length}</Typography>
          </Box>
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper elevation={2}>
          <Box p={2}>
            <Typography variant="subtitle2" color="textSecondary" gutterBottom>
              Total Balance
            </Typography>
            <Typography variant="h5">{formatCurrency(totalBalance)}</Typography>
          </Box>
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper elevation={2}>
          <Box p={2}>
            <Typography variant="subtitle2" color="textSecondary" gutterBottom>
              Top Wallet
            </Typography>
            <Typography variant="body1">{topWallet?.name || 'N/A'}</Typography>
            <Typography variant="h6" color="primary">
              {formatCurrency(topWallet?.balance || 0)}
            </Typography>
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default StatsCards;
