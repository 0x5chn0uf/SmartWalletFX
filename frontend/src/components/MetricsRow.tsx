import React, { useState } from 'react';
import { Box, Typography, Button } from '@mui/material';

interface MetricsRowProps {
  apy: number;
  apyProjected: number;
  apyRealized: number;
  netDeposits: number;
  netWithdrawals: number;
  net: number;
}

const MetricsRow: React.FC<MetricsRowProps> = ({
  apy,
  apyProjected,
  apyRealized,
  netDeposits,
  netWithdrawals,
  net,
}) => {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleExpand = (sectionId: string) => {
    setExpandedSection(expandedSection === sectionId ? null : sectionId);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        gap: 3,
        mb: 3,
        flexWrap: 'wrap',
      }}
    >
      {/* APY Card */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #242937 0%, #2d3548 100%)',
          borderRadius: 2,
          p: 3,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          minWidth: 280,
          flex: '1 1 350px',
          transition: 'all 0.3s ease',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          position: 'relative',
          overflow: 'hidden',
          animation: 'fadeInUp 0.8s ease-out',
          '@keyframes fadeInUp': {
            from: { opacity: 0, transform: 'translateY(30px)' },
            to: { opacity: 1, transform: 'translateY(0)' },
          },
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: 'linear-gradient(90deg, #4fd1c7, #6366f1)',
            borderRadius: 'inherit',
          },
          '&:hover': {
            transform: 'translateY(-8px)',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
          },
        }}
      >
        <Typography
          sx={{
            color: '#9ca3af',
            fontSize: '0.9rem',
            fontWeight: 500,
            mb: 1,
          }}
        >
          Average APY
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 1.5,
            mb: 1,
          }}
        >
          <Typography
            sx={{
              fontSize: '2rem',
              fontWeight: 700,
              color: '#4fd1c7',
              animation: 'countUp 0.8s ease-out 0.4s both',
              '@keyframes countUp': {
                from: { opacity: 0, transform: 'scale(0.8)' },
                to: { opacity: 1, transform: 'scale(1)' },
              },
            }}
          >
            {apy}%
          </Typography>
          <Typography
            sx={{
              color: '#9ca3af',
              fontSize: '1.1rem',
              fontWeight: 500,
            }}
          >
            (${apyProjected.toLocaleString()} projected)
          </Typography>
        </Box>
        <Box
          sx={{
            width: '100%',
            height: '1px',
            background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
            border: 'none',
            margin: '1.5rem 0',
          }}
        />
        <Typography
          sx={{
            color: '#9ca3af',
            fontSize: '1.2rem',
            fontWeight: 600,
            mb: 1.5,
          }}
        >
          Realized vs Projected Yield
        </Typography>
        <Box
          sx={{
            display: 'flex',
            gap: 3,
            alignItems: 'flex-end',
            mt: 1.5,
          }}
        >
          <Box
            sx={{
              width: 70,
              height: 90,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-end',
              borderRadius: '0.5rem 0.5rem 0 0',
              color: '#fff',
              fontWeight: 600,
              fontSize: '1rem',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              padding: '1rem 0.5rem',
              transition: 'all 0.4s ease',
              cursor: 'pointer',
              position: 'relative',
              overflow: 'hidden',
              background: 'linear-gradient(135deg, #10b981 0%, #4fd1c7 100%)',
              animation: 'slideInLeft 0.8s ease-out',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.2) 0%, transparent 50%)',
                opacity: 0,
                transition: 'opacity 0.3s ease',
              },
              '&:hover': {
                transform: 'scale(1.05) translateY(-5px)',
                filter: 'brightness(1.2)',
                '&::before': {
                  opacity: 1,
                },
              },
              '@keyframes slideInLeft': {
                from: { opacity: 0, transform: 'translateX(-30px)' },
                to: { opacity: 1, transform: 'translateX(0)' },
              },
            }}
          >
            ${apyRealized.toLocaleString()}
            <Box
              sx={{
                mt: 1,
                color: '#fff',
                fontSize: '0.9rem',
                fontWeight: 700,
                textShadow: '0 2px 8px #1a1f2e',
              }}
            >
              Realized
            </Box>
          </Box>
          <Box
            sx={{
              width: 70,
              height: 130,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-end',
              borderRadius: '0.5rem 0.5rem 0 0',
              color: '#fff',
              fontWeight: 600,
              fontSize: '1rem',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              padding: '1rem 0.5rem',
              transition: 'all 0.4s ease',
              cursor: 'pointer',
              position: 'relative',
              overflow: 'hidden',
              background: 'linear-gradient(135deg, #6366f1 0%, #4fd1c7 100%)',
              animation: 'slideInLeft 0.8s ease-out 0.2s both',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.2) 0%, transparent 50%)',
                opacity: 0,
                transition: 'opacity 0.3s ease',
              },
              '&:hover': {
                transform: 'scale(1.05) translateY(-5px)',
                filter: 'brightness(1.2)',
                '&::before': {
                  opacity: 1,
                },
              },
            }}
          >
            ${apyProjected.toLocaleString()}
            <Box
              sx={{
                mt: 1,
                color: '#fff',
                fontSize: '0.9rem',
                fontWeight: 700,
                textShadow: '0 2px 8px #1a1f2e',
              }}
            >
              Projected
            </Box>
          </Box>
        </Box>
        <Button
          onClick={() => toggleExpand('apyCard')}
          sx={{
            background: 'none',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '0.5rem',
            color: '#4fd1c7',
            padding: '0.5rem 1rem',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            mt: 1,
            '&:hover': {
              background: 'rgba(79, 209, 199, 0.1)',
              transform: 'translateY(-2px)',
            },
          }}
        >
          {expandedSection === 'apyCard' ? 'Show Less' : 'Show Details'}
        </Button>
      </Box>

      {/* Net Deposits/Withdrawals */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #242937 0%, #2d3548 100%)',
          borderRadius: 2,
          p: 3,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          minWidth: 280,
          flex: '1 1 350px',
          transition: 'all 0.3s ease',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          position: 'relative',
          overflow: 'hidden',
          animation: 'fadeInUp 0.8s ease-out 0.2s both',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: 'linear-gradient(90deg, #4fd1c7, #6366f1)',
            borderRadius: 'inherit',
          },
          '&:hover': {
            transform: 'translateY(-8px)',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
          },
        }}
      >
        <Typography
          sx={{
            color: '#9ca3af',
            fontSize: '1.2rem',
            fontWeight: 600,
            mb: 1.5,
          }}
        >
          Net Deposits vs Net Withdrawals
        </Typography>
        <Typography
          sx={{
            fontSize: '1.4rem',
            fontWeight: 700,
            color: '#10b981',
            display: 'block',
            mb: 1,
            animation: 'countUp 0.8s ease-out 0.5s both',
          }}
        >
          Net: ${net.toLocaleString()}
        </Typography>
        <Box
          sx={{
            display: 'flex',
            gap: 3,
            alignItems: 'flex-end',
            mt: 1.5,
          }}
        >
          <Box
            sx={{
              width: 70,
              height: 130,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-end',
              borderRadius: '0.5rem 0.5rem 0 0',
              color: '#fff',
              fontWeight: 600,
              fontSize: '1rem',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              padding: '1rem 0.5rem',
              transition: 'all 0.4s ease',
              cursor: 'pointer',
              position: 'relative',
              overflow: 'hidden',
              background: 'linear-gradient(135deg, #4fd1c7 0%, #3b82f6 100%)',
              animation: 'slideInLeft 0.8s ease-out 0.1s both',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.2) 0%, transparent 50%)',
                opacity: 0,
                transition: 'opacity 0.3s ease',
              },
              '&:hover': {
                transform: 'scale(1.05) translateY(-5px)',
                filter: 'brightness(1.2)',
                '&::before': {
                  opacity: 1,
                },
              },
            }}
          >
            ${netDeposits / 1000}k
            <Box
              sx={{
                mt: 1,
                color: '#fff',
                fontSize: '0.9rem',
                fontWeight: 700,
                textShadow: '0 2px 8px #1a1f2e',
              }}
            >
              Deposits
            </Box>
          </Box>
          <Box
            sx={{
              width: 70,
              height: 70,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-end',
              borderRadius: '0.5rem 0.5rem 0 0',
              color: '#fff',
              fontWeight: 600,
              fontSize: '1rem',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              padding: '1rem 0.5rem',
              transition: 'all 0.4s ease',
              cursor: 'pointer',
              position: 'relative',
              overflow: 'hidden',
              background: 'linear-gradient(135deg, #ef4444 0%, #f59e0b 100%)',
              animation: 'slideInLeft 0.8s ease-out 0.3s both',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.2) 0%, transparent 50%)',
                opacity: 0,
                transition: 'opacity 0.3s ease',
              },
              '&:hover': {
                transform: 'scale(1.05) translateY(-5px)',
                filter: 'brightness(1.2)',
                '&::before': {
                  opacity: 1,
                },
              },
            }}
          >
            ${netWithdrawals / 1000}k
            <Box
              sx={{
                mt: 1,
                color: '#fff',
                fontSize: '0.9rem',
                fontWeight: 700,
                textShadow: '0 2px 8px #1a1f2e',
              }}
            >
              Withdrawals
            </Box>
          </Box>
        </Box>
        <Button
          onClick={() => toggleExpand('netCard')}
          sx={{
            background: 'none',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '0.5rem',
            color: '#4fd1c7',
            padding: '0.5rem 1rem',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            mt: 1,
            '&:hover': {
              background: 'rgba(79, 209, 199, 0.1)',
              transform: 'translateY(-2px)',
            },
          }}
        >
          {expandedSection === 'netCard' ? 'Show Less' : 'Show History'}
        </Button>
      </Box>
    </Box>
  );
};

export default MetricsRow;