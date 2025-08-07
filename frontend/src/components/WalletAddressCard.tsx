import React from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import useNotification from '../hooks/useNotification';

interface WalletAddressCardProps {
  address: string;
  isPreviewMode?: boolean;
}

const WalletAddressCard: React.FC<WalletAddressCardProps> = ({
  address,
  isPreviewMode = true,
}) => {
  const { showSuccess, showError } = useNotification();

  const handleCopyAddress = async () => {
    try {
      await navigator.clipboard.writeText(address);
      showSuccess('Address copied to clipboard!');
    } catch (err) {
      showError('Failed to copy address');
    }
  };

  return (
    <Box
      sx={{
        background: 'linear-gradient(135deg, #242937 0%, #2d3548 100%)',
        borderRadius: 2,
        p: 3,
        mb: 3,
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: 'linear-gradient(90deg, #4fd1c7, #6366f1)',
        },
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              fontFamily: '"SF Mono", Monaco, "Cascadia Code", monospace',
              color: '#4fd1c7',
              fontSize: '1rem',
              fontWeight: 600,
              background: 'rgba(79, 209, 199, 0.1)',
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              border: '1px solid rgba(79, 209, 199, 0.2)',
            }}
          >
            {address}
          </Box>
          <IconButton
            onClick={handleCopyAddress}
            sx={{
              border: '1px solid rgba(79, 209, 199, 0.3)',
              color: '#4fd1c7',
              padding: '0.5rem',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'rgba(79, 209, 199, 0.1)',
                transform: 'translateY(-1px)',
              },
            }}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Box>
        {isPreviewMode && (
          <Box
            sx={{
              background: 'linear-gradient(135deg, #4fd1c7, #6366f1)',
              color: 'white',
              padding: '0.5rem 1.5rem',
              borderRadius: '2rem',
              fontSize: '0.85rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%, 100%': { opacity: 1 },
                '50%': { opacity: 0.7 },
              },
            }}
          >
            PREVIEW MODE
          </Box>
        )}
      </Box>
      {isPreviewMode && (
        <Typography
          sx={{
            color: '#9ca3af',
            fontSize: '1rem',
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          You're viewing a limited preview. Sign up to unlock complete portfolio history, detailed
          analytics, and all positions.
        </Typography>
      )}
    </Box>
  );
};

export default WalletAddressCard;