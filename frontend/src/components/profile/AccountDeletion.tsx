import React, { useState } from 'react';
import {
  Box,
  Typography,
  Alert,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import { Warning, Delete, AccountCircle, Storage, Timeline, Security } from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store';
import { deleteAccount } from '../../store/slices/userProfileSlice';

const DELETION_CONSEQUENCES = [
  {
    icon: <AccountCircle />,
    text: 'Your profile and personal information will be permanently deleted',
  },
  {
    icon: <Storage />,
    text: 'All wallet data, transactions, and portfolio history will be removed',
  },
  {
    icon: <Timeline />,
    text: 'Historical performance data and analytics will be lost',
  },
  {
    icon: <Security />,
    text: 'All API keys and connected services will be disconnected',
  },
];

const AccountDeletion: React.FC = () => {
  const dispatch = useDispatch<any>();
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const { loading, error } = useSelector((state: RootState) => state.userProfile || {});

  const [showDialog, setShowDialog] = useState(false);
  const [confirmationText, setConfirmationText] = useState('');
  const [acknowledgedConsequences, setAcknowledgedConsequences] = useState(false);
  const [confirmPassword, setConfirmPassword] = useState('');

  const expectedConfirmation = 'DELETE MY ACCOUNT';
  const isConfirmationValid = confirmationText === expectedConfirmation;

  const handleOpenDialog = () => {
    setShowDialog(true);
    setConfirmationText('');
    setAcknowledgedConsequences(false);
    setConfirmPassword('');
  };

  const handleCloseDialog = () => {
    setShowDialog(false);
    setConfirmationText('');
    setAcknowledgedConsequences(false);
    setConfirmPassword('');
  };

  const handleDeleteAccount = async () => {
    if (!isConfirmationValid || !acknowledgedConsequences || !confirmPassword) {
      return;
    }

    try {
      await dispatch(deleteAccount({ password: confirmPassword }));
      // If successful, redirect to home page
      navigate('/');
    } catch (err) {
      // Error handling is managed by the Redux slice
      console.error('Account deletion failed:', err);
    }
  };

  if (!user) {
    return (
      <Typography variant="body1" color="textSecondary">
        Please log in to manage your account.
      </Typography>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, color: 'error.main' }}>
        <Warning sx={{ mr: 2 }} />
        <Typography variant="h6">Delete Account</Typography>
      </Box>

      <Alert severity="error" sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Danger Zone
        </Typography>
        <Typography variant="body2">
          Once you delete your account, there is no going back. Please be certain about this action.
        </Typography>
      </Alert>

      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          What happens when you delete your account:
        </Typography>

        <List dense>
          {DELETION_CONSEQUENCES.map((consequence, index) => (
            <ListItem key={index} sx={{ py: 1 }}>
              <ListItemIcon sx={{ color: 'error.main', minWidth: 40 }}>
                {consequence.icon}
              </ListItemIcon>
              <ListItemText
                primary={consequence.text}
                primaryTypographyProps={{ variant: 'body2' }}
              />
            </ListItem>
          ))}
        </List>
      </Box>

      <Box
        sx={{
          mb: 4,
          p: 3,
          bgcolor: 'warning.light',
          borderRadius: 2,
          border: 1,
          borderColor: 'warning.main',
        }}
      >
        <Typography
          variant="subtitle2"
          gutterBottom
          sx={{ color: 'warning.contrastText', fontWeight: 600 }}
        >
          Before you proceed:
        </Typography>
        <Typography variant="body2" sx={{ color: 'warning.contrastText' }}>
          • Consider exporting your data if you need it for records
          <br />
          • Remove any active subscriptions or services
          <br />
          • Update any external services that depend on this account
          <br />• This action cannot be undone - there is no account recovery option
        </Typography>
      </Box>

      <Box>
        <Button
          variant="contained"
          color="error"
          size="large"
          startIcon={<Delete />}
          onClick={handleOpenDialog}
          sx={{
            fontWeight: 600,
            '&:hover': {
              bgcolor: 'error.dark',
            },
          }}
        >
          Delete My Account
        </Button>
      </Box>

      {/* Confirmation Dialog */}
      <Dialog
        open={showDialog}
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 2 },
        }}
      >
        <DialogTitle sx={{ color: 'error.main', fontWeight: 600 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Warning sx={{ mr: 2 }} />
            Confirm Account Deletion
          </Box>
        </DialogTitle>

        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Typography variant="body1" sx={{ mb: 3 }}>
            You are about to permanently delete the account for <strong>{user.email}</strong>.
          </Typography>

          <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
            Type <strong>{expectedConfirmation}</strong> below to confirm:
          </Typography>

          <TextField
            fullWidth
            label="Confirmation Text"
            value={confirmationText}
            onChange={e => setConfirmationText(e.target.value)}
            error={confirmationText.length > 0 && !isConfirmationValid}
            helperText={
              confirmationText.length > 0 && !isConfirmationValid
                ? `Must type exactly: ${expectedConfirmation}`
                : ''
            }
            sx={{ mb: 3 }}
            disabled={loading}
          />

          <TextField
            fullWidth
            type="password"
            label="Confirm Password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            helperText="Enter your current password to confirm"
            sx={{ mb: 3 }}
            disabled={loading}
            required
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={acknowledgedConsequences}
                onChange={e => setAcknowledgedConsequences(e.target.checked)}
                disabled={loading}
                color="error"
              />
            }
            label={
              <Typography variant="body2">
                I understand that this action is permanent and cannot be undone
              </Typography>
            }
            sx={{ mb: 2 }}
          />
        </DialogContent>

        <DialogActions sx={{ p: 3, pt: 0 }}>
          <Button onClick={handleCloseDialog} disabled={loading} variant="outlined">
            Cancel
          </Button>
          <Button
            onClick={handleDeleteAccount}
            color="error"
            variant="contained"
            disabled={
              loading || !isConfirmationValid || !acknowledgedConsequences || !confirmPassword
            }
            startIcon={loading ? <CircularProgress size={20} /> : <Delete />}
          >
            {loading ? 'Deleting...' : 'Delete Account'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AccountDeletion;
