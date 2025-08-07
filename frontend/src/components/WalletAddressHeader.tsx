import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';

interface WalletAddressHeaderProps {
  address: string;
  isPreviewMode?: boolean;
}

const WalletAddressHeader: React.FC<WalletAddressHeaderProps> = ({
  address,
  isPreviewMode = true,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy address:', err);
    }
  };

  return (
    <Box
      sx={{
        background: 'var(--color-surface)',
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
          background: 'linear-gradient(90deg, var(--color-primary), var(--accent-secondary))',
        },
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography
            component="span"
            sx={{
              fontFamily: '"SF Mono", Monaco, "Cascadia Code", monospace',
              color: 'var(--color-primary)',
              fontSize: '0.9rem',
              fontWeight: 600,
              background: 'rgba(79, 209, 199, 0.1)',
              padding: '0.4rem 0.8rem',
              borderRadius: '0.4rem',
              border: '1px solid rgba(79, 209, 199, 0.2)',
            }}
          >
            {address}
          </Typography>
          <Button
            onClick={handleCopy}
            sx={{
              background: 'transparent',
              border: '1px solid rgba(79, 209, 199, 0.3)',
              color: copied ? 'var(--success)' : 'var(--color-primary)',
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              fontSize: '0.85rem',
              fontWeight: 500,
              minWidth: 'auto',
              '&:hover': {
                background: 'rgba(79, 209, 199, 0.1)',
                transform: 'translateY(-1px)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            {copied ? 'Copied!' : 'Copy'}
          </Button>
        </Box>
        {isPreviewMode && (
          <Chip
            label="PREVIEW MODE"
            sx={{
              background: 'linear-gradient(135deg, var(--color-primary), var(--accent-secondary))',
              color: 'white',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            }}
          />
        )}
      </Box>
      {isPreviewMode && (
        <Typography
          sx={{
            color: 'var(--text-secondary)',
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

export default WalletAddressHeader;