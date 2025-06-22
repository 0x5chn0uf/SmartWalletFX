import React from 'react';
import { Avatar, Box, Container, Paper, Typography } from '@mui/material';
import SecurityIcon from '@mui/icons-material/Security';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import WorkspacePremiumIcon from '@mui/icons-material/WorkspacePremium';

const trustSignals = [
  {
    icon: <SecurityIcon fontSize="large" />,
    title: 'Bank-Grade Security',
    description:
      'Your assets are protected with industry-leading security protocols and encryption.',
  },
  {
    icon: <VerifiedUserIcon fontSize="large" />,
    title: 'Verified by Audits',
    description: 'Our smart contracts are regularly audited by top-tier security firms.',
  },
  {
    icon: <WorkspacePremiumIcon fontSize="large" />,
    title: 'Community Trusted',
    description:
      'Join thousands of satisfied traders who trust our platform to automate their strategies.',
  },
];

const TrustBanner: React.FC = () => {
  return (
    <Box sx={{ py: 8, backgroundColor: 'background.default' }}>
      <Container maxWidth="lg">
        <Typography variant="h3" component="h2" sx={{ textAlign: 'center', mb: 6 }}>
          A Platform You Can Trust
        </Typography>
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 4,
            justifyContent: 'center',
          }}
        >
          {trustSignals.map(signal => (
            <Box
              key={signal.title}
              sx={{
                width: { xs: '100%', md: 'calc(33.333% - 2rem)' },
              }}
            >
              <Paper elevation={3} sx={{ p: 4, textAlign: 'center', height: '100%' }}>
                <Avatar
                  sx={{ bgcolor: 'secondary.main', mx: 'auto', mb: 2, width: 56, height: 56 }}
                >
                  {signal.icon}
                </Avatar>
                <Typography variant="h5" component="h3" gutterBottom>
                  {signal.title}
                </Typography>
                <Typography color="text.secondary">{signal.description}</Typography>
              </Paper>
            </Box>
          ))}
        </Box>
      </Container>
    </Box>
  );
};

export default TrustBanner;
