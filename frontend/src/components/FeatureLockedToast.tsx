import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

interface FeatureLockedToastProps {
  show: boolean;
  onClose: () => void;
  message?: string;
}

const FeatureLockedToast: React.FC<FeatureLockedToastProps> = ({
  show,
  onClose,
  message = 'Register to unlock extended historical data',
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (show) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        setTimeout(() => onClose(), 300); // Wait for animation to complete
      }, 3000);

      return () => clearTimeout(timer);
    } else {
      setVisible(false);
    }
  }, [show, onClose]);

  if (!show && !visible) return null;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: '2rem',
        right: '2rem',
        background: 'var(--color-surface)',
        border: '1px solid rgba(255, 184, 0, 0.3)',
        borderRadius: '0.5rem',
        padding: '1rem',
        color: 'var(--text-primary)',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        zIndex: 10000,
        maxWidth: '300px',
        transform: visible ? 'translateX(0)' : 'translateX(100%)',
        opacity: visible ? 1 : 0,
        transition: 'all 0.3s ease',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          mb: 0.5,
        }}
      >
        <span>🔒</span>
        <Typography
          sx={{
            fontWeight: 600,
            color: 'var(--text-primary)',
          }}
        >
          Feature Locked
        </Typography>
      </Box>
      <Typography
        component="p"
        sx={{
          fontSize: '0.9rem',
          color: 'var(--text-secondary)',
          margin: 0,
        }}
      >
        {message}
      </Typography>
    </Box>
  );
};

export default FeatureLockedToast;