import React from 'react';
import { Box, Skeleton, Container } from '@mui/material';

const PageSkeleton: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        {/* Page title skeleton */}
        <Skeleton variant="text" sx={{ fontSize: '2.5rem', mb: 3, width: '40%' }} />

        {/* Navigation or breadcrumb skeleton */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
          <Skeleton variant="rectangular" width={100} height={40} />
          <Skeleton variant="rectangular" width={100} height={40} />
          <Skeleton variant="rectangular" width={100} height={40} />
        </Box>

        {/* Main content area skeleton */}
        <Box
          sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}
        >
          <Skeleton variant="rectangular" height={200} />
          <Skeleton variant="rectangular" height={200} />
        </Box>

        {/* Secondary content skeleton */}
        <Box sx={{ mb: 4 }}>
          <Skeleton variant="text" sx={{ fontSize: '1.5rem', mb: 2, width: '30%' }} />
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Skeleton variant="text" height={24} />
            <Skeleton variant="text" height={24} width="80%" />
            <Skeleton variant="text" height={24} width="60%" />
          </Box>
        </Box>

        {/* Chart or data visualization skeleton */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3 }}>
          <Box>
            <Skeleton variant="text" sx={{ fontSize: '1.25rem', mb: 2, width: '25%' }} />
            <Skeleton variant="rectangular" height={300} />
          </Box>
          <Box>
            <Skeleton variant="text" sx={{ fontSize: '1.25rem', mb: 2, width: '35%' }} />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Skeleton variant="rectangular" height={60} />
              <Skeleton variant="rectangular" height={60} />
              <Skeleton variant="rectangular" height={60} />
              <Skeleton variant="rectangular" height={60} />
            </Box>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default PageSkeleton;
