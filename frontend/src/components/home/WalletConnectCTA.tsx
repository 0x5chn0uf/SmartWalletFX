import React from 'react';
import { Box, Button, Container, Typography } from '@mui/material';

const WalletConnectCTA: React.FC = () => {
  return (
    <Box sx={{ py: 6, backgroundColor: 'background.paper' }}>
      <Container maxWidth="sm" sx={{ textAlign: 'center' }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Ready to Get Started?
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Connect your wallet to access the full suite of trading tools and features.
        </Typography>
        <Button variant="contained" color="primary" size="large">
          Connect Wallet
        </Button>
      </Container>
    </Box>
  );
};

export default WalletConnectCTA;
