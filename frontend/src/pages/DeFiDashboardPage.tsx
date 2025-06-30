import React, { useRef } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import TableBody from '@mui/material/TableBody';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material';

const MOCK = {
  totalValue: 42500,
  totalValueChange: 2.3,
  totalValueChangeAbs: 950,
  apy: 7.25,
  apyProjected: 3800,
  apyRealized: 2400,
  netDeposits: 18000,
  netWithdrawals: 7000,
  net: 11000,
  timeline: {},
  timelineChanges: [
    { label: '24h', value: '+2.3%', color: 'var(--success)' },
    { label: '7d', value: '+5.8%', color: 'var(--accent-secondary)' },
    { label: '30d', value: '+12.1%', color: 'var(--warning)' },
  ],
  positions: [
    { asset: 'ETH', protocol: 'Aave', value: 12000, apy: 5.2 },
    { asset: 'USDC', protocol: 'Compound', value: 8500, apy: 3.8 },
    { asset: 'WBTC', protocol: 'Yearn', value: 22000, apy: 9.1 },
  ],
};

type TimelineRange = '24h' | '7d' | '30d';

interface TimelineButtonProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  buttonRef?: React.RefObject<HTMLButtonElement>;
}

const TimelineButton: React.FC<TimelineButtonProps> = ({
  active,
  onClick,
  children,
  buttonRef,
}) => (
  <button
    ref={buttonRef}
    className={active ? 'timeline-btn active' : 'timeline-btn'}
    style={{
      background: 'none',
      border: 'none',
      borderRadius: 0,
      color: active ? '#4fd1c7' : 'var(--text-secondary)',
      fontWeight: 500,
      fontSize: '15.2px',
      padding: '0 8px 2px 8px',
      gap: 8,
      cursor: 'pointer',
      borderBottom: active ? '2px solid #4fd1c7' : '2px solid transparent',
      transition: 'color 0.2s, border-bottom 0.2s',
      outline: 'none',
    }}
    onClick={onClick}
    tabIndex={0}
    type="button"
  >
    {children}
  </button>
);

const DeFiDashboardPage: React.FC = () => {
  const theme = useTheme();
  const isSmDown = useMediaQuery(theme.breakpoints.down('sm'));

  // Timeline range state and refs
  const [activeRange, setActiveRange] = React.useState<TimelineRange>('24h');
  const btnRefs = {
    '24h': useRef<HTMLButtonElement>(null),
    '7d': useRef<HTMLButtonElement>(null),
    '30d': useRef<HTMLButtonElement>(null),
  };

  const handleRangeClick = (range: TimelineRange) => {
    setActiveRange(range);
    setTimeout(() => {
      btnRefs[range].current?.focus();
    }, 0);
  };

  return (
    <Box className="dashboard-container" sx={{ maxWidth: 1200, mx: 'auto', my: 5 }}>
      {/* Portfolio Performance Card (Timeline Wallet Card) */}
      <Box
        className="timeline-wallet-card"
        sx={{
          position: 'relative',
          mb: 4,
          p: isSmDown ? 2 : 3,
          background: '#2d3548',
          borderRadius: 1.5,
          boxShadow: 4,
          minHeight: 375,
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          alignItems: { xs: 'flex-start', md: 'stretch' },
        }}
      >
        {/* Top right metric */}
        <Box
          className="timeline-metric"
          sx={{
            position: { xs: 'static', md: 'absolute' },
            top: 0,
            right: 0,
            minWidth: 180,
            zIndex: 2,
            alignItems: 'flex-end',
            display: 'flex',
            flexDirection: 'column',
            p: 3,
            m: 0,
          }}
        >
          <Typography
            className="metric-label"
            sx={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: 500, mb: 1 }}
          >
            Total Value of Wallet
          </Typography>
          <Typography
            className="metric-value"
            sx={{
              color: 'var(--color-primary)',
              fontSize: '2.2rem',
              fontWeight: 700,
              lineHeight: 1.1,
            }}
          >
            ${MOCK.totalValue.toLocaleString()}
          </Typography>
          <Box
            className="variation"
            sx={{
              color: 'var(--success)',
              fontWeight: 600,
              fontSize: '1rem',
              display: 'flex',
              gap: 0.5,
              mt: 0.75,
            }}
          >
            <span className="perf-main">
              +{MOCK.totalValueChange}%{' '}
              <span
                className="perf-value"
                style={{ fontSize: '0.8em', alignItems: 'baseline', gap: 0.5 }}
              >
                (+${MOCK.totalValueChangeAbs})
              </span>
            </span>
            <span style={{ fontSize: '1.2em' }}>&#9650;</span>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 400, fontSize: '0.95em' }}>
              (24h)
            </span>
          </Box>
        </Box>
        {/* Timeline section */}
        <Box className="timeline-section" sx={{ width: '100%' }}>
          <Box className="chart-title-row" sx={{ mb: 1 }}>
            <Typography
              className="chart-title"
              sx={{ color: 'var(--text-secondary)', fontSize: '1.2rem', mb: 0 }}
            >
              Performance Timeline
            </Typography>
            <Box className="timeline-buttons-row" sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <TimelineButton
                active={activeRange === '24h'}
                onClick={() => handleRangeClick('24h')}
                buttonRef={btnRefs['24h']}
              >
                24h
              </TimelineButton>
              <TimelineButton
                active={activeRange === '7d'}
                onClick={() => handleRangeClick('7d')}
                buttonRef={btnRefs['7d']}
              >
                7d
              </TimelineButton>
              <TimelineButton
                active={activeRange === '30d'}
                onClick={() => handleRangeClick('30d')}
                buttonRef={btnRefs['30d']}
              >
                30d
              </TimelineButton>
            </Box>
          </Box>
          {/* SVG Timeline Chart (static, as in HTML) */}
          <Box sx={{ width: '100%', height: isSmDown ? 160 : 220, my: 1 }}>
            <svg
              width="100%"
              height="100%"
              viewBox="0 0 600 220"
              style={{ background: 'transparent' }}
            >
              <defs>
                <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4fd1c7" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4fd1c7" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#4fd1c7" stopOpacity="0" />
                </linearGradient>
              </defs>
              <polygon
                points="0,180 60,160 120,120 180,100 240,80 300,90 360,70 420,100 480,60 540,40 600,60 600,220 0,220"
                fill="url(#areaGradient)"
              />
              <polyline
                fill="none"
                stroke="url(#lineGradient)"
                strokeWidth="4"
                points="0,180 60,160 120,120 180,100 240,80 300,90 360,70 420,100 480,60 540,40 600,60"
              />
              {/* Dots */}
              <circle cx="0" cy="180" r="5" fill="#4fd1c7" />
              <circle cx="60" cy="160" r="5" fill="#4fd1c7" />
              <circle cx="120" cy="120" r="5" fill="#4fd1c7" />
              <circle cx="180" cy="100" r="5" fill="#4fd1c7" />
              <circle cx="240" cy="80" r="5" fill="#4fd1c7" />
              <circle cx="300" cy="90" r="5" fill="#4fd1c7" />
              <circle cx="360" cy="70" r="5" fill="#4fd1c7" />
              <circle cx="420" cy="100" r="5" fill="#4fd1c7" />
              <circle cx="480" cy="60" r="5" fill="#4fd1c7" />
              <circle cx="540" cy="40" r="5" fill="#4fd1c7" />
              <circle cx="600" cy="60" r="5" fill="#4fd1c7" />
              {/* X axis labels */}
              <text x="0" y="200" fill="#9ca3af" fontSize="12">
                Jan
              </text>
              <text x="120" y="200" fill="#9ca3af" fontSize="12">
                Mar
              </text>
              <text x="240" y="200" fill="#9ca3af" fontSize="12">
                May
              </text>
              <text x="360" y="200" fill="#9ca3af" fontSize="12">
                Jul
              </text>
              <text x="480" y="200" fill="#9ca3af" fontSize="12">
                Sep
              </text>
              <text x="600" y="200" fill="#9ca3af" fontSize="12">
                Nov
              </text>
            </svg>
          </Box>
          {/* Timeline changes row */}
          <Box
            className="timeline-changes-row"
            sx={{
              display: 'flex',
              gap: isSmDown ? 2 : 4,
              mt: 2,
              mb: 1,
              flexWrap: 'wrap',
              justifyContent: 'center',
            }}
          >
            {MOCK.timelineChanges.map(change => (
              <Box
                key={change.label}
                className="change-metric"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  fontSize: 16,
                  color: 'var(--text-secondary)',
                  background: 'none',
                }}
              >
                <span>{change.label}</span>
                <span
                  className="change-value"
                  style={{ color: 'var(--success)', fontWeight: 600, fontSize: '1.1rem' }}
                >
                  {change.value}
                </span>
                {/* Sparkline: use a simple SVG for each */}
                <svg className="sparkline" width="48" height="20" viewBox="0 0 48 20">
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

      {/* Metrics Row: APY and Net Deposits/Withdrawals */}
      <Box
        className="metrics-row"
        sx={{ display: 'flex', gap: isSmDown ? 1.5 : 3, mb: 4, flexWrap: 'wrap' }}
      >
        {/* APY Card */}
        <Box
          className="metric-card"
          sx={{
            background: 'var(--color-surface)',
            borderRadius: 2,
            p: isSmDown ? 2 : 3,
            boxShadow: 3,
            minWidth: 220,
            flex: '1 1 320px',
            mb: 1.5,
          }}
        >
          <Typography
            className="metric-label"
            sx={{ color: 'var(--text-secondary)', fontSize: 14, mb: 1 }}
          >
            Average APY
          </Typography>
          <Box
            className="metric-value-row"
            sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5, mb: 1 }}
          >
            <Typography
              className="metric-value"
              sx={{ fontSize: 32, fontWeight: 700, color: 'var(--color-primary)' }}
            >
              {MOCK.apy}%
            </Typography>
            <span
              className="apy-projected"
              style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', fontWeight: 500 }}
            >
              (${MOCK.apyProjected.toLocaleString()} projected)
            </span>
          </Box>
          <hr
            className="metric-divider"
            style={{
              width: '100%',
              height: 1,
              background: 'rgba(255,255,255,0.08)',
              border: 'none',
              margin: '16px 0 12px 0',
            }}
          />
          <Typography
            className="yield-title"
            sx={{ color: 'var(--text-secondary)', fontSize: '1.1rem', fontWeight: 600, mb: 1 }}
          >
            Realized vs Projected Yield
          </Typography>
          <Box
            className="yield-bars"
            sx={{ display: 'flex', gap: isSmDown ? 1.5 : 3, alignItems: 'flex-end', mt: 1 }}
          >
            <Box
              className="yield-bar"
              sx={{
                width: 60,
                height: 80,
                borderRadius: '8px 8px 0 0',
                background: 'linear-gradient(135deg, #10b981 0%, #4fd1c7 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                mb: 0,
              }}
            >
              ${MOCK.apyRealized.toLocaleString()}
              <div
                className="yield-bar-label"
                style={{
                  marginTop: 8,
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 700,
                  textShadow: '0 2px 8px #1a1f2e',
                }}
              >
                Realized
              </div>
            </Box>
            <Box
              className="yield-bar projected"
              sx={{
                width: 60,
                height: 120,
                borderRadius: '8px 8px 0 0',
                background: 'linear-gradient(135deg, #6366f1 0%, #4fd1c7 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                mb: 0,
              }}
            >
              ${MOCK.apyProjected.toLocaleString()}
              <div
                className="yield-bar-label"
                style={{
                  marginTop: 8,
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 700,
                  textShadow: '0 2px 8px #1a1f2e',
                }}
              >
                Projected
              </div>
            </Box>
          </Box>
        </Box>
        {/* Net Deposits/Withdrawals */}
        <Box
          className="net-section"
          sx={{
            background: 'var(--color-surface)',
            borderRadius: 2,
            p: isSmDown ? 2 : 3,
            boxShadow: 3,
            minWidth: 220,
            flex: '1 1 320px',
            mb: 1.5,
          }}
        >
          <Typography
            className="net-title"
            sx={{ color: 'var(--text-secondary)', fontSize: '1.1rem', fontWeight: 600, mb: 1 }}
          >
            Net Deposits vs Net Withdrawals
          </Typography>
          <Typography
            className="net-value"
            sx={{
              fontSize: 20,
              fontWeight: 700,
              mb: 0.5,
              color: 'var(--success)',
            }}
          >
            Net: +${MOCK.net.toLocaleString()}
          </Typography>
          <Box
            className="net-bars"
            sx={{ display: 'flex', gap: isSmDown ? 1.5 : 3, alignItems: 'flex-end', mt: 1 }}
          >
            <Box
              className="net-bar"
              sx={{
                width: 60,
                height: 120,
                borderRadius: '8px 8px 0 0',
                background: 'linear-gradient(135deg, #4fd1c7 0%, #3b82f6 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                mb: 0,
              }}
            >
              ${MOCK.netDeposits / 1000}k
              <div
                className="net-bar-label"
                style={{
                  marginTop: 8,
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 700,
                  textShadow: '0 2px 8px #1a1f2e',
                }}
              >
                Deposits
              </div>
            </Box>
            <Box
              className="net-bar withdrawal"
              sx={{
                width: 60,
                height: 60,
                borderRadius: '8px 8px 0 0',
                background: 'linear-gradient(135deg, #ef4444 0%, #f59e0b 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: 16,
                boxShadow: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                mb: 0,
              }}
            >
              ${MOCK.netWithdrawals / 1000}k
              <div
                className="net-bar-label"
                style={{
                  marginTop: 8,
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 700,
                  textShadow: '0 2px 8px #1a1f2e',
                }}
              >
                Withdrawals
              </div>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Position Breakdown Table */}
      <Box
        className="breakdown-section"
        sx={{
          background: 'var(--color-surface)',
          borderRadius: 2,
          p: isSmDown ? 2 : 3,
          boxShadow: 3,
        }}
      >
        <Typography
          className="breakdown-title"
          sx={{ color: 'var(--text-secondary)', fontSize: '1.2rem', mb: 2 }}
        >
          Position Breakdown
        </Typography>
        <table className="position-table">
          <thead>
            <tr>
              <th>Asset</th>
              <th>Protocol</th>
              <th>Value</th>
              <th>APY</th>
            </tr>
          </thead>
          <tbody>
            {MOCK.positions.map(row => (
              <tr key={row.asset + row.protocol}>
                <td>{row.asset}</td>
                <td>{row.protocol}</td>
                <td>${row.value.toLocaleString()}</td>
                <td>{row.apy}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Box>
    </Box>
  );
};

export default DeFiDashboardPage;
