import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';

const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();

  const handleGoToLogin = () => {
    navigate('/login-register');
  };

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          textAlign: 'center',
          gap: 3,
        }}
      >
        <LockOutlinedIcon sx={{ fontSize: 120, color: 'warning.main' }} />

        <Typography variant="h1" component="h1" sx={{ fontSize: '4rem', fontWeight: 'bold' }}>
          403
        </Typography>

        <Typography variant="h4" component="h2" gutterBottom>
          Access Denied
        </Typography>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          You don't have permission to access this page. Please log in with the appropriate
          credentials.
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button variant="contained" color="primary" onClick={handleGoToLogin} size="large">
            Sign In
          </Button>

          <Button variant="outlined" color="primary" onClick={handleGoHome} size="large">
            Go Home
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default UnauthorizedPage;
