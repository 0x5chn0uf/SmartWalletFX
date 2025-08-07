import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';

interface Position {
  asset: string;
  protocol: string;
  value: number;
  apy: number;
  icon: string;
}

interface EnhancedTopPositionsProps {
  positions: Position[];
  onUnlockClick?: () => void;
}

const mockHiddenPositions: Position[] = [
  { asset: 'LINK', protocol: 'Curve', value: 5200, apy: 7.4, icon: 'L' },
  { asset: 'AAVE', protocol: 'Aave V3', value: 3800, apy: 6.2, icon: 'A' },
  { asset: 'UNI', protocol: 'Uniswap', value: 2900, apy: 4.8, icon: 'U' },
  { asset: 'COMP', protocol: 'Compound', value: 2100, apy: 5.1, icon: 'C' },
  { asset: 'CRV', protocol: 'Curve', value: 1800, apy: 8.3, icon: 'C' },
  { asset: 'MKR', protocol: 'MakerDAO', value: 1500, apy: 3.9, icon: 'M' },
  { asset: 'SUSHI', protocol: 'SushiSwap', value: 1200, apy: 6.7, icon: 'S' },
  { asset: 'BAL', protocol: 'Balancer', value: 900, apy: 7.1, icon: 'B' },
  { asset: 'YFI', protocol: 'Yearn', value: 700, apy: 9.2, icon: 'Y' },
];

const EnhancedTopPositions: React.FC<EnhancedTopPositionsProps> = ({
  positions,
  onUnlockClick,
}) => {
  return (
    <Box>
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
      <Box sx={{ pt: 1, px: 3 }}>
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
              color: 'var(--text-primary)',
              background: 'linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              position: 'relative',
              '&::after': {
                content: '""',
                position: 'absolute',
                bottom: '-4px',
                left: 0,
                width: '40px',
                height: '2px',
                background: 'linear-gradient(90deg, var(--color-primary), var(--accent-secondary))',
                borderRadius: '1px',
              },
            }}
          >
            Your Top Positions
          </Typography>
          <Typography
            sx={{
              color: 'var(--text-secondary)',
              fontSize: '0.9rem',
              fontWeight: 500,
              padding: '0.25rem 0.5rem',
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '0.25rem',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            3 of {3 + mockHiddenPositions.length} positions shown
          </Typography>
        </Box>

        {/* Visible Positions */}
        <Box component="ul" sx={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {positions.map((position, index) => (
            <Box
              key={`${position.asset}-${position.protocol}`}
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
                  px: 1,
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
                    background: 'linear-gradient(135deg, var(--color-primary), var(--accent-secondary))',
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
                      background: 'linear-gradient(45deg, var(--color-primary), var(--accent-secondary))',
                      borderRadius: '50%',
                      zIndex: -1,
                      opacity: 0,
                      transition: 'all 0.3s ease',
                    },
                  }}
                >
                  {position.asset.charAt(0)}
                </Box>
                <Box>
                  <Typography
                    component="h4"
                    sx={{
                      margin: 0,
                      color: 'var(--text-primary)',
                      fontSize: '1.1rem',
                      fontWeight: 700,
                      mb: 0.25,
                    }}
                  >
                    {position.asset}
                  </Typography>
                  <Typography
                    component="p"
                    sx={{
                      margin: 0,
                      color: 'var(--text-secondary)',
                      fontSize: '0.9rem',
                      fontWeight: 500,
                    }}
                  >
                    {position.asset === 'WBTC' ? 'Wrapped Bitcoin' : 
                     position.asset === 'ETH' ? 'Ethereum' :
                     position.asset === 'USDC' ? 'USD Coin' : position.asset} • {position.protocol}
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                <Typography
                  sx={{
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    fontSize: '1.2rem',
                  }}
                >
                  ${position.value.toLocaleString()}
                </Typography>
                <Typography
                  sx={{
                    color: 'var(--success)',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    padding: '0.25rem 0.5rem',
                    background: 'rgba(16, 185, 129, 0.1)',
                    borderRadius: '0.25rem',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                  }}
                >
                  +{position.apy}% APY
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>

        {/* Locked Content with Blur Effect */}
        <Box
          sx={{
            position: 'relative',
            background: 'var(--color-surface-elevated)',
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
              {mockHiddenPositions.slice(0, 2).map((position, index) => (
                <Box
                  key={`${position.asset}-${position.protocol}`}
                  component="li"
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1.5rem 0',
                    borderBottom: index === 0 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        background: 'linear-gradient(135deg, var(--color-primary), var(--accent-secondary))',
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
                      <Typography
                        component="h4"
                        sx={{
                          margin: 0,
                          color: 'var(--text-primary)',
                          fontSize: '1.1rem',
                          fontWeight: 700,
                          mb: 0.25,
                        }}
                      >
                        {position.asset}
                      </Typography>
                      <Typography
                        component="p"
                        sx={{
                          margin: 0,
                          color: 'var(--text-secondary)',
                          fontSize: '0.9rem',
                          fontWeight: 500,
                        }}
                      >
                        {position.asset} Token • {position.protocol}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                    <Typography
                      sx={{
                        fontWeight: 700,
                        color: 'var(--text-primary)',
                        fontSize: '1.2rem',
                      }}
                    >
                      ${position.value.toLocaleString()}
                    </Typography>
                    <Typography
                      sx={{
                        color: 'var(--success)',
                        fontSize: '0.9rem',
                        fontWeight: 600,
                        padding: '0.25rem 0.5rem',
                        background: 'rgba(16, 185, 129, 0.1)',
                        borderRadius: '0.25rem',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                      }}
                    >
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
            <Box sx={{ textAlign: 'center', mb: 2, zIndex: 10 }}>
              <Typography
                component="h3"
                sx={{
                  margin: '0 0 0.5rem 0',
                  color: 'var(--text-primary)',
                  fontSize: '1.4rem',
                  fontWeight: 700,
                }}
              >
                {mockHiddenPositions.length} More Positions Hidden
              </Typography>
              <Typography
                component="p"
                sx={{
                  margin: 0,
                  color: 'var(--text-secondary)',
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
                background: 'linear-gradient(135deg, var(--color-primary), var(--accent-secondary))',
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

export default EnhancedTopPositions;