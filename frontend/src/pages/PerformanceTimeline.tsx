import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useTimelineData } from '../hooks/useTimelineData';
import { TimelineChart } from '../components/Charts/TimelineChart';
import { PortfolioSnapshot } from '../types/timeline';

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

  const snapshots = (data ?? []) as PortfolioSnapshot[];

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ padding: '1rem' }}>
        <h2>Performance Timeline</h2>
        {isLoading && <p>Loading timeline...</p>}
        {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
        {!isLoading && !error && snapshots.length === 0 && <p>No timeline data available.</p>}
        {!isLoading && snapshots.length > 0 && <TimelineChart snapshots={snapshots} />}
      </div>
    </QueryClientProvider>
  );
};

export default PerformanceTimeline; 