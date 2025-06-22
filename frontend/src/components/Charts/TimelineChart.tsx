import React from 'react';
import { ChartDatum } from '../../utils/timelineAdapter';

export interface TimelineChartProps {
  data: ChartDatum[];
  metric: 'collateral' | 'borrowings' | 'health_score';
}

export const TimelineChart: React.FC<TimelineChartProps> = ({ data, metric }) => {
  return (
    <div>
      <h1>Timeline Chart - {metric}</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};
