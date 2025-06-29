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
              <TableCell>TVL</TableCell>
              <TableCell>APY</TableCell>
              <TableCell>Positions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {protocols?.map(p => (
              <TableRow key={p.name}>
                <TableCell>{p.name}</TableCell>
                <TableCell>${p.tvl.toLocaleString()}</TableCell>
                <TableCell>{p.apy.toFixed(2)}%</TableCell>
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
