import React, { useState } from 'react';
import { Container, Paper, Typography, Tabs, Tab, Box, Avatar, Grid } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import ProfileForm from '../components/profile/ProfileForm';
import ProfilePictureUpload from '../components/profile/ProfilePictureUpload';
import PasswordChangeForm from '../components/profile/PasswordChangeForm';
import NotificationSettings from '../components/profile/NotificationSettings';
import AccountDeletion from '../components/profile/AccountDeletion';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index, ...other }: TabPanelProps) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`profile-tabpanel-${index}`}
      aria-labelledby={`profile-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `profile-tab-${index}`,
    'aria-controls': `profile-tabpanel-${index}`,
  };
}

const ProfileSettingsPage: React.FC = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const { user } = useSelector((state: RootState) => state.auth);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (!user) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Please log in to access your profile settings.
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 4, fontWeight: 600 }}>
        Profile Settings
      </Typography>

      {/* Profile Header */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 3,
          background: theme.palette.background.paper,
          borderRadius: 2,
        }}
      >
        <Grid container spacing={3} alignItems="center">
          <Grid>
            <Avatar
              sx={{
                width: 80,
                height: 80,
                bgcolor: theme.palette.primary.main,
                fontSize: '2rem',
              }}
              src={user.profile_picture_url}
            >
              {user.username.charAt(0).toUpperCase()}
            </Avatar>
          </Grid>
          <Grid sx={{ flex: 1 }}>
            <Typography variant="h5" gutterBottom>
              {user.first_name && user.last_name
                ? `${user.first_name} ${user.last_name}`
                : user.username}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {user.email}
            </Typography>
            {user.bio && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {user.bio}
              </Typography>
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* Settings Tabs */}
      <Paper
        elevation={1}
        sx={{
          background: theme.palette.background.paper,
          borderRadius: 2,
        }}
      >
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="profile settings tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="Profile" {...a11yProps(0)} />
            <Tab label="Security" {...a11yProps(1)} />
            <Tab label="Notifications" {...a11yProps(2)} />
            <Tab label="Account" {...a11yProps(3)} />
          </Tabs>
        </Box>

        <Box sx={{ p: 3 }}>
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={4}>
              <Grid size={{ xs: 12, md: 8 }}>
                <ProfileForm />
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <ProfilePictureUpload />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={4}>
              <Grid size={{ xs: 12, md: 8 }}>
                <PasswordChangeForm />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <NotificationSettings />
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <AccountDeletion />
          </TabPanel>
        </Box>
      </Paper>
    </Container>
  );
};

export default ProfileSettingsPage;
