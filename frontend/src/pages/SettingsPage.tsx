import React from 'react';
import { Box, Typography, Container } from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>

        <Typography variant="body1" color="text.secondary">
          Settings functionality coming soon...
        </Typography>
      </Box>
    </Container>
  );
};

export default SettingsPage;
