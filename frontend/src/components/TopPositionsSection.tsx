import React from 'react';
import { Box, Typography, Button } from '@mui/material';

interface Position {
  id: string;
  icon: string;
  asset: string;
  protocol: string;
  value: number;
  apy: number;
}

interface TopPositionsSectionProps {
  positions: Position[];
  lockedPositions: Position[];
  onUnlockClick: () => void;
}

const TopPositionsSection: React.FC<TopPositionsSectionProps> = ({
  positions,
  lockedPositions,
  onUnlockClick,
}) => {
  return (
    <Box sx={{ mt: 3 }}>
      {/* Section Separator */}
      <Box
        sx={{
          width: '100%',
          margin: '2rem 0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Box
          sx={{
            width: '100%',
            height: '1px',
            background: 'linear-gradient(90deg, transparent, rgba(79, 209, 199, 0.3), transparent)',
          }}
        />
      </Box>

      {/* Top Position Section */}
      <Box sx={{ pt: 1 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
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
              '&::after': {
                content: '""',
                position: 'absolute',
                bottom: '-4px',
                left: 0,
                width: '40px',
                height: '2px',
                background: 'linear-gradient(90deg, #4fd1c7, #6366f1)',
                borderRadius: '1px',
              },
            }}
          >
            Your Top Positions
          </Typography>
          <Typography
            sx={{
              color: '#9ca3af',
              fontSize: '0.9rem',
              fontWeight: 500,
              padding: '0.25rem 0.5rem',
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '0.25rem',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            3 of {positions.length + lockedPositions.length} positions shown
          </Typography>
        </Box>

        <Box component="ul" sx={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {positions.map((position) => (
            <Box
              key={position.id}
              component="li"
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1.5rem 0',
                borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                transition: 'all 0.3s ease',
                borderRadius: '0.5rem',
                '&:hover': {
                  background: 'rgba(79, 209, 199, 0.05)',
                  transform: 'scale(1.02)',
                  paddingLeft: '1rem',
                  paddingRight: '1rem',
                },
                '&:last-child': {
                  borderBottom: 'none',
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    background: 'linear-gradient(135deg, #4fd1c7, #6366f1)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 700,
                    fontSize: '1.1rem',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                    transition: 'all 0.3s ease',
                    position: 'relative',
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      inset: '-2px',
                      background: 'linear-gradient(45deg, #4fd1c7, #6366f1)',
                      borderRadius: '50%',
                      zIndex: -1,
                      opacity: 0,
                      transition: 'all 0.3s ease',
                    },
                    '&:hover': {
                      transform: 'scale(1.1)',
                      '&::after': {
                        opacity: 1,
                      },
                    },
                  }}
                >
                  {position.icon}
                </Box>
                <Box>
                  <Typography
                    sx={{
                      margin: 0,
                      color: '#ffffff',
                      fontSize: '1.1rem',
                      fontWeight: 700,
                      mb: 0.25,
                    }}
                  >
                    {position.asset}
                  </Typography>
                  <Typography
                    sx={{
                      margin: 0,
                      color: '#9ca3af',
                      fontSize: '0.9rem',
                      fontWeight: 500,
                    }}
                  >
                    {position.protocol}
                  </Typography>
                </Box>
              </Box>
              <Box
                sx={{
                  textAlign: 'right',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 0.25,
                }}
              >
                <Typography
                  sx={{
                    fontWeight: 700,
                    color: '#ffffff',
                    fontSize: '1.2rem',
                  }}
                >
                  ${position.value.toLocaleString()}
                </Typography>
                <Box
                  sx={{
                    color: '#10b981',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    padding: '0.25rem 0.5rem',
                    background: 'rgba(16, 185, 129, 0.1)',
                    borderRadius: '0.25rem',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                  }}
                >
                  +{position.apy}% APY
                </Box>
              </Box>
            </Box>
          ))}
        </Box>

        {/* Locked Content with Blur Effect */}
        <Box
          sx={{
            position: 'relative',
            background: '#2d3548',
            borderRadius: 2,
            mt: 2,
            overflow: 'hidden',
            border: '1px solid rgba(255, 255, 255, 0.05)',
          }}
        >
          <Box
            sx={{
              filter: 'blur(4px)',
              opacity: 0.4,
              padding: '1.5rem',
              transition: 'all 0.3s ease',
            }}
          >
            <Box component="ul" sx={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {lockedPositions.slice(0, 2).map((position) => (
                <Box
                  key={position.id}
                  component="li"
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1.5rem 0',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    '&:last-child': {
                      borderBottom: 'none',
                    },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        background: 'linear-gradient(135deg, #4fd1c7, #6366f1)',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '1.1rem',
                      }}
                    >
                      {position.icon}
                    </Box>
                    <Box>
                      <Typography sx={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 700, mb: 0.25 }}>
                        {position.asset}
                      </Typography>
                      <Typography sx={{ color: '#9ca3af', fontSize: '0.9rem' }}>
                        {position.protocol}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography sx={{ fontWeight: 700, color: '#ffffff', fontSize: '1.2rem' }}>
                      ${position.value.toLocaleString()}
                    </Typography>
                    <Typography sx={{ color: '#10b981', fontSize: '0.9rem' }}>
                      +{position.apy}% APY
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(26, 31, 46, 0.2)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              backdropFilter: 'blur(12px)',
              transition: 'all 0.3s ease',
            }}
          >
            <Box
              sx={{
                textAlign: 'center',
                mb: 1.5,
                zIndex: 10,
              }}
            >
              <Typography
                sx={{
                  margin: '0 0 0.5rem 0',
                  color: '#ffffff',
                  fontSize: '1.4rem',
                  fontWeight: 700,
                }}
              >
                {lockedPositions.length} More Positions Hidden
              </Typography>
              <Typography
                sx={{
                  margin: 0,
                  color: '#9ca3af',
                  fontSize: '1rem',
                  lineHeight: 1.5,
                }}
              >
                Register to see your complete portfolio breakdown
              </Typography>
            </Box>
            <Button
              onClick={onUnlockClick}
              sx={{
                background: 'linear-gradient(135deg, #4fd1c7, #6366f1)',
                color: 'white',
                border: 'none',
                padding: '0.75rem 2rem',
                borderRadius: '0.5rem',
                fontWeight: 700,
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                position: 'relative',
                overflow: 'hidden',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
                },
              }}
            >
              Unlock All Positions
            </Button>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default TopPositionsSection;