import React from 'react';
import { Dialog, DialogContent, Typography, Button, Box } from '@mui/material';

interface FeatureLockedModalProps {
  open: boolean;
  onClose: () => void;
  onStartTrial: () => void;
}

const FeatureLockedModal: React.FC<FeatureLockedModalProps> = ({
  open,
  onClose,
  onStartTrial,
}) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          background: '#242937',
          borderRadius: 2,
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
          maxWidth: 400,
          width: '90%',
          textAlign: 'center',
        },
      }}
      BackdropProps={{
        sx: {
          backgroundColor: 'rgba(26, 31, 46, 0.9)',
          backdropFilter: 'blur(10px)',
        },
      }}
    >
      <DialogContent sx={{ p: 3 }}>
        <Typography
          sx={{
            color: '#ffffff',
            mb: 1.5,
            fontSize: '1.5rem',
            fontWeight: 700,
          }}
        >
          🚀 Unlock Full Access
        </Typography>
        <Typography
          sx={{
            color: '#9ca3af',
            mb: 2,
            lineHeight: 1.5,
          }}
        >
          Get complete portfolio insights, extended historical data, and advanced analytics.
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button
            onClick={onStartTrial}
            sx={{
              background: 'linear-gradient(135deg, #4fd1c7, #6366f1)',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '0.5rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              },
            }}
          >
            Create an Account
          </Button>
          <Button
            onClick={onClose}
            sx={{
              background: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#9ca3af',
              padding: '0.75rem 1.5rem',
              borderRadius: '0.5rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'rgba(255, 255, 255, 0.05)',
                transform: 'translateY(-2px)',
              },
            }}
          >
            Maybe Later
          </Button>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default FeatureLockedModal;