import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Container, Typography, Box, CircularProgress, Alert, Paper } from '@mui/material';
import { RootState, AppDispatch } from '../store';
import {
  fetchWalletDetail,
  fetchWalletTransactions,
  clearWalletDetail,
} from '../store/walletDetailSlice';
import BalanceAreaChart from '../components/BalanceAreaChart';
import TransactionTable from '../components/TransactionTable';

const WalletDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const dispatch = useDispatch<AppDispatch>();
  const { wallet, transactions, status, error } = useSelector((state: RootState) => state.walletDetail);

  useEffect(() => {
    if (id) {
      dispatch(fetchWalletDetail(id));
      dispatch(fetchWalletTransactions(id));
    }
    return () => {
      dispatch(clearWalletDetail());
    };
  }, [dispatch, id]);

  if (status === 'loading' || !wallet) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" mt={4}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        {wallet.name}
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle2">Address</Typography>
            <Typography variant="body2" gutterBottom>
              {wallet.address}
            </Typography>
            <Typography variant="subtitle2">Balance</Typography>
            <Typography variant="h6" color="primary">
              {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: wallet.currency,
              }).format(wallet.balance)}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Last updated {new Date(wallet.lastUpdated).toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ flex: 2 }}>
            <BalanceAreaChart data={wallet.trend} />
          </Box>
        </Box>
      </Paper>

      <Typography variant="h5" gutterBottom>
        Transactions
      </Typography>

      <TransactionTable transactions={transactions} />
    </Container>
  );
};

export default WalletDetailPage;
