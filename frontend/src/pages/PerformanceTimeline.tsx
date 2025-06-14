import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useTimelineData } from '../hooks/useTimelineData';
import { TimelineChart } from '../components/Charts/TimelineChart';
import { MetricSelect } from '../components/TimelineFilters/MetricSelect';
import { IntervalToggle } from '../components/TimelineFilters/IntervalToggle';
import { RangePicker } from '../components/TimelineFilters/RangePicker';
import { mapSnapshotsToChartData } from '../utils/timelineAdapter';

const queryClient = new QueryClient();

const DEMO_ADDRESS = '0x000000000000000000000000000000000000dEaD';

const PerformanceTimeline: React.FC = () => {
  const now = Math.floor(Date.now() / 1000);
  const from = Math.floor(dayjs().subtract(30, 'day').valueOf() / 1000);

  const { data, isLoading, error } = useTimelineData({
    address: DEMO_ADDRESS,
    from,
    to: now,
    interval: 'daily',
    raw: true,
  });

  const [metric, setMetric] = React.useState<'collateral' | 'borrowings' | 'health_score'>('collateral');
  const [intervalState, setIntervalState] = React.useState<'daily' | 'weekly'>('daily');

  const snapshots = Array.isArray(data) ? data : [];
  const chartData = mapSnapshotsToChartData(snapshots);

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ padding: '1rem' }}>
        <h2>Performance Timeline</h2>
        {isLoading && <p>Loading timeline...</p>}
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
    </QueryClientProvider>
  );
};

export default PerformanceTimeline; 