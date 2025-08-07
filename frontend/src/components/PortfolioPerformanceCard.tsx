import React, { useState, useRef } from 'react';
import { Box, Typography, Button } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

interface TimelineData {
  x: number;
  y: number;
  value: string;
  date: string;
}

interface PortfolioPerformanceCardProps {
  totalValue: number;
  totalValueChange: number;
  totalValueChangeAbs: number;
  timelineData: Record<string, TimelineData[]>;
  timelineChanges: Array<{ label: string; value: string; color: string }>;
}

const PortfolioPerformanceCard: React.FC<PortfolioPerformanceCardProps> = ({
  totalValue,
  totalValueChange,
  totalValueChangeAbs,
  timelineData,
  timelineChanges,
}) => {
  const [activeRange, setActiveRange] = useState<'24h' | '7d' | '30d' | '90d'>('24h');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipData, setTooltipData] = useState({ value: '', date: '', x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  const handleRangeChange = (range: '24h' | '7d' | '30d' | '90d') => {
    if (range !== '24h') {
      // Show locked feature notification for other ranges
      return;
    }
    setActiveRange(range);
  };

  const handleDotHover = (
    event: React.MouseEvent<SVGCircleElement>,
    data: TimelineData
  ) => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const dotRect = event.currentTarget.getBoundingClientRect();
      
      setTooltipData({
        value: data.value,
        date: data.date,
        x: dotRect.left - rect.left - 40,
        y: dotRect.top - rect.top - 60,
      });
      setTooltipVisible(true);
    }
  };

  const currentData = timelineData[activeRange] || timelineData['24h'] || [];

  return (
    <Box
      sx={{
        position: 'relative',
        mb: 3,
        p: 3,
        background: 'linear-gradient(135deg, #242937 0%, #2d3548 100%)',
        borderRadius: 2,
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
        minHeight: 400,
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s ease',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: 'linear-gradient(90deg, #4fd1c7, #6366f1, #10b981)',
        },
        '&:hover': {
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25), 0 0 30px rgba(79, 209, 199, 0.2)',
        },
      }}
    >
      {/* Top right metric */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          right: 0,
          minWidth: 200,
          zIndex: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          p: 3,
          animation: 'slideInLeft 0.6s ease-out 0.2s both',
          '@keyframes slideInLeft': {
            from: { opacity: 0, transform: 'translateX(-30px)' },
            to: { opacity: 1, transform: 'translateX(0)' },
          },
        }}
      >
        <Typography
          sx={{
            color: '#9ca3af',
            fontSize: '0.9rem',
            fontWeight: 500,
            mb: 0.5,
            transition: 'color 0.3s ease',
          }}
        >
          Total Portfolio Value
        </Typography>
        <Typography
          sx={{
            color: '#4fd1c7',
            fontSize: '2.5rem',
            fontWeight: 700,
            lineHeight: 1.1,
            animation: 'countUp 0.8s ease-out 0.4s both',
            transition: 'all 0.3s ease',
            textShadow: '0 0 30px rgba(79, 209, 199, 0.4)',
            filter: 'drop-shadow(0 0 20px rgba(79, 209, 199, 0.3))',
            '&:hover': {
              transform: 'scale(1.05)',
            },
            '@keyframes countUp': {
              from: { opacity: 0, transform: 'scale(0.8)' },
              to: { opacity: 1, transform: 'scale(1)' },
            },
          }}
        >
          ${totalValue.toLocaleString()}
        </Typography>
        <Box
          sx={{
            color: '#10b981',
            fontWeight: 600,
            fontSize: '1rem',
            display: 'flex',
            gap: 0.5,
            mt: 0.75,
            alignItems: 'center',
            transition: 'all 0.3s ease',
            background: 'rgba(16, 185, 129, 0.1)',
            padding: '0.5rem 1rem',
            borderRadius: '0.5rem',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            backdropFilter: 'blur(10px)',
            '&:hover': {
              transform: 'scale(1.1)',
            },
          }}
        >
          <span>+{totalValueChange}% (+${totalValueChangeAbs})</span>
          <TrendingUpIcon sx={{ width: 16, height: 16, animation: 'pulse 2s ease-in-out infinite' }} />
          <span style={{ color: '#6b7280', fontWeight: 400, fontSize: '0.9em' }}>(24h)</span>
        </Box>
      </Box>

      {/* Timeline section */}
      <Box sx={{ width: '100%', animation: 'fadeInUp 0.6s ease-out 0.3s both' }}>
        <Box sx={{ mb: 2 }}>
          <Typography
            sx={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'transparent',
              background: 'linear-gradient(135deg, #ffffff 0%, #9ca3af 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              position: 'relative',
              margin: 0,
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
            Portfolio Performance
          </Typography>
          <Box
            sx={{
              display: 'flex',
              gap: 0.25,
              mt: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '0.25rem',
              borderRadius: '0.75rem',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              width: 'fit-content',
            }}
          >
            {(['24h', '7d', '30d', '90d'] as const).map(range => (
              <Button
                key={range}
                onClick={() => handleRangeChange(range)}
                sx={{
                  background: 'transparent',
                  border: 'none',
                  borderRadius: '0.5rem',
                  color: activeRange === range ? '#4fd1c7' : '#9ca3af',
                  fontWeight: 500,
                  fontSize: '0.9rem',
                  padding: '0.5rem 1rem',
                  cursor: range === '24h' ? 'pointer' : 'not-allowed',
                  transition: 'all 0.3s ease',
                  position: 'relative',
                  minWidth: '60px',
                  opacity: range === '24h' ? 1 : 0.4,
                  '&:hover': range === '24h' ? {
                    color: '#ffffff',
                    background: 'rgba(255, 255, 255, 0.1)',
                    transform: 'scale(1.05)',
                  } : {},
                  ...(activeRange === range && {
                    color: '#4fd1c7',
                    background: 'rgba(79, 209, 199, 0.2)',
                    boxShadow: '0 0 15px rgba(79, 209, 199, 0.3)',
                  }),
                  ...(range !== '24h' && {
                    '&::after': {
                      content: '"🔒"',
                      marginLeft: '0.5rem',
                      fontSize: '0.8rem',
                      opacity: 0.7,
                    },
                  }),
                }}
              >
                {range}
              </Button>
            ))}
          </Box>
        </Box>

        {/* Interactive SVG Timeline Chart */}
        <Box
          ref={containerRef}
          sx={{
            width: '100%',
            height: 250,
            margin: '1.5rem 0',
            position: 'relative',
            transition: 'all 0.3s ease',
            borderRadius: '0.5rem',
            overflow: 'hidden',
            '&:hover': {
              transform: 'scale(1.02)',
            },
          }}
        >
          <svg width="100%" height="100%" viewBox="0 0 600 250" style={{ display: 'block' }}>
            <defs>
              <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4fd1c7" />
                <stop offset="100%" stopColor="#3b82f6" />
              </linearGradient>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4fd1c7" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#4fd1c7" stopOpacity="0" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            {currentData.length > 0 && (
              <>
                <polygon
                  points={`${currentData.map(d => `${d.x},${d.y}`).join(' ')} ${currentData[currentData.length - 1]?.x},250 0,250`}
                  fill="url(#areaGradient)"
                />
                <polyline
                  fill="none"
                  stroke="url(#lineGradient)"
                  strokeWidth="3"
                  filter="url(#glow)"
                  points={currentData.map(d => `${d.x},${d.y}`).join(' ')}
                />
                {currentData.map((point, index) => (
                  <circle
                    key={index}
                    cx={point.x}
                    cy={point.y}
                    r="6"
                    fill="#4fd1c7"
                    style={{
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                    }}
                    onMouseEnter={(e) => handleDotHover(e, point)}
                    onMouseLeave={() => setTooltipVisible(false)}
                  />
                ))}
              </>
            )}
          </svg>
          {tooltipVisible && (
            <Box
              sx={{
                position: 'absolute',
                left: `${tooltipData.x}px`,
                top: `${tooltipData.y}px`,
                background: 'rgba(45, 53, 72, 0.95)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.5rem',
                padding: '0.5rem 1rem',
                color: '#ffffff',
                fontSize: '0.875rem',
                pointerEvents: 'none',
                opacity: 1,
                transform: 'translateY(0)',
                transition: 'all 0.3s ease',
                backdropFilter: 'blur(10px)',
                zIndex: 10,
              }}
            >
              <strong>{tooltipData.value}</strong><br />
              <small>{tooltipData.date}</small>
            </Box>
          )}
        </Box>

        {/* Timeline changes row */}
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            mt: 1.5,
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          {timelineChanges.map((change, index) => (
            <Box
              key={change.label}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                fontSize: '1rem',
                color: '#9ca3af',
                padding: '0.5rem 1rem',
                borderRadius: '0.5rem',
                transition: 'all 0.3s ease',
                cursor: change.label === '24h' ? 'default' : 'pointer',
                filter: change.label === '24h' ? 'none' : 'blur(4px)',
                opacity: change.label === '24h' ? 1 : 0.4,
                '&:hover': change.label === '24h' ? {
                  background: 'rgba(79, 209, 199, 0.1)',
                  transform: 'translateY(-3px)',
                } : {},
              }}
            >
              <span>{change.label}</span>
              <span
                style={{
                  color: change.color,
                  fontWeight: 700,
                  fontSize: '1.1rem',
                }}
              >
                {change.value}
              </span>
              <svg width="48" height="20" viewBox="0 0 48 20">
                <polyline
                  fill="none"
                  stroke={change.color}
                  strokeWidth="2"
                  points="0,15 8,12 16,10 24,8 32,12 40,6 48,8"
                />
              </svg>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

export default PortfolioPerformanceCard;