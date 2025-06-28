import React from 'react';
import { Box, Card, CardContent, Container, Typography } from '@mui/material';

interface StatCardProps {
  title: string;
  value: string;
  description: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, description }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent sx={{ textAlign: 'center' }}>
      <Typography variant="h4" component="div" gutterBottom>
        {value}
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" component="div" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
    </CardContent>
  </Card>
);

const featuredStats = [
  {
    title: 'Total Trading Volume',
    value: '$1.2B+',
    description: 'Across all automated strategies since inception.',
  },
  {
    title: 'Active Bots',
    value: '7,500+',
    description: 'Currently executing trades across multiple pairs.',
  },
  {
    title: 'Supported Networks',
    value: '5+',
    description: 'Including Ethereum, BSC, Polygon, and more.',
  },
];

const FeaturedStats: React.FC = () => {
  return (
    <Box sx={{ py: 8, backgroundColor: 'background.default' }}>
      <Container maxWidth="lg">
        <Typography variant="h3" component="h2" sx={{ textAlign: 'center', mb: 6 }}>
          Platform by the Numbers
        </Typography>
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 4,
            justifyContent: 'center',
          }}
        >
          {featuredStats.map(stat => (
            <Box
              key={stat.title}
              sx={{
                width: { xs: '100%', sm: 'calc(50% - 2rem)', md: 'calc(33.333% - 2rem)' },
              }}
            >
              <StatCard title={stat.title} value={stat.value} description={stat.description} />
            </Box>
          ))}
        </Box>
      </Container>
    </Box>
  );
};

export default FeaturedStats;
