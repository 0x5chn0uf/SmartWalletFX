import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useTimelineData } from '../hooks/useTimelineData';
import { TimelineChart } from '../components/Charts/TimelineChart';
import { MetricSelect } from '../components/TimelineFilters/MetricSelect';
import { IntervalToggle } from '../components/TimelineFilters/IntervalToggle';
import { mapSnapshotsToChartData } from '../utils/timelineAdapter';
import { Skeleton } from '@mui/material';

const queryClient = new QueryClient();

const DEMO_ADDRESS = '0x000000000000000000000000000000000000dEaD';

// Inner content component uses the query hook inside a provider context
const PerformanceTimelineContent: React.FC = () => {
  const now = Math.floor(Date.now() / 1000);
  const from = Math.floor(dayjs().subtract(30, 'day').valueOf() / 1000);

  const { data, isLoading, error } = useTimelineData({
    address: DEMO_ADDRESS,
    from,
    to: now,
    interval: 'daily',
    raw: true,
  });

  const [metric, setMetric] = React.useState<'collateral' | 'borrowings' | 'health_score'>(
    'collateral'
  );
  const [intervalState, setIntervalState] = React.useState<'daily' | 'weekly'>('daily');

  const snapshots = Array.isArray(data) ? data : [];
  const chartData = mapSnapshotsToChartData(snapshots);

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Performance Timeline</h2>
      {isLoading && <Skeleton variant="rectangular" height={400} animation="wave" />}
      {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
      {!isLoading && !error && snapshots.length === 0 && <p>No timeline data available.</p>}
      {!isLoading && snapshots.length > 0 && (
        <>
          <div style={{ marginBottom: '1rem' }}>
            <MetricSelect value={metric} onChange={setMetric} />
            <IntervalToggle value={intervalState} onChange={setIntervalState} />
          </div>
          <TimelineChart data={chartData} metric={metric} />
        </>
      )}
    </div>
  );
};

// Outer component provides the React Query client
const PerformanceTimeline: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <PerformanceTimelineContent />
  </QueryClientProvider>
);

export default PerformanceTimeline;
