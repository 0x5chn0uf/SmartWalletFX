import React from 'react';
import { useQuery } from 'react-query';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Table from '@mui/material/Table';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import TableBody from '@mui/material/TableBody';
import Box from '@mui/material/Box';
import TableSortLabel from '@mui/material/TableSortLabel';
import { visuallyHidden } from '@mui/utils';
import {
  getDefiKPI,
  getProtocolBreakdown,
  DefiKPI,
  ProtocolBreakdown,
  getPortfolioTimeline,
} from '../services/defi';
import { TimelineChart } from '../components/Charts/TimelineChart';
import { mapSnapshotsToChartData } from '../utils/timelineAdapter';

const DeFiDashboardPage: React.FC = () => {
  const {
    data: kpi,
    isLoading: kpiLoading,
    error: kpiError,
  } = useQuery<DefiKPI>('defiKPI', getDefiKPI);
  const {
    data: protocols,
    isLoading: protocolsLoading,
    error: protocolsError,
  } = useQuery<ProtocolBreakdown[]>('protocolBreakdown', getProtocolBreakdown);
  const {
    data: timeline,
    isLoading: timelineLoading,
    error: timelineError,
  } = useQuery('portfolioTimeline', () => getPortfolioTimeline());

  // Sorting state for protocol table
  const [orderBy, setOrderBy] = React.useState<'tvl' | 'apy' | 'positions'>('tvl');
  const [order, setOrder] = React.useState<'asc' | 'desc'>('desc');

  const handleSort = (property: 'tvl' | 'apy' | 'positions') => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedProtocols = React.useMemo(() => {
    if (!protocols) return [];
    return [...protocols].sort((a, b) => {
      const valA = a[orderBy];
      const valB = b[orderBy];
      if (valA < valB) return order === 'asc' ? -1 : 1;
      if (valA > valB) return order === 'asc' ? 1 : -1;
      return 0;
    });
  }, [order, orderBy, protocols]);

  // Colour helpers
  const tvlColor = (value: number) => {
    if (!protocols || protocols.length === 0) return undefined;
    const max = Math.max(...protocols.map(p => p.tvl));
    const intensity = value / max; // 0-1
    const green = Math.floor(80 + 100 * intensity);
    return `rgb(0, ${green}, 100)`;
  };

  const apyColor = (value: number) => {
    // low APY red -> high green up to 20%
    const capped = Math.min(value, 20);
    const percent = capped / 20; // 0-1
    const r = Math.floor(200 * (1 - percent));
    const g = Math.floor(200 * percent);
    return `rgb(${r}, ${g}, 80)`;
  };

  if (kpiLoading || protocolsLoading || timelineLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (kpiError || protocolsError || timelineError) {
    return <Alert severity="error">Failed to load DeFi data. Please try again later.</Alert>;
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        DeFi Tracker Dashboard
      </Typography>
      <Grid container spacing={3}>
        {/* KPI Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1">Total Value Locked (TVL)</Typography>
              <Typography variant="h5">${kpi?.tvl?.toLocaleString() ?? '—'}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1">Average APY</Typography>
              <Typography variant="h5">{kpi?.apy?.toFixed(2) ?? '—'}%</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1">Protocols Tracked</Typography>
              <Typography variant="h5">{kpi?.protocols?.length ?? '—'}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Timeline Chart Integration */}
      <Box mt={4}>
        <Typography variant="h6" gutterBottom>
          Performance Timeline
        </Typography>
        <Box
          height={300}
          display="flex"
          alignItems="center"
          justifyContent="center"
          bgcolor="#222"
          borderRadius={2}
          color="#fff"
        >
          {timeline && timeline.snapshots.length > 0 ? (
            <TimelineChart data={mapSnapshotsToChartData(timeline.snapshots)} metric="collateral" />
          ) : (
            'No timeline data available'
          )}
        </Box>
      </Box>

      {/* Protocol Breakdown Table */}
      <Box mt={4}>
        <Typography variant="h6" gutterBottom>
          Protocol Breakdown
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell sortDirection={orderBy === 'tvl' ? order : false}>
                <TableSortLabel
                  active={orderBy === 'tvl'}
                  direction={orderBy === 'tvl' ? order : 'asc'}
                  onClick={() => handleSort('tvl')}
                >
                  TVL
                  {orderBy === 'tvl' ? (
                    <Box component="span" sx={visuallyHidden}>
                      {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                    </Box>
                  ) : null}
                </TableSortLabel>
              </TableCell>
              <TableCell sortDirection={orderBy === 'apy' ? order : false}>
                <TableSortLabel
                  active={orderBy === 'apy'}
                  direction={orderBy === 'apy' ? order : 'asc'}
                  onClick={() => handleSort('apy')}
                >
                  APY
                </TableSortLabel>
              </TableCell>
              <TableCell sortDirection={orderBy === 'positions' ? order : false}>
                <TableSortLabel
                  active={orderBy === 'positions'}
                  direction={orderBy === 'positions' ? order : 'asc'}
                  onClick={() => handleSort('positions')}
                >
                  Positions
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedProtocols.map(p => (
              <TableRow key={p.name}>
                <TableCell>{p.name}</TableCell>
                <TableCell sx={{ color: tvlColor(p.tvl) }}>${p.tvl.toLocaleString()}</TableCell>
                <TableCell sx={{ color: apyColor(p.apy) }}>{p.apy.toFixed(2)}%</TableCell>
                <TableCell>{p.positions}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>
    </Box>
  );
};

export default DeFiDashboardPage;
