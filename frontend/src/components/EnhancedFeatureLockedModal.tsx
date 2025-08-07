import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Modal from '@mui/material/Modal';

interface EnhancedFeatureLockedModalProps {
  open: boolean;
  onClose: () => void;
  onStartTrial?: () => void;
}

const EnhancedFeatureLockedModal: React.FC<EnhancedFeatureLockedModalProps> = ({
  open,
  onClose,
  onStartTrial,
}) => {
  const handleStartTrial = () => {
    onStartTrial?.();
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backdropFilter: 'blur(10px)',
        backgroundColor: 'rgba(26, 31, 46, 0.9)',
      }}
    >
      <Box
        sx={{
          background: 'var(--color-surface)',
          borderRadius: 2,
          p: 4,
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          maxWidth: 400,
          width: '90%',
          textAlign: 'center',
          transform: open ? 'scale(1) translateY(0)' : 'scale(0.9) translateY(20px)',
          transition: 'all 0.3s ease',
          animation: open ? 'modalSlideIn 0.3s ease-out' : 'none',
          '@keyframes modalSlideIn': {
            '0%': {
              opacity: 0,
              transform: 'scale(0.9) translateY(20px)',
            },
            '100%': {
              opacity: 1,
              transform: 'scale(1) translateY(0)',
            },
          },
        }}
      >
        <Typography
          component="h2"
          sx={{
            color: 'var(--text-primary)',
            mb: 2,
            fontSize: '1.5rem',
            fontWeight: 700,
          }}
        >
          🚀 Unlock Full Access
        </Typography>
        <Typography
          sx={{
            color: 'var(--text-secondary)',
            mb: 3,
            lineHeight: 1.5,
          }}
        >
          Get complete portfolio insights, extended historical data, and advanced analytics.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            onClick={handleStartTrial}
            sx={{
              background: 'linear-gradient(135deg, var(--color-primary), var(--accent-secondary))',
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
              color: 'var(--text-secondary)',
              padding: '0.75rem 1.5rem',
              borderRadius: '0.5rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'rgba(255, 255, 255, 0.05)',
              },
            }}
          >
            Maybe Later
          </Button>
        </Box>
      </Box>
    </Modal>
  );
};

export default EnhancedFeatureLockedModal;