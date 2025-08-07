import React, { useState } from 'react';
import Fab from '@mui/material/Fab';
import Box from '@mui/material/Box';

interface FloatingActionButtonProps {
  onRefresh?: () => void;
}

const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({ onRefresh }) => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    onRefresh?.();
    
    // Reset after animation
    setTimeout(() => {
      setIsRefreshing(false);
    }, 1000);
  };

  return (
    <Fab
      onClick={handleRefresh}
      sx={{
        position: 'fixed',
        bottom: '2rem',
        right: '2rem',
        width: 60,
        height: 60,
        borderRadius: '50%',
        background: 'linear-gradient(135deg, var(--color-primary), var(--accent-secondary))',
        border: 'none',
        cursor: 'pointer',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
        color: 'white',
        fontSize: '1.5rem',
        transition: 'all 0.3s ease',
        zIndex: 1000,
        animation: 'glow 3s ease-in-out infinite',
        transform: isRefreshing ? 'scale(0.8) rotate(360deg)' : 'scale(1)',
        '@keyframes glow': {
          '0%, 100%': {
            boxShadow: '0 0 20px rgba(79, 209, 199, 0.3)',
          },
          '50%': {
            boxShadow: '0 0 30px rgba(79, 209, 199, 0.6)',
          },
        },
        '&:hover': {
          transform: isRefreshing ? 'scale(0.8) rotate(360deg)' : 'scale(1.1) rotate(15deg)',
        },
      }}
    >
      <Box component="span" sx={{ fontSize: '1.5rem' }}>
        ⟳
      </Box>
    </Fab>
  );
};

export default FloatingActionButton;