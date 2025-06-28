import React from 'react';
import { Box, Button, Container, Typography } from '@mui/material';

const HeroSection: React.FC = () => {
  return (
    <Box
      sx={{
        width: '100%',
        py: 8,
        background: 'linear-gradient(45deg, #0d1b2a 30%, #1b263b 90%)',
        color: 'white',
        textAlign: 'center',
      }}
    >
      <Container maxWidth="md">
        <Typography variant="h2" component="h1" gutterBottom>
          Your Smart Wallet for Algorithmic Trading
        </Typography>
        <Typography variant="h5" component="p" color="text.secondary" paragraph>
          Automate your strategies, manage your risk, and trade with confidence on the decentralized
          web.
        </Typography>
        <Box sx={{ mt: 4 }}>
          <Button variant="contained" color="primary" size="large" sx={{ mr: 2 }}>
            Launch App
          </Button>
          <Button variant="outlined" color="secondary" size="large">
            Connect Wallet
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default HeroSection;
