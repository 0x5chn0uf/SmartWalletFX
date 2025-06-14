import React from 'react';
import { useTimelineData } from '../hooks/useTimelineData';
import { TimelineChart } from '../components/Charts/TimelineChart';

/**
 * Temporary page to visualise performance timeline.
 * Displays loading/error/empty states and the TimelineChart component with mocked data.
 */
const PerformanceTimeline = () => {
  const { data, loading, error } = useTimelineData();

  if (loading) {
    return <p>Loading timeline...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  if (!data || data.length === 0) {
    return <p>No timeline data available.</p>;
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Performance Timeline</h2>
      <TimelineChart snapshots={data} />
    </div>
  );
};

export default PerformanceTimeline; 