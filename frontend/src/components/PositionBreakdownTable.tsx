import React from 'react';
import { Box, Typography } from '@mui/material';

interface PositionData {
  asset: string;
  protocol: string;
  value: number;
  apy: number;
  change?: number;
}

interface PositionBreakdownTableProps {
  positions: PositionData[];
}

const PositionBreakdownTable: React.FC<PositionBreakdownTableProps> = ({ positions }) => {
  return (
    <Box
      sx={{
        background: 'linear-gradient(135deg, #242937 0%, #2d3548 100%)',
        borderRadius: 2,
        p: 3,
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        transition: 'all 0.3s ease',
        animation: 'fadeInUp 0.8s ease-out 0.6s both',
        position: 'relative',
        overflow: 'hidden',
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
          background: 'linear-gradient(90deg, #4fd1c7, #10b981)',
        },
        '&:hover': {
          transform: 'translateY(-5px)',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
        },
      }}
    >
      <Typography
        sx={{
          fontSize: '1.5rem',
          fontWeight: 700,
          color: 'transparent',
          background: 'linear-gradient(135deg, #ffffff 0%, #9ca3af 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          position: 'relative',
          mb: 2,
          '&::after': {
            content: '""',
            position: 'absolute',
            bottom: '-4px',
            left: 0,
            width: '40px',
            height: '2px',
            background: 'linear-gradient(90deg, #4fd1c7, #10b981)',
            borderRadius: '1px',
          },
        }}
      >
        Position Breakdown
      </Typography>
      <Box
        component="table"
        sx={{
          width: '100%',
          borderCollapse: 'collapse',
          '& th, & td': {
            padding: '1rem 0.75rem',
            textAlign: 'left',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            transition: 'all 0.3s ease',
          },
          '& th': {
            color: '#9ca3af',
            fontWeight: 600,
            background: 'rgba(79, 209, 199, 0.05)',
            fontSize: '0.9rem',
          },
          '& tbody tr': {
            transition: 'all 0.3s ease',
            '&:hover': {
              background: 'rgba(79, 209, 199, 0.1)',
              '& td': {
                color: '#4fd1c7',
                transform: 'translateX(5px)',
              },
            },
          },
          '& td': {
            color: '#ffffff',
            fontWeight: 500,
          },
        }}
      >
        <thead>
          <tr>
            <th>Asset</th>
            <th>Protocol</th>
            <th>Value</th>
            <th>APY</th>
            <th>24h Change</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position, index) => (
            <tr key={`${position.asset}-${position.protocol}-${index}`}>
              <td>
                <Typography sx={{ fontWeight: 600, color: '#ffffff' }}>{position.asset}</Typography>
              </td>
              <td>
                <Typography sx={{ color: '#9ca3af' }}>{position.protocol}</Typography>
              </td>
              <td>
                <Typography sx={{ fontWeight: 700, color: '#ffffff' }}>
                  ${position.value.toLocaleString()}
                </Typography>
              </td>
              <td>
                <Box
                  sx={{
                    color: '#10b981',
                    fontWeight: 600,
                    padding: '0.25rem 0.5rem',
                    background: 'rgba(16, 185, 129, 0.1)',
                    borderRadius: '0.25rem',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                    display: 'inline-block',
                  }}
                >
                  {position.apy}%
                </Box>
              </td>
              <td>
                <Typography
                  sx={{
                    color: position.change && position.change > 0 ? '#10b981' : '#ef4444',
                    fontWeight: 600,
                  }}
                >
                  {position.change ? (position.change > 0 ? '+' : '') + position.change.toFixed(1) + '%' : '—'}
                </Typography>
              </td>
            </tr>
          ))}
        </tbody>
      </Box>
    </Box>
  );
};

export default PositionBreakdownTable;