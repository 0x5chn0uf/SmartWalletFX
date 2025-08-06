import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Grid,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  LinearProgress,
} from '@mui/material';
import { Visibility, VisibilityOff, Lock } from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { changePassword } from '../../store/slices/userProfileSlice';
import { PasswordChange, PasswordChangeSchema } from '../../schemas/api';

// Password strength validation
const getPasswordStrength = (password: string): { score: number; feedback: string[] } => {
  const feedback: string[] = [];
  let score = 0;

  if (password.length >= 8) {
    score += 20;
  } else {
    feedback.push('At least 8 characters');
  }

  if (password.length >= 12) {
    score += 10;
  }

  if (/[a-z]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include lowercase letters');
  }

  if (/[A-Z]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include uppercase letters');
  }

  if (/\d/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include numbers');
  }

  if (/[^a-zA-Z0-9]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include special characters');
  }

  if (password.length >= 16) {
    score += 10;
  }

  return { score: Math.min(score, 100), feedback };
};

const getStrengthColor = (score: number): string => {
  if (score < 40) return '#f44336'; // red
  if (score < 70) return '#ff9800'; // orange
  if (score < 90) return '#2196f3'; // blue
  return '#4caf50'; // green
};

const getStrengthLabel = (score: number): string => {
  if (score < 40) return 'Weak';
  if (score < 70) return 'Medium';
  if (score < 90) return 'Strong';
  return 'Very Strong';
};

const PasswordChangeForm: React.FC = () => {
  const dispatch = useDispatch<any>();
  const { user } = useSelector((state: RootState) => state.auth);
  const { loading, error, success } = useSelector((state: RootState) => state.userProfile || {});

  const [formData, setFormData] = useState<PasswordChange>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [passwordStrength, setPasswordStrength] = useState({ score: 0, feedback: [] as string[] });

  const handleChange =
    (field: keyof PasswordChange) => (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      setFormData(prev => ({ ...prev, [field]: value }));

      // Clear validation error for this field
      if (validationErrors[field]) {
        setValidationErrors(prev => ({ ...prev, [field]: '' }));
      }

      // Update password strength for new password
      if (field === 'new_password') {
        setPasswordStrength(getPasswordStrength(value));
      }
    };

  const togglePasswordVisibility = (field: 'current' | 'new' | 'confirm') => {
    setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const validateForm = (): boolean => {
    try {
      PasswordChangeSchema.parse(formData);
      setValidationErrors({});
      return true;
    } catch (error: any) {
      const errors: Record<string, string> = {};
      if (error.issues) {
        error.issues.forEach((issue: any) => {
          const field = issue.path[0];
          errors[field] = issue.message;
        });
      }
      setValidationErrors(errors);
      return false;
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await dispatch(changePassword(formData));

      // Clear form on success
      if (!error) {
        setFormData({
          current_password: '',
          new_password: '',
          confirm_password: '',
        });
        setPasswordStrength({ score: 0, feedback: [] });
      }
    } catch (err) {
      // Error is handled by the Redux state
    }
  };

  if (!user) {
    return (
      <Typography variant="body1" color="textSecondary">
        Please log in to change your password.
      </Typography>
    );
  }

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Lock sx={{ mr: 2, color: 'text.secondary' }} />
        <Typography variant="h6">Change Password</Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Password changed successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid size={12}>
          <TextField
            fullWidth
            type={showPasswords.current ? 'text' : 'password'}
            label="Current Password"
            value={formData.current_password}
            onChange={handleChange('current_password')}
            error={!!validationErrors.current_password}
            helperText={validationErrors.current_password}
            disabled={loading}
            required
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => togglePasswordVisibility('current')}
                    edge="end"
                    aria-label="toggle current password visibility"
                  >
                    {showPasswords.current ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        <Grid size={12}>
          <TextField
            fullWidth
            type={showPasswords.new ? 'text' : 'password'}
            label="New Password"
            value={formData.new_password}
            onChange={handleChange('new_password')}
            error={!!validationErrors.new_password}
            helperText={validationErrors.new_password}
            disabled={loading}
            required
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => togglePasswordVisibility('new')}
                    edge="end"
                    aria-label="toggle new password visibility"
                  >
                    {showPasswords.new ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {formData.new_password && (
            <Box sx={{ mt: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ mr: 2 }}>
                  Strength: {getStrengthLabel(passwordStrength.score)}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={passwordStrength.score}
                  sx={{
                    flex: 1,
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: 'grey.300',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getStrengthColor(passwordStrength.score),
                      borderRadius: 3,
                    },
                  }}
                />
              </Box>
              {passwordStrength.feedback.length > 0 && (
                <Typography variant="caption" color="textSecondary">
                  Suggestions: {passwordStrength.feedback.join(', ')}
                </Typography>
              )}
            </Box>
          )}
        </Grid>

        <Grid size={12}>
          <TextField
            fullWidth
            type={showPasswords.confirm ? 'text' : 'password'}
            label="Confirm New Password"
            value={formData.confirm_password}
            onChange={handleChange('confirm_password')}
            error={!!validationErrors.confirm_password}
            helperText={validationErrors.confirm_password}
            disabled={loading}
            required
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => togglePasswordVisibility('confirm')}
                    edge="end"
                    aria-label="toggle confirm password visibility"
                  >
                    {showPasswords.confirm ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        <Grid size={12}>
          <Box sx={{ display: 'flex', gap: 2, pt: 2 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={loading || passwordStrength.score < 40}
              startIcon={loading ? <CircularProgress size={20} /> : <Lock />}
            >
              {loading ? 'Changing Password...' : 'Change Password'}
            </Button>

            <Button
              type="button"
              variant="outlined"
              disabled={loading}
              onClick={() => {
                setFormData({
                  current_password: '',
                  new_password: '',
                  confirm_password: '',
                });
                setPasswordStrength({ score: 0, feedback: [] });
                setValidationErrors({});
              }}
            >
              Clear
            </Button>
          </Box>
        </Grid>
      </Grid>

      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>Password Requirements:</strong>
          <br />
          • At least 8 characters long
          <br />
          • Include uppercase and lowercase letters
          <br />
          • Include numbers and special characters
          <br />• Avoid common passwords and personal information
        </Typography>
      </Alert>
    </Box>
  );
};

export default PasswordChangeForm;
