import React from 'react';
import { Container, Box, CssBaseline } from '@mui/material';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Container maxWidth="lg">{children}</Container>
      </Box>
    </>
  );
};
