import React, { useState, useRef, useMemo } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useTimeline } from '../hooks/useTimeline';

export type TimelineRange = '24h' | '7d' | '30d' | '90d';

interface TimelineData {
  x: number;
  y: number;
  value: string;
  date: string;
}

interface InteractiveTimelineChartProps {
  totalValue: number;
  totalValueChange: number;
  totalValueChangeAbs: number;
  onLockedFeatureClick?: () => void;
  walletAddress?: string;
  isAuthenticated?: boolean;
}

const timelineData: Record<TimelineRange, TimelineData[]> = {
  '24h': [
    { x: 50, y: 200, value: '$39,500', date: '00:00' },
    { x: 150, y: 180, value: '$40,200', date: '04:00' },
    { x: 250, y: 140, value: '$41,800', date: '08:00' },
    { x: 350, y: 120, value: '$42,100', date: '12:00' },
    { x: 450, y: 100, value: '$42,600', date: '16:00' },
    { x: 550, y: 110, value: '$42,300', date: '20:00' },
    { x: 650, y: 90, value: '$42,800', date: '24:00' },
    { x: 750, y: 120, value: '$42,100', date: '04:00' },
    { x: 850, y: 80, value: '$42,900', date: '08:00' },
    { x: 950, y: 60, value: '$43,200', date: '12:00' },
    { x: 1150, y: 80, value: '$42,500', date: 'Now' },
  ],
  '7d': [
    { x: 50, y: 180, value: '$38,500', date: 'Mon' },
    { x: 150, y: 160, value: '$39,200', date: 'Tue' },
    { x: 250, y: 120, value: '$40,800', date: 'Wed' },
    { x: 350, y: 100, value: '$41,100', date: 'Thu' },
    { x: 450, y: 80, value: '$41,600', date: 'Fri' },
    { x: 550, y: 90, value: '$41,300', date: 'Sat' },
    { x: 650, y: 70, value: '$41,800', date: 'Sun' },
    { x: 750, y: 100, value: '$41,100', date: 'Mon' },
    { x: 850, y: 60, value: '$41,900', date: 'Tue' },
    { x: 950, y: 40, value: '$42,200', date: 'Wed' },
    { x: 1150, y: 60, value: '$42,500', date: 'Now' },
  ],
  '30d': [
    { x: 50, y: 220, value: '$37,500', date: 'Week 1' },
    { x: 150, y: 200, value: '$38,200', date: 'Week 1' },
    { x: 250, y: 160, value: '$39,800', date: 'Week 2' },
    { x: 350, y: 140, value: '$40,100', date: 'Week 2' },
    { x: 450, y: 120, value: '$40,600', date: 'Week 3' },
    { x: 550, y: 130, value: '$40,300', date: 'Week 3' },
    { x: 650, y: 110, value: '$40,800', date: 'Week 4' },
    { x: 750, y: 140, value: '$40,100', date: 'Week 4' },
    { x: 850, y: 100, value: '$40,900', date: 'Week 5' },
    { x: 950, y: 80, value: '$41,200', date: 'Week 5' },
    { x: 1150, y: 100, value: '$42,500', date: 'Now' },
  ],
  '90d': [
    { x: 50, y: 240, value: '$35,500', date: 'Month 1' },
    { x: 150, y: 220, value: '$36,200', date: 'Month 1' },
    { x: 250, y: 180, value: '$37,800', date: 'Month 1' },
    { x: 350, y: 160, value: '$38,100', date: 'Month 2' },
    { x: 450, y: 140, value: '$38,600', date: 'Month 2' },
    { x: 550, y: 150, value: '$38,300', date: 'Month 2' },
    { x: 650, y: 130, value: '$38,800', date: 'Month 3' },
    { x: 750, y: 160, value: '$38,100', date: 'Month 3' },
    { x: 850, y: 120, value: '$38,900', date: 'Month 3' },
    { x: 950, y: 100, value: '$39,200', date: 'Month 3' },
    { x: 1150, y: 120, value: '$42,500', date: 'Now' },
  ],
};

const InteractiveTimelineChart: React.FC<InteractiveTimelineChartProps> = ({
  totalValue,
  totalValueChange,
  totalValueChangeAbs,
  onLockedFeatureClick,
  walletAddress,
  isAuthenticated = false,
}) => {
  const theme = useTheme();
  const isSmDown = useMediaQuery(theme.breakpoints.down('sm'));
  const [activeRange, setActiveRange] = useState<TimelineRange>('24h');
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    content: { value: string; date: string };
  }>({
    visible: false,
    x: 0,
    y: 0,
    content: { value: '', date: '' },
  });

  const chartContainerRef = useRef<HTMLDivElement>(null);

  // Convert time range to date range for API calls
  const dateRange = useMemo(() => {
    if (!walletAddress) return null;
    
    const now = new Date();
    const endDate = now.toISOString().split('T')[0]; // Today in YYYY-MM-DD format
    
    let daysBack = 1;
    switch (activeRange) {
      case '24h': daysBack = 1; break;
      case '7d': daysBack = 7; break;
      case '30d': daysBack = 30; break;
      case '90d': daysBack = 90; break;
      default: daysBack = 1;
    }
    
    const startDate = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
    return {
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate,
    };
  }, [activeRange, walletAddress]);

  // Fetch real timeline data from API
  const { data: apiTimelineData, loading: timelineLoading } = useTimeline({
    address: walletAddress || '',
    start_date: dateRange?.start_date,
    end_date: dateRange?.end_date,
    interval: 'daily',
    enabled: !!walletAddress && !!dateRange,
  });

  const handleRangeClick = (range: TimelineRange) => {
    if (range !== '24h' && !isAuthenticated) {
      onLockedFeatureClick?.();
      return;
    }
    setActiveRange(range);
  };

  const handleDotHover = (event: React.MouseEvent, data: TimelineData) => {
    if (!chartContainerRef.current) return;

    const containerRect = chartContainerRef.current.getBoundingClientRect();
    const svgRect = (event.target as Element).closest('svg')?.getBoundingClientRect();

    if (svgRect) {
      const tooltipWidth = 120; // Approximate tooltip width
      const tooltipHeight = 60; // Approximate tooltip height
      
      let x = event.clientX - containerRect.left - 40;
      let y = event.clientY - containerRect.top - 60;
      
      // Prevent tooltip from going off the right edge
      if (x + tooltipWidth > containerRect.width) {
        x = containerRect.width - tooltipWidth - 10;
      }
      
      // Prevent tooltip from going off the left edge
      if (x < 10) {
        x = 10;
      }
      
      // Prevent tooltip from going off the top
      if (y < 10) {
        y = 10;
      }
      
      setTooltip({
        visible: true,
        x,
        y,
        content: { value: data.value, date: data.date },
      });
    }
  };

  const handleDotLeave = () => {
    setTooltip(prev => ({ ...prev, visible: false }));
  };

  // Transform API data to chart format or use mock data
  const currentData = useMemo(() => {
    if (apiTimelineData && apiTimelineData.length > 0) {
      // Transform API data to chart format
      const maxValue = Math.max(...apiTimelineData.map(item => item.total_collateral_usd || 0));
      const minValue = Math.min(...apiTimelineData.map(item => item.total_collateral_usd || 0));
      const valueRange = maxValue - minValue || 1;
      
      return apiTimelineData.map((item, index) => {
        const value = item.total_collateral_usd || 0;
        // Normalize y-coordinate: higher values should have lower y (closer to top)
        const normalizedY = 240 - ((value - minValue) / valueRange) * 160; // Scale to 80-240 range
        
        return {
          x: 50 + (index * (1100 / Math.max(apiTimelineData.length - 1, 1))), // Distribute across width
          y: normalizedY,
          value: `$${value.toLocaleString()}`,
          date: new Date(item.timestamp * 1000).toLocaleDateString(),
        };
      });
    }
    
    // Fallback to mock data
    return timelineData[activeRange];
  }, [apiTimelineData, activeRange]);
  const points = currentData.map(point => `${point.x},${point.y}`).join(' ');
  const areaPoints = `${points} ${currentData[currentData.length - 1].x},250 50,250`;

  return (
    <Box
      sx={{
        position: 'relative',
        p: 3,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Top right metric */}
      <Box
        sx={{
          position: { xs: 'static', md: 'absolute' },
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
            from: {
              opacity: 0,
              transform: 'translateX(-30px)',
            },
            to: {
              opacity: 1,
              transform: 'translateX(0)',
            },
          },
        }}
      >
        <Typography
          sx={{
            color: 'var(--text-secondary)',
            fontSize: '0.9rem',
            fontWeight: 500,
            mb: 1,
          }}
        >
          Total Portfolio Value
        </Typography>
        <Typography
          sx={{
            color: 'var(--color-primary)',
            fontSize: '2.5rem',
            fontWeight: 700,
            lineHeight: 1.1,
            animation: 'countUp 0.8s ease-out 0.4s both',
            textShadow: '0 0 30px rgba(79, 209, 199, 0.4)',
            filter: 'drop-shadow(0 0 20px rgba(79, 209, 199, 0.3))',
            '@keyframes countUp': {
              from: { opacity: 0, transform: 'scale(0.8)' },
              to: { opacity: 1, transform: 'scale(1)' },
            },
            '&:hover': {
              transform: 'scale(1.05)',
            },
          }}
        >
          ${totalValue.toLocaleString()}
        </Typography>
        <Box
          sx={{
            color: 'var(--success)',
            fontWeight: 600,
            fontSize: '0.9rem',
            display: 'flex',
            gap: 0.4,
            mt: 1,
            alignItems: 'center',
            background: 'rgba(16, 185, 129, 0.1)',
            padding: '0.4rem 0.8rem',
            borderRadius: '0.4rem',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            backdropFilter: 'blur(10px)',
            transition: 'transform 0.2s ease-in-out',
            '&:hover': {
              transform: 'scale(1.15)',
            },
          }}
        >
          <span>
            +{totalValueChange}% <span style={{ fontSize: '0.85em' }}>(+${totalValueChangeAbs})</span>
          </span>
          <span style={{ fontSize: '1.2em', animation: 'pulse 2s ease-in-out infinite' }}>▲</span>
          <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.9em' }}>
            (24h)
          </span>
        </Box>
      </Box>

      {/* Timeline section */}
      <Box sx={{ width: '100%', animation: 'fadeInUp 0.6s ease-out 0.3s both' }}>
        <Box sx={{ mb: 2 }}>
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
              margin: 0,
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
            {(['24h', '7d', '30d', '90d'] as const).map(range => {
              const isActive = activeRange === range;
              const isLocked = range !== '24h' && !isAuthenticated;

              return (
                <Button
                  key={range}
                  onClick={() => handleRangeClick(range)}
                  sx={{
                    background: 'transparent',
                    border: 'none',
                    borderRadius: '0.5rem',
                    color: isActive ? 'var(--color-primary)' : 'var(--text-secondary)',
                    fontWeight: 500,
                    fontSize: '0.9rem',
                    padding: '0.5rem 1rem',
                    cursor: isLocked ? 'not-allowed' : 'pointer',
                    transition: 'all 0.3s ease',
                    minWidth: '60px',
                    opacity: isLocked ? 0.4 : 1,
                    '&:hover': {
                      color: isLocked ? 'var(--text-secondary)' : 'var(--text-primary)',
                      background: isLocked ? 'transparent' : 'rgba(255, 255, 255, 0.1)',
                      transform: isLocked ? 'none' : 'scale(1.05)',
                    },
                    ...(isActive && {
                      color: 'var(--color-primary)',
                      background: 'rgba(79, 209, 199, 0.2)',
                      boxShadow: '0 0 15px rgba(79, 209, 199, 0.3)',
                    }),
                    ...(isLocked && {
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
              );
            })}
          </Box>
        </Box>

        {/* Interactive Chart */}
        <Box
          ref={chartContainerRef}
          sx={{
            width: '100%',
            height: isSmDown ? 180 : 250,
            my: 2,
            position: 'relative',
            transition: 'all 0.3s ease',
            borderRadius: '0.5rem',
            overflow: 'hidden',
            '&:hover': {
              transform: 'scale(1.02)',
            },
          }}
        >
          <svg width="100%" height="100%" viewBox="0 0 1200 250">
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
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <polygon fill="url(#areaGradient)" points={areaPoints} />
            <polyline
              fill="none"
              stroke="url(#lineGradient)"
              strokeWidth="3"
              filter="url(#glow)"
              points={points}
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
                onMouseLeave={handleDotLeave}
              />
            ))}
          </svg>

          {/* Tooltip */}
          {tooltip.visible && (
            <Box
              sx={{
                position: 'absolute',
                left: `${tooltip.x}px`,
                top: `${tooltip.y}px`,
                background: 'rgba(45, 53, 72, 0.95)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.5rem',
                padding: '0.5rem 1rem',
                color: 'var(--text-primary)',
                fontSize: '0.875rem',
                pointerEvents: 'none',
                backdropFilter: 'blur(10px)',
                zIndex: 1000,
              }}
            >
              <Typography component="strong">{tooltip.content.value}</Typography>
              <br />
              <Typography component="small">{tooltip.content.date}</Typography>
            </Box>
          )}
        </Box>

        {/* Timeline changes row */}
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            mt: 2,
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          {[
            { label: '24h', value: '+2.3%', color: 'var(--success)', locked: false },
            { label: '7d', value: '+5.8%', color: 'var(--accent-secondary)', locked: true },
            { label: '30d', value: '+12.1%', color: 'var(--warning)', locked: true },
            { label: '90d', value: '+18.7%', color: 'var(--color-primary)', locked: true },
          ].map(change => (
            <Box
              key={change.label}
              onClick={change.locked ? onLockedFeatureClick : undefined}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                fontSize: '1rem',
                color: 'var(--text-secondary)',
                padding: '0.5rem 1rem',
                borderRadius: '0.5rem',
                transition: 'all 0.3s ease',
                cursor: change.locked ? 'pointer' : 'default',
                ...(change.locked && {
                  opacity: 0.4,
                }),
                '&:hover': {
                  background: change.locked ? 'rgba(79, 209, 199, 0.05)' : 'rgba(79, 209, 199, 0.1)',
                  transform: 'translateY(-3px)',
                },
              }}
            >
              <span>{change.label}</span>
              <Typography
                component="span"
                sx={{
                  color: 'var(--success)',
                  fontWeight: 700,
                  fontSize: '1.1rem',
                  filter: change.locked ? 'blur(4px)' : 'none',
                }}
              >
                {change.value}
              </Typography>
              <svg 
                width="48" 
                height="20" 
                viewBox="0 0 48 20"
                style={{
                  filter: change.locked ? 'blur(4px)' : 'none',
                }}
              >
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

export default InteractiveTimelineChart;