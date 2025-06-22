import React from 'react';
import {
  Avatar,
  Box,
  Container,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Typography,
} from '@mui/material';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import BoltIcon from '@mui/icons-material/Bolt';
import SecurityIcon from '@mui/icons-material/Security';

const recentActivities = [
  {
    icon: <ShowChartIcon />,
    primary: 'New Strategy Deployed',
    secondary: 'ETH/USDT grid strategy launched with a 5% profit target.',
    time: '5 minutes ago',
  },
  {
    icon: <BoltIcon />,
    primary: 'Risk Threshold Adjusted',
    secondary: 'Global stop-loss updated to 15% across all active bots.',
    time: '1 hour ago',
  },
  {
    icon: <SecurityIcon />,
    primary: 'Security Audit Passed',
    secondary: 'Annual security audit completed with no critical findings.',
    time: '1 day ago',
  },
];

const RecentActivityList: React.FC = () => {
  return (
    <Box sx={{ py: 8, backgroundColor: 'background.paper' }}>
      <Container maxWidth="md">
        <Typography variant="h3" component="h2" sx={{ textAlign: 'center', mb: 6 }}>
          Latest Platform Activity
        </Typography>
        <List>
          {recentActivities.map((activity, index) => (
            <ListItem key={index} alignItems="flex-start">
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'primary.main' }}>{activity.icon}</Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={activity.primary}
                secondary={activity.secondary}
                primaryTypographyProps={{ variant: 'h6' }}
              />
              <Typography variant="caption" color="text.secondary">
                {activity.time}
              </Typography>
            </ListItem>
          ))}
        </List>
      </Container>
    </Box>
  );
};

export default RecentActivityList;
