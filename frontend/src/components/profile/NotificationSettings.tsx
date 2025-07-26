import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  FormControlLabel,
  Switch,
  Alert,
  Button,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  Grid,
} from '@mui/material';
import {
  Notifications,
  Security,
  TrendingUp,
  PriceChange,
  Email,
  Smartphone,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { updateNotificationPreferences } from '../../store/slices/userProfileSlice';
import { NotificationPreferences } from '../../schemas/api';

interface NotificationOption {
  key: keyof NotificationPreferences;
  label: string;
  description: string;
  icon: React.ReactNode;
  critical?: boolean;
}

const NOTIFICATION_OPTIONS: NotificationOption[] = [
  {
    key: 'email_notifications',
    label: 'Email Notifications',
    description: 'Receive general notifications via email',
    icon: <Email />,
  },
  {
    key: 'security_alerts',
    label: 'Security Alerts',
    description: 'Important security notifications (login attempts, password changes)',
    icon: <Security />,
    critical: true,
  },
  {
    key: 'portfolio_updates',
    label: 'Portfolio Updates',
    description: 'Daily and weekly portfolio performance summaries',
    icon: <TrendingUp />,
  },
  {
    key: 'price_alerts',
    label: 'Price Alerts',
    description: 'Notifications when assets reach target prices or thresholds',
    icon: <PriceChange />,
  },
];

const NotificationSettings: React.FC = () => {
  const dispatch = useDispatch<any>();
  const { user } = useSelector((state: RootState) => state.auth);
  const { loading, error, success } = useSelector((state: RootState) => state.userProfile || {});

  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_notifications: true,
    security_alerts: true,
    portfolio_updates: true,
    price_alerts: true,
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Initialize preferences from user data
  useEffect(() => {
    if (user?.notification_preferences) {
      const userPrefs = user.notification_preferences as NotificationPreferences;
      setPreferences({
        email_notifications: userPrefs.email_notifications ?? true,
        security_alerts: userPrefs.security_alerts ?? true,
        portfolio_updates: userPrefs.portfolio_updates ?? true,
        price_alerts: userPrefs.price_alerts ?? true,
      });
      setHasChanges(false); // Reset changes when data is loaded
    }
  }, [user]);

  const handleToggle =
    (key: keyof NotificationPreferences) => (event: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = event.target.checked;

      const newPreferences = {
        ...preferences,
        [key]: newValue,
      };

      setPreferences(newPreferences);

      // Check if preferences differ from original user preferences
      const originalPrefs = user?.notification_preferences as NotificationPreferences;
      const hasActualChanges = originalPrefs ? 
        Object.keys(newPreferences).some(prefKey => {
          const key = prefKey as keyof NotificationPreferences;
          return newPreferences[key] !== (originalPrefs[key] ?? true);
        }) : true;

      setHasChanges(hasActualChanges);
    };

  const handleSave = async () => {
    await dispatch(updateNotificationPreferences(preferences));
    if (!error) {
      setHasChanges(false);
    }
  };

  const handleReset = () => {
    if (user?.notification_preferences) {
      const userPrefs = user.notification_preferences as NotificationPreferences;
      setPreferences({
        email_notifications: userPrefs.email_notifications ?? true,
        security_alerts: userPrefs.security_alerts ?? true,
        portfolio_updates: userPrefs.portfolio_updates ?? true,
        price_alerts: userPrefs.price_alerts ?? true,
      });
    }
    setHasChanges(false);
  };

  if (!user) {
    return (
      <Typography variant="body1" color="textSecondary">
        Please log in to manage your notification preferences.
      </Typography>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Notifications sx={{ mr: 2, color: 'text.secondary' }} />
        <Typography variant="h6">Notification Preferences</Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Notification preferences updated successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        {NOTIFICATION_OPTIONS.map(option => (
          <Grid item xs={12} key={option.key}>
            <Card
              variant="outlined"
              sx={{
                transition: 'all 0.2s',
                '&:hover': {
                  boxShadow: 1,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Box
                    sx={{
                      color: option.critical ? 'error.main' : 'primary.main',
                      mt: 0.5,
                    }}
                  >
                    {option.icon}
                  </Box>

                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1" sx={{ flex: 1 }}>
                        {option.label}
                      </Typography>
                      {option.critical && (
                        <Typography
                          variant="caption"
                          sx={{
                            color: 'error.main',
                            bgcolor: 'error.light',
                            px: 1,
                            py: 0.25,
                            borderRadius: 1,
                            fontSize: '0.65rem',
                            fontWeight: 600,
                          }}
                        >
                          CRITICAL
                        </Typography>
                      )}
                    </Box>

                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                      {option.description}
                    </Typography>
                  </Box>

                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences[option.key] || false}
                        onChange={handleToggle(option.key)}
                        disabled={loading}
                        color={option.critical ? 'error' : 'primary'}
                      />
                    }
                    label=""
                    sx={{ ml: 0 }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Information Cards */}
      <Box sx={{ mt: 4 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Email Delivery:</strong> Notifications are sent to {user.email}. Update your
            email address in the Profile tab if needed.
          </Typography>
        </Alert>

        <Alert severity="warning">
          <Typography variant="body2">
            <strong>Security Alerts:</strong> We strongly recommend keeping security alerts enabled
            to protect your account from unauthorized access attempts.
          </Typography>
        </Alert>
      </Box>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2, pt: 3, mt: 3, borderTop: 1, borderColor: 'divider' }}>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={loading || !hasChanges}
          startIcon={loading ? <CircularProgress size={20} /> : <Notifications />}
        >
          {loading ? 'Saving...' : 'Save Preferences'}
        </Button>

        <Button variant="outlined" onClick={handleReset} disabled={loading || !hasChanges}>
          Reset Changes
        </Button>
      </Box>

      {/* Future Enhancement Notice */}
      <Box
        sx={{
          mt: 4,
          p: 2,
          bgcolor: 'background.paper',
          borderRadius: 1,
          border: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <Smartphone sx={{ mr: 1, fontSize: '1.2rem' }} />
          Coming Soon
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Push notifications, SMS alerts, and in-app notification preferences will be available in a
          future update.
        </Typography>
      </Box>
    </Box>
  );
};

export default NotificationSettings;
