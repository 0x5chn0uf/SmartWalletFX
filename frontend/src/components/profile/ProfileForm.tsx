import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Grid,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { updateUserProfile } from '../../store/slices/userProfileSlice';
import { UserProfileUpdate } from '../../schemas/api';

// Common timezones list
const COMMON_TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Kolkata',
  'Australia/Sydney',
];

// Currency options
const CURRENCIES = [
  { value: 'USD', label: 'USD - US Dollar' },
  { value: 'EUR', label: 'EUR - Euro' },
  { value: 'GBP', label: 'GBP - British Pound' },
  { value: 'JPY', label: 'JPY - Japanese Yen' },
  { value: 'CAD', label: 'CAD - Canadian Dollar' },
  { value: 'AUD', label: 'AUD - Australian Dollar' },
  { value: 'CHF', label: 'CHF - Swiss Franc' },
  { value: 'CNY', label: 'CNY - Chinese Yuan' },
];

const ProfileForm: React.FC = () => {
  const dispatch = useDispatch<any>();
  const { user } = useSelector((state: RootState) => state.auth);
  const { loading, error, success } = useSelector((state: RootState) => state.userProfile || {});

  const [formData, setFormData] = useState<UserProfileUpdate>({
    first_name: '',
    last_name: '',
    bio: '',
    timezone: '',
    preferred_currency: 'USD',
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Initialize form with user data
  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        bio: user.bio || '',
        timezone: user.timezone || '',
        preferred_currency: user.preferred_currency || 'USD',
      });
    }
  }, [user]);

  const handleChange =
    (field: keyof UserProfileUpdate) => (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      setFormData(prev => ({ ...prev, [field]: value }));

      // Clear validation error for this field
      if (validationErrors[field]) {
        setValidationErrors(prev => ({ ...prev, [field]: '' }));
      }
    };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (formData.first_name && formData.first_name.length > 100) {
      errors.first_name = 'First name must be 100 characters or less';
    }

    if (formData.last_name && formData.last_name.length > 100) {
      errors.last_name = 'Last name must be 100 characters or less';
    }

    if (formData.bio && formData.bio.length > 1000) {
      errors.bio = 'Bio must be 1000 characters or less';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Filter out empty strings and undefined values
    const updateData: UserProfileUpdate = {};
    Object.entries(formData).forEach(([key, value]) => {
      if (value !== '' && value !== undefined) {
        updateData[key as keyof UserProfileUpdate] = value;
      }
    });

    await dispatch(updateUserProfile(updateData));
  };

  if (!user) {
    return (
      <Typography variant="body1" color="textSecondary">
        Please log in to edit your profile.
      </Typography>
    );
  }

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
        Personal Information
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Profile updated successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="First Name"
            value={formData.first_name}
            onChange={handleChange('first_name')}
            error={!!validationErrors.first_name}
            helperText={validationErrors.first_name}
            disabled={loading}
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="Last Name"
            value={formData.last_name}
            onChange={handleChange('last_name')}
            error={!!validationErrors.last_name}
            helperText={validationErrors.last_name}
            disabled={loading}
          />
        </Grid>

        <Grid size={12}>
          <TextField
            fullWidth
            label="Bio"
            multiline
            rows={4}
            value={formData.bio}
            onChange={handleChange('bio')}
            error={!!validationErrors.bio}
            helperText={validationErrors.bio || `${formData.bio?.length || 0}/1000 characters`}
            disabled={loading}
            placeholder="Tell us a bit about yourself..."
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            select
            label="Timezone"
            value={formData.timezone}
            onChange={handleChange('timezone')}
            disabled={loading}
            helperText="Select your preferred timezone"
          >
            <MenuItem value="">
              <em>None</em>
            </MenuItem>
            {COMMON_TIMEZONES.map(tz => (
              <MenuItem key={tz} value={tz}>
                {tz}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            select
            label="Preferred Currency"
            value={formData.preferred_currency}
            onChange={handleChange('preferred_currency')}
            disabled={loading}
            helperText="Currency for displaying portfolio values"
          >
            {CURRENCIES.map(currency => (
              <MenuItem key={currency.value} value={currency.value}>
                {currency.label}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid size={12}>
          <Box sx={{ display: 'flex', gap: 2, pt: 2 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : null}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>

            <Button
              type="button"
              variant="outlined"
              disabled={loading}
              onClick={() => {
                // Reset form to original user data
                if (user) {
                  setFormData({
                    first_name: user.first_name || '',
                    last_name: user.last_name || '',
                    bio: user.bio || '',
                    timezone: user.timezone || '',
                    preferred_currency: user.preferred_currency || 'USD',
                  });
                  setValidationErrors({});
                }
              }}
            >
              Reset
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProfileForm;
