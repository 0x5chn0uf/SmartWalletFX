import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Container, 
  Typography, 
  TextField, 
  Box, 
  CircularProgress,
  Alert
} from '@mui/material';
import { RootState, AppDispatch } from '../store';
import { fetchWallets, setSearch, setPage } from '../store/walletsSlice';
import WalletTable from '../components/WalletTable';
import Pagination from '../components/Pagination';
import useNotification from '../hooks/useNotification';

const WalletList: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { wallets, total, page, limit, search, status, error } = useSelector(
    (state: RootState) => state.wallets
  );
  const [searchInput, setSearchInput] = useState(search);
  const { showError } = useNotification();

  useEffect(() => {
    dispatch(fetchWallets({ page, limit, search })).catch((err) => {
      showError('Failed to load wallets. Please try again.');
    });
  }, [dispatch, page, limit, search, showError]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchInput(event.target.value);
  };

  const handleSearchSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    dispatch(setSearch(searchInput));
  };

  const handlePageChange = (newPage: number) => {
    dispatch(setPage(newPage));
  };

  if (status === 'loading') {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" mt={4}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Wallet List
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSearchSubmit} sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Search wallets"
          value={searchInput}
          onChange={handleSearchChange}
          placeholder="Enter wallet name..."
          sx={{ maxWidth: 400 }}
        />
      </Box>

      <WalletTable wallets={wallets} />

      <Pagination
        page={page}
        total={total}
        limit={limit}
        onPageChange={handlePageChange}
      />
    </Container>
  );
};

export default WalletList; 