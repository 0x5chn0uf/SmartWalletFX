import React from 'react';
import { PortfolioSnapshot } from '../../types/timeline';

export interface TimelineChartProps {
  snapshots: PortfolioSnapshot[];
}

export const TimelineChart: React.FC<TimelineChartProps> = ({ snapshots }) => {
  return (
    <div>
      <h1>Timeline Chart</h1>
      <pre>{JSON.stringify(snapshots, null, 2)}</pre>
    </div>
  );
};
