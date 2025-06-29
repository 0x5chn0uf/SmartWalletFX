import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const FEATURES = [
  { title: 'Unified Dashboard', description: 'View all your investments in one place.' },
  { title: 'Performance Metrics', description: 'Get detailed insights and performance summaries.' },
  {
    title: 'Alerts & Notifications',
    description: 'Stay informed with custom price and portfolio alerts.',
  },
  { title: 'Secure Sync', description: 'Protect your data with industry-standard encryption.' },
];

const LandingPage: React.FC = () => {
  return (
    <Box
      sx={{
        backgroundColor: 'background.default',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        pb: 6,
      }}
    >
      <Box sx={{ flex: 1 }}>
        <Box
          component="header"
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            px: 3,
            py: 2,
            backgroundColor: 'background.paper',
          }}
        >
          <Typography
            variant="h6"
            component="a"
            href="#"
            sx={{
              color: 'primary.main',
              textDecoration: 'none',
              fontWeight: 800,
              fontSize: '24px',
            }}
          >
            SmartWalletFX
          </Typography>
          <Box component="nav">
            <Box
              component="a"
              href="#features"
              sx={{
                mx: 2,
                color: 'text.secondary',
                textDecoration: 'none',
                fontWeight: 500,
                '&:hover': { color: 'text.primary' },
              }}
            >
              Features
            </Box>
            <Box
              component="a"
              href="#pricing"
              sx={{
                mx: 2,
                color: 'text.secondary',
                textDecoration: 'none',
                fontWeight: 500,
                '&:hover': { color: 'text.primary' },
              }}
            >
              Pricing
            </Box>
            <Box
              component={RouterLink}
              to="/login"
              sx={{
                mx: 2,
                color: 'text.secondary',
                textDecoration: 'none',
                fontWeight: 500,
                '&:hover': { color: 'text.primary' },
              }}
            >
              Login
            </Box>
          </Box>
        </Box>

        <Box
          component="section"
          sx={{
            backgroundColor: 'background.paper',
            px: 3,
            py: 10,
            textAlign: 'center',
          }}
        >
          <Typography
            variant="h1"
            component="h1"
            sx={{
              fontSize: { xs: '40px', md: '56px' },
              fontWeight: 700,
              mb: 2,
              lineHeight: 1.1,
            }}
          >
            Track. Analyze. Grow.
          </Typography>
          <Typography
            variant="body1"
            paragraph
            sx={{ color: 'text.secondary', fontSize: '18px', mb: 4 }}
          >
            All-in-one portfolio management for crypto and traditional assets.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            size="large"
            component={RouterLink}
            to="/login"
            sx={{
              py: 1.5,
              px: 3,
              fontWeight: 500,
              color: '#1f2937',
              fontSize: '16px',
              lineHeight: 1.2,
              '&:hover': {
                backgroundColor: '#3eb9ad',
              },
            }}
          >
            Start Tracking
          </Button>
        </Box>

        <Box component="section" id="features" sx={{ flex: 1, px: 3, py: 4 }}>
          <Box
            sx={{
              margin: '0 auto',
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(4, 1fr)',
              },
              gap: 3,
              px: 0,
            }}
          >
            {FEATURES.map(feature => (
              <Box
                key={feature.title}
                sx={{
                  backgroundColor: 'background.paper',
                  p: 2,
                  borderRadius: 1,
                  textAlign: 'center',
                  height: '100%',
                  width: '100%',
                }}
              >
                <Typography
                  variant="h6"
                  component="h3"
                  sx={{ mb: 1, color: 'text.primary', fontSize: '22px', fontWeight: 700 }}
                >
                  {feature.title}
                </Typography>
                <Typography
                  variant="body1"
                  sx={{ color: 'text.secondary', fontSize: '16px', mt: 1 }}
                >
                  {feature.description}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      </Box>

      <Box
        component="footer"
        sx={{ backgroundColor: 'background.paper', textAlign: 'center', px: 2, py: 2 }}
      >
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          © 2025 SmartWalletFX. All rights reserved.
        </Typography>
      </Box>
    </Box>
  );
};

export default LandingPage;
